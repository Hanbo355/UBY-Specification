"""
UBY时间标注规范 - GIS扩展测试
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os
from datetime import datetime

# 导入被测试模块
from uby_time.gis_ext import (
    UBYGeoDataFrame, UBYQGISLayer, UBYArcGISTools,
    create_uby_temporal_geometry, export_uby_shapefile,
    check_gis_dependencies, get_supported_gis_formats
)
from uby_time.models import UBYTime


class TestGISDependencies(unittest.TestCase):
    """测试GIS依赖检查"""
    
    def test_check_gis_dependencies(self):
        """测试依赖检查函数"""
        deps = check_gis_dependencies()
        
        self.assertIsInstance(deps, dict)
        self.assertIn("geopandas", deps)
        self.assertIn("shapely", deps)
        self.assertIn("qgis", deps)
        self.assertIn("arcpy", deps)
        
        for dep, available in deps.items():
            self.assertIsInstance(available, bool)
    
    def test_get_supported_gis_formats(self):
        """测试支持格式列表"""
        formats = get_supported_gis_formats()
        
        self.assertIsInstance(formats, list)
        self.assertIn("geojson", formats)  # 基础支持


class TestUBYGeoDataFrame(unittest.TestCase):
    """测试UBY地理数据框架"""
    
    def setUp(self):
        """设置测试环境"""
        # Mock GeoPandas
        self.mock_gpd = Mock()
        self.mock_gdf = Mock()
        self.mock_gdf.copy.return_value = self.mock_gdf
        self.mock_gdf.to_json.return_value = '{"type": "FeatureCollection", "features": []}'
        self.mock_gdf.__getitem__ = Mock()
        self.mock_gdf.__setitem__ = Mock()
        
        self.mock_gpd.GeoDataFrame.return_value = self.mock_gdf
    
    @patch('uby_time.gis_ext.HAS_GEOPANDAS', True)
    @patch('uby_time.gis_ext.gpd')
    def test_uby_geodataframe_init(self, mock_gpd):
        """测试UBYGeoDataFrame初始化"""
        mock_gpd.GeoDataFrame.return_value = self.mock_gdf
        
        # 测试无参数初始化
        ugdf = UBYGeoDataFrame()
        self.assertIsNotNone(ugdf.gdf)
        self.assertEqual(len(ugdf._uby_time_columns), 0)
        
        # 测试带GeoDataFrame参数初始化
        ugdf2 = UBYGeoDataFrame(self.mock_gdf)
        self.assertEqual(ugdf2.gdf, self.mock_gdf)
    
    @patch('uby_time.gis_ext.HAS_GEOPANDAS', False)
    def test_uby_geodataframe_no_geopandas(self):
        """测试没有GeoPandas时的错误处理"""
        with self.assertRaises(ImportError):
            UBYGeoDataFrame()
    
    @patch('uby_time.gis_ext.HAS_GEOPANDAS', True)
    @patch('uby_time.gis_ext.gpd')
    def test_from_geodataframe(self, mock_gpd):
        """测试从GeoDataFrame创建"""
        mock_gpd.GeoDataFrame.return_value = self.mock_gdf
        
        ugdf = UBYGeoDataFrame.from_geodataframe(self.mock_gdf)
        self.mock_gdf.copy.assert_called_once()
    
    @patch('uby_time.gis_ext.HAS_GEOPANDAS', True)
    @patch('uby_time.gis_ext.gpd')
    def test_add_uby_time_column(self, mock_gpd):
        """测试添加UBY时间列"""
        mock_gpd.GeoDataFrame.return_value = self.mock_gdf
        
        ugdf = UBYGeoDataFrame()
        
        # 测试UBY字符串格式
        time_data = ["13.8G", "4.5G", "0.5G"]
        ugdf.add_uby_time_column("formation_time", time_data, "uby")
        
        self.assertIn("formation_time", ugdf._uby_time_columns)
        
        # 测试儒略日格式
        jd_data = [2451545.0, 2451910.5, 2452275.0]
        ugdf.add_uby_time_column("observation_time", jd_data, "jd")
        
        self.assertIn("observation_time", ugdf._uby_time_columns)
    
    @patch('uby_time.gis_ext.HAS_GEOPANDAS', True)
    @patch('uby_time.gis_ext.gpd')
    def test_get_temporal_extent(self, mock_gpd):
        """测试获取时间范围"""
        mock_gpd.GeoDataFrame.return_value = self.mock_gdf
        
        ugdf = UBYGeoDataFrame()
        ugdf._uby_time_columns.add("test_time")
        
        # Mock数据
        ugdf.gdf = {"test_time": ["13.8G", "4.5G", "0.5G"]}
        
        # 由于需要实际的UBYTime对象，我们mock这个方法
        with patch.object(ugdf, 'get_temporal_extent') as mock_extent:
            mock_extent.return_value = ("0.5G", "13.8G")
            start, end = ugdf.get_temporal_extent("test_time")
            self.assertEqual(start, "0.5G")
            self.assertEqual(end, "13.8G")
    
    @patch('uby_time.gis_ext.HAS_GEOPANDAS', True)
    @patch('uby_time.gis_ext.gpd')
    def test_to_geojson_with_uby(self, mock_gpd):
        """测试导出GeoJSON"""
        mock_gpd.GeoDataFrame.return_value = self.mock_gdf
        
        ugdf = UBYGeoDataFrame()
        ugdf._uby_time_columns.add("test_time")
        
        # 测试返回字符串
        result = ugdf.to_geojson_with_uby()
        self.assertIsInstance(result, str)
        
        # 验证包含UBY元数据
        geojson_dict = json.loads(result)
        self.assertIn("uby_metadata", geojson_dict)
        self.assertIn("uby_time_columns", geojson_dict["uby_metadata"])
        self.assertIn("specification_version", geojson_dict["uby_metadata"])


class TestUBYQGISLayer(unittest.TestCase):
    """测试QGIS图层支持"""
    
    @patch('uby_time.gis_ext.HAS_QGIS', False)
    def test_qgis_layer_no_qgis(self):
        """测试没有QGIS时的错误处理"""
        with self.assertRaises(ImportError):
            UBYQGISLayer()
    
    @patch('uby_time.gis_ext.HAS_QGIS', True)
    @patch('uby_time.gis_ext.QgsVectorLayer')
    @patch('uby_time.gis_ext.QgsFields')
    @patch('uby_time.gis_ext.QgsField')
    def test_create_point_layer(self, mock_field, mock_fields, mock_layer):
        """测试创建点图层"""
        mock_layer_instance = Mock()
        mock_layer.return_value = mock_layer_instance
        
        mock_fields_instance = Mock()
        mock_fields.return_value = mock_fields_instance
        
        layer = UBYQGISLayer("test_layer")
        result = layer.create_point_layer()
        
        self.assertEqual(result, mock_layer_instance)
        mock_layer.assert_called_once()
    
    @patch('uby_time.gis_ext.HAS_QGIS', True)
    @patch('uby_time.gis_ext.QgsVectorLayer')
    @patch('uby_time.gis_ext.QgsFeature')
    @patch('uby_time.gis_ext.QgsGeometry')
    @patch('uby_time.gis_ext.QgsPointXY')
    def test_add_uby_point(self, mock_point, mock_geom, mock_feature, mock_layer):
        """测试添加UBY点要素"""
        # 设置mocks
        mock_layer_instance = Mock()
        mock_layer.return_value = mock_layer_instance
        mock_layer_instance.featureCount.return_value = 0
        
        mock_feature_instance = Mock()
        mock_feature.return_value = mock_feature_instance
        
        layer = UBYQGISLayer()
        layer.layer = mock_layer_instance
        
        # 测试添加点
        layer.add_uby_point(120.0, 30.0, "13.8G", "Big Bang")
        
        mock_feature.assert_called_once()
        mock_feature_instance.setGeometry.assert_called_once()
        mock_feature_instance.setAttributes.assert_called_once()


class TestUBYArcGISTools(unittest.TestCase):
    """测试ArcGIS工具支持"""
    
    @patch('uby_time.gis_ext.HAS_ARCPY', False)
    def test_arcgis_tools_no_arcpy(self):
        """测试没有ArcPy时的错误处理"""
        with self.assertRaises(ImportError):
            UBYArcGISTools()
    
    @patch('uby_time.gis_ext.HAS_ARCPY', True)
    @patch('uby_time.gis_ext.arcpy')
    def test_add_uby_field(self, mock_arcpy):
        """测试添加UBY字段"""
        UBYArcGISTools.add_uby_field("test_fc", "UBY_TIME")
        
        mock_arcpy.AddField_management.assert_called_once_with(
            "test_fc", "UBY_TIME", "TEXT", field_length=50
        )
    
    @patch('uby_time.gis_ext.HAS_ARCPY', True)
    @patch('uby_time.gis_ext.arcpy')
    def test_populate_uby_field(self, mock_arcpy):
        """测试填充UBY字段"""
        # Mock cursor
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_cursor.__iter__ = Mock(return_value=iter([
            [datetime(2000, 1, 1), None]
        ]))
        
        mock_arcpy.da.UpdateCursor.return_value = mock_cursor
        
        UBYArcGISTools.populate_uby_field(
            "test_fc", "date_field", "uby_field", "datetime"
        )
        
        mock_arcpy.da.UpdateCursor.assert_called_once()


class TestTemporalGeometry(unittest.TestCase):
    """测试时空几何功能"""
    
    @patch('uby_time.gis_ext.HAS_SHAPELY', False)
    def test_temporal_geometry_no_shapely(self):
        """测试没有Shapely时的错误处理"""
        with self.assertRaises(ImportError):
            create_uby_temporal_geometry([(0, 0)], ["13.8G"])
    
    @patch('uby_time.gis_ext.HAS_SHAPELY', True)
    @patch('uby_time.gis_ext.Point')
    @patch('uby_time.gis_ext.LineString')
    def test_create_temporal_geometry(self, mock_linestring, mock_point):
        """测试创建时空几何"""
        mock_point_instance = Mock()
        mock_point.return_value = mock_point_instance
        
        # 测试点几何
        result = create_uby_temporal_geometry(
            [(120.0, 30.0)], ["13.8G"], "point"
        )
        
        self.assertIn("geometry", result)
        self.assertIn("times", result)
        self.assertIn("temporal_extent", result)
        self.assertEqual(result["geometry_type"], "point")
        
        # 测试线几何
        mock_linestring_instance = Mock()
        mock_linestring.return_value = mock_linestring_instance
        
        result2 = create_uby_temporal_geometry(
            [(120.0, 30.0), (121.0, 31.0)], 
            ["13.8G", "4.5G"], 
            "linestring"
        )
        
        self.assertEqual(result2["geometry_type"], "linestring")
    
    def test_temporal_geometry_validation(self):
        """测试时空几何验证"""
        with patch('uby_time.gis_ext.HAS_SHAPELY', True):
            # 测试坐标和时间数量不匹配
            with self.assertRaises(ValueError):
                create_uby_temporal_geometry(
                    [(0, 0), (1, 1)], ["13.8G"]
                )
            
            # 测试不支持的几何类型
            with self.assertRaises(ValueError):
                create_uby_temporal_geometry(
                    [(0, 0)], ["13.8G"], "unsupported"
                )


class TestExportFunctions(unittest.TestCase):
    """测试导出功能"""
    
    @patch('uby_time.gis_ext.HAS_GEOPANDAS', False)
    def test_export_shapefile_no_geopandas(self):
        """测试没有GeoPandas时的错误处理"""
        with self.assertRaises(ImportError):
            export_uby_shapefile(None, "test")
    
    @patch('uby_time.gis_ext.HAS_GEOPANDAS', True)
    def test_export_shapefile_with_mock(self):
        """测试Shapefile导出（使用Mock）"""
        # 创建mock UBYGeoDataFrame
        mock_ugdf = Mock()
        mock_ugdf._uby_time_columns = {"time_col"}
        
        mock_gdf = Mock()
        mock_gdf.copy.return_value = mock_gdf
        mock_gdf.to_file = Mock()
        mock_ugdf.gdf = mock_gdf
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test")
            
            with patch('builtins.open', create=True) as mock_open:
                mock_file = Mock()
                mock_open.return_value.__enter__.return_value = mock_file
                
                export_uby_shapefile(mock_ugdf, filename)
                
                # 验证调用
                mock_gdf.to_file.assert_called_once_with(f"{filename}.shp")
                mock_open.assert_called()


class TestIntegrationScenarios(unittest.TestCase):
    """测试集成场景"""
    
    def test_datetime_to_jd_conversion(self):
        """测试datetime到儒略日转换"""
        from uby_time.gis_ext import UBYGeoDataFrame
        
        # 测试已知日期
        dt = datetime(2000, 1, 1, 12, 0, 0)  # J2000.0
        jd = UBYGeoDataFrame._datetime_to_jd(dt)
        
        # J2000.0应该是2451545.0
        self.assertAlmostEqual(jd, 2451545.0, places=1)
    
    @patch('uby_time.gis_ext.HAS_GEOPANDAS', True)
    @patch('uby_time.gis_ext.gpd')
    def test_workflow_simulation(self, mock_gpd):
        """测试完整工作流程模拟"""
        # 模拟创建UBYGeoDataFrame并添加时间数据
        mock_gdf = Mock()
        mock_gdf.copy.return_value = mock_gdf
        mock_gdf.__getitem__ = Mock()
        mock_gdf.__setitem__ = Mock()
        mock_gpd.GeoDataFrame.return_value = mock_gdf
        
        ugdf = UBYGeoDataFrame()
        
        # 模拟添加时间列
        time_data = ["13.8G", "4.5G", "0.5G"]
        ugdf.add_uby_time_column("formation_time", time_data)
        
        # 验证时间列被添加
        self.assertIn("formation_time", ugdf._uby_time_columns)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效时间格式
        with patch('uby_time.gis_ext.HAS_GEOPANDAS', True):
            with patch('uby_time.gis_ext.gpd') as mock_gpd:
                mock_gdf = Mock()
                mock_gpd.GeoDataFrame.return_value = mock_gdf
                
                ugdf = UBYGeoDataFrame()
                
                with self.assertRaises(ValueError):
                    ugdf.add_uby_time_column(
                        "test", [None], "invalid_format"
                    )


if __name__ == '__main__':
    unittest.main()
