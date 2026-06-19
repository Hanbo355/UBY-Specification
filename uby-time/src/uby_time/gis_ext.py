"""
UBY时间标注规范 - GIS软件集成扩展

支持主流GIS软件和库：
- GeoPandas (pandas地理扩展)
- QGIS (通过PyQGIS)
- ArcGIS (通过arcpy)
- Shapely几何操作
- 时空数据的UBY标注
"""

import warnings
from typing import Optional, Union, List, Dict, Any, Tuple
from datetime import datetime
import json

from .constants import UBY_SPEC_VERSION
from .conversion import jd_to_uby, uby_to_jd
from .models import UBYTime

# 可选依赖处理
try:
    import geopandas as gpd
    import pandas as pd
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False
    gpd = None
    pd = None

try:
    from shapely.geometry import Point, LineString, Polygon
    from shapely import wkt
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False
    Point = LineString = Polygon = wkt = None

try:
    # QGIS支持
    from qgis.core import (
        QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
        QgsProject, QgsField, QgsFields
    )
    from PyQt5.QtCore import QVariant
    HAS_QGIS = True
except ImportError:
    HAS_QGIS = False
    QgsVectorLayer = QgsFeature = QgsGeometry = QgsPointXY = None
    QgsProject = QgsField = QgsFields = QVariant = None

try:
    # ArcGIS支持
    import arcpy
    HAS_ARCPY = True
except ImportError:
    HAS_ARCPY = False
    arcpy = None


class UBYGeoDataFrame:
    """
    UBY时间标注的地理数据框架
    基于GeoPandas，添加UBY时间处理功能
    """
    
    def __init__(self, gdf: Optional['gpd.GeoDataFrame'] = None):
        if not HAS_GEOPANDAS:
            raise ImportError("GeoPandas is required for UBYGeoDataFrame")
        
        self.gdf = gdf if gdf is not None else gpd.GeoDataFrame()
        self._uby_time_columns = set()
    
    @classmethod
    def from_geodataframe(cls, gdf: 'gpd.GeoDataFrame') -> 'UBYGeoDataFrame':
        """从现有GeoDataFrame创建UBYGeoDataFrame"""
        return cls(gdf.copy())
    
    def add_uby_time_column(self, 
                           column_name: str,
                           time_data: Union[List[Union[str, float, 'UBYTime']], 'pd.Series'],
                           time_format: str = 'auto') -> None:
        """
        添加UBY时间列
        
        Args:
            column_name: 列名
            time_data: 时间数据
            time_format: 时间格式 ('uby', 'jd', 'datetime', 'auto')
        """
        if not HAS_GEOPANDAS:
            raise ImportError("GeoPandas is required")
        
        uby_times = []
        for time_val in time_data:
            if isinstance(time_val, UBYTime):
                uby_times.append(time_val)
            elif time_format == 'uby' or (time_format == 'auto' and isinstance(time_val, str)):
                uby_times.append(UBYTime.from_uby_string(str(time_val)))
            elif time_format == 'jd' or (time_format == 'auto' and isinstance(time_val, (int, float))):
                uby_times.append(UBYTime.from_julian_day(float(time_val)))
            elif time_format == 'datetime':
                if isinstance(time_val, datetime):
                    jd = self._datetime_to_jd(time_val)
                    uby_times.append(UBYTime.from_julian_day(jd))
                else:
                    raise ValueError(f"Expected datetime object, got {type(time_val)}")
            else:
                raise ValueError(f"Cannot parse time value: {time_val}")
        
        self.gdf[column_name] = [t.to_uby_string() for t in uby_times]
        self._uby_time_columns.add(column_name)
    
    def get_temporal_extent(self, time_column: str) -> Tuple[str, str]:
        """获取时间范围"""
        if time_column not in self._uby_time_columns:
            raise ValueError(f"Column {time_column} is not a UBY time column")
        
        uby_times = [UBYTime.from_uby_string(uby_str) for uby_str in self.gdf[time_column]]
        jd_times = [t.to_julian_day() for t in uby_times]
        
        min_jd, max_jd = min(jd_times), max(jd_times)
        min_uby = UBYTime.from_julian_day(min_jd)
        max_uby = UBYTime.from_julian_day(max_jd)
        
        return min_uby.to_uby_string(), max_uby.to_uby_string()
    
    def filter_by_time_range(self, 
                           time_column: str,
                           start_time: Union[str, 'UBYTime'],
                           end_time: Union[str, 'UBYTime']) -> 'UBYGeoDataFrame':
        """按时间范围过滤数据"""
        if time_column not in self._uby_time_columns:
            raise ValueError(f"Column {time_column} is not a UBY time column")
        
        start_uby = start_time if isinstance(start_time, UBYTime) else UBYTime.from_uby_string(start_time)
        end_uby = end_time if isinstance(end_time, UBYTime) else UBYTime.from_uby_string(end_time)
        
        start_jd = start_uby.to_julian_day()
        end_jd = end_uby.to_julian_day()
        
        # 转换为JD进行比较
        time_jds = [UBYTime.from_uby_string(uby_str).to_julian_day() 
                   for uby_str in self.gdf[time_column]]
        
        mask = [(start_jd <= jd <= end_jd) for jd in time_jds]
        filtered_gdf = self.gdf[mask].copy()
        
        result = UBYGeoDataFrame(filtered_gdf)
        result._uby_time_columns = self._uby_time_columns.copy()
        return result
    
    def to_geojson_with_uby(self, filename: Optional[str] = None) -> Union[str, None]:
        """导出为包含UBY时间的GeoJSON"""
        geojson_dict = json.loads(self.gdf.to_json())
        
        # 添加UBY时间元数据
        geojson_dict['uby_metadata'] = {
            'uby_time_columns': list(self._uby_time_columns),
            'specification_version': UBY_SPEC_VERSION,
            'export_timestamp': datetime.now().isoformat()
        }
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(geojson_dict, f, indent=2, ensure_ascii=False)
            return None
        else:
            return json.dumps(geojson_dict, indent=2, ensure_ascii=False)
    
    @staticmethod
    def _datetime_to_jd(dt: datetime) -> float:
        """将datetime转换为儒略日"""
        # 简化的儒略日计算
        a = (14 - dt.month) // 12
        y = dt.year + 4800 - a
        m = dt.month + 12 * a - 3
        
        jd = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        
        # 添加时间部分
        time_fraction = (dt.hour - 12) / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0
        return jd + time_fraction
    
    def __getattr__(self, name):
        """代理到底层GeoDataFrame"""
        return getattr(self.gdf, name)


class UBYQGISLayer:
    """
    QGIS图层的UBY时间支持
    """
    
    def __init__(self, layer_name: str = "UBY_Layer"):
        if not HAS_QGIS:
            raise ImportError("QGIS (PyQGIS) is required for UBYQGISLayer")
        
        self.layer_name = layer_name
        self.layer = None
        self._uby_fields = {}
    
    def create_point_layer(self, crs: str = "EPSG:4326") -> 'QgsVectorLayer':
        """创建点图层"""
        self.layer = QgsVectorLayer(f"Point?crs={crs}", self.layer_name, "memory")
        
        # 添加基础字段。真实 QGIS 环境使用 QVariant 类型；测试或轻量 mock
        # 环境可能只 patch PyQGIS 类而没有 PyQt QVariant，此时传入 None
        # 以保持扩展模块的可选依赖降级能力。
        int_type = QVariant.Int if QVariant is not None else None
        string_type = QVariant.String if QVariant is not None else None

        fields = QgsFields()
        fields.append(QgsField("id", int_type))
        fields.append(QgsField("name", string_type))
        fields.append(QgsField("uby_time", string_type))
        
        self.layer.dataProvider().addAttributes(fields)
        self.layer.updateFields()
        
        return self.layer
    
    def add_uby_point(self, 
                     x: float, 
                     y: float, 
                     uby_time: Union[str, 'UBYTime'],
                     name: str = "",
                     feature_id: Optional[int] = None) -> None:
        """添加带UBY时间的点要素"""
        if not self.layer:
            raise ValueError("Layer not created. Call create_point_layer() first.")
        
        uby_str = uby_time if isinstance(uby_time, str) else uby_time.to_uby_string()
        
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
        
        attributes = []
        if feature_id is not None:
            attributes.append(feature_id)
        else:
            attributes.append(self.layer.featureCount() + 1)
        
        attributes.extend([name, uby_str])
        feature.setAttributes(attributes)
        
        self.layer.dataProvider().addFeature(feature)
        self.layer.updateExtents()
    
    def filter_by_uby_range(self, 
                           start_uby: Union[str, 'UBYTime'],
                           end_uby: Union[str, 'UBYTime']) -> List[int]:
        """按UBY时间范围过滤要素，返回要素ID列表"""
        if not self.layer:
            raise ValueError("Layer not created")
        
        start_time = start_uby if isinstance(start_uby, UBYTime) else UBYTime.from_uby_string(start_uby)
        end_time = end_uby if isinstance(end_uby, UBYTime) else UBYTime.from_uby_string(end_uby)
        
        start_jd = start_time.to_julian_day()
        end_jd = end_time.to_julian_day()
        
        filtered_ids = []
        for feature in self.layer.getFeatures():
            uby_str = feature.attribute("uby_time")
            if uby_str:
                try:
                    feature_time = UBYTime.from_uby_string(uby_str)
                    feature_jd = feature_time.to_julian_day()
                    if start_jd <= feature_jd <= end_jd:
                        filtered_ids.append(feature.id())
                except Exception:
                    continue
        
        return filtered_ids
    
    def add_to_project(self) -> None:
        """将图层添加到QGIS项目"""
        if self.layer:
            QgsProject.instance().addMapLayer(self.layer)


class UBYArcGISTools:
    """
    ArcGIS工具集的UBY时间支持
    """
    
    def __init__(self):
        if not HAS_ARCPY:
            raise ImportError("ArcPy is required for UBYArcGISTools")
    
    @staticmethod
    def add_uby_field(feature_class: str, field_name: str = "UBY_TIME") -> None:
        """为要素类添加UBY时间字段"""
        arcpy.AddField_management(feature_class, field_name, "TEXT", field_length=50)
    
    @staticmethod
    def populate_uby_field(feature_class: str, 
                          source_time_field: str,
                          uby_field: str = "UBY_TIME",
                          time_format: str = "datetime") -> None:
        """
        从现有时间字段填充UBY时间字段
        
        Args:
            feature_class: 要素类路径
            source_time_field: 源时间字段名
            uby_field: UBY时间字段名
            time_format: 源时间格式 ('datetime', 'jd', 'timestamp')
        """
        with arcpy.da.UpdateCursor(feature_class, [source_time_field, uby_field]) as cursor:
            for row in cursor:
                source_time = row[0]
                if source_time is not None:
                    try:
                        if time_format == "datetime":
                            # 假设是datetime对象
                            jd = UBYArcGISTools._datetime_to_jd(source_time)
                            uby_time = UBYTime.from_julian_day(jd)
                        elif time_format == "jd":
                            uby_time = UBYTime.from_julian_day(float(source_time))
                        elif time_format == "timestamp":
                            # Unix时间戳
                            dt = datetime.fromtimestamp(source_time)
                            jd = UBYArcGISTools._datetime_to_jd(dt)
                            uby_time = UBYTime.from_julian_day(jd)
                        else:
                            raise ValueError(f"Unsupported time format: {time_format}")
                        
                        row[1] = uby_time.to_uby_string()
                        cursor.updateRow(row)
                    except Exception as e:
                        print(f"Error processing time value {source_time}: {e}")
                        continue
    
    @staticmethod
    def select_by_uby_range(feature_class: str,
                           uby_field: str,
                           start_uby: Union[str, 'UBYTime'],
                           end_uby: Union[str, 'UBYTime'],
                           selection_type: str = "NEW_SELECTION") -> None:
        """按UBY时间范围选择要素"""
        start_time = start_uby if isinstance(start_uby, UBYTime) else UBYTime.from_uby_string(start_uby)
        end_time = end_uby if isinstance(end_uby, UBYTime) else UBYTime.from_uby_string(end_uby)
        
        start_jd = start_time.to_julian_day()
        end_jd = end_time.to_julian_day()
        
        # 构建选择表达式（需要自定义函数支持）
        where_clause = f"{uby_field} IS NOT NULL"
        
        # 由于ArcGIS SQL不直接支持UBY转换，我们需要使用游标进行选择
        selected_oids = []
        with arcpy.da.SearchCursor(feature_class, ["OID@", uby_field]) as cursor:
            for row in cursor:
                oid, uby_str = row
                if uby_str:
                    try:
                        feature_time = UBYTime.from_uby_string(uby_str)
                        feature_jd = feature_time.to_julian_day()
                        if start_jd <= feature_jd <= end_jd:
                            selected_oids.append(oid)
                    except Exception:
                        continue
        
        if selected_oids:
            oid_list = ",".join(map(str, selected_oids))
            where_clause = f"OBJECTID IN ({oid_list})"
            arcpy.SelectLayerByAttribute_management(feature_class, selection_type, where_clause)
    
    @staticmethod
    def _datetime_to_jd(dt: datetime) -> float:
        """将datetime转换为儒略日"""
        a = (14 - dt.month) // 12
        y = dt.year + 4800 - a
        m = dt.month + 12 * a - 3
        
        jd = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        time_fraction = (dt.hour - 12) / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0
        return jd + time_fraction


def create_uby_temporal_geometry(coordinates: List[Tuple[float, float]],
                                times: List[Union[str, 'UBYTime']],
                                geometry_type: str = "linestring") -> Dict[str, Any]:
    """
    创建时空几何对象
    
    Args:
        coordinates: 坐标列表 [(x1, y1), (x2, y2), ...]
        times: 对应的UBY时间列表
        geometry_type: 几何类型 ('point', 'linestring', 'polygon')
    
    Returns:
        包含几何和时间信息的字典
    """
    if not HAS_SHAPELY:
        raise ImportError("Shapely is required for temporal geometry")
    
    if len(coordinates) != len(times):
        raise ValueError("Coordinates and times must have the same length")
    
    # 转换时间为UBYTime对象
    uby_times = []
    for t in times:
        if isinstance(t, UBYTime):
            uby_times.append(t)
        else:
            uby_times.append(UBYTime.from_uby_string(str(t)))
    
    # 创建几何对象
    if geometry_type.lower() == "point":
        if len(coordinates) != 1:
            raise ValueError("Point geometry requires exactly one coordinate")
        geometry = Point(coordinates[0])
    elif geometry_type.lower() == "linestring":
        geometry = LineString(coordinates)
    elif geometry_type.lower() == "polygon":
        geometry = Polygon(coordinates)
    else:
        raise ValueError(f"Unsupported geometry type: {geometry_type}")
    
    return {
        "geometry": geometry,
        "times": [t.to_uby_string() for t in uby_times],
        "coordinates": coordinates,
        "temporal_extent": {
            "start": min(uby_times, key=lambda x: x.to_julian_day()).to_uby_string(),
            "end": max(uby_times, key=lambda x: x.to_julian_day()).to_uby_string()
        },
        "geometry_type": geometry_type
    }


def export_uby_shapefile(uby_gdf: 'UBYGeoDataFrame', 
                        filename: str,
                        time_columns: Optional[List[str]] = None) -> None:
    """
    导出UBY地理数据为Shapefile格式
    
    Args:
        uby_gdf: UBY地理数据框架
        filename: 输出文件名（不含扩展名）
        time_columns: 要导出的UBY时间列，None表示导出所有
    """
    if not HAS_GEOPANDAS:
        raise ImportError("GeoPandas is required")
    
    export_gdf = uby_gdf.gdf.copy()
    
    # 处理时间列
    if time_columns is None:
        time_columns = list(uby_gdf._uby_time_columns)
    
    # Shapefile字段名限制为10个字符
    for col in time_columns:
        if len(col) > 10:
            new_col = col[:10]
            export_gdf = export_gdf.rename(columns={col: new_col})
            warnings.warn(f"Column '{col}' renamed to '{new_col}' due to Shapefile limitations")
    
    # 导出
    export_gdf.to_file(f"{filename}.shp")
    
    # 创建UBY元数据文件
    metadata = {
        "uby_time_columns": time_columns,
        "specification_version": UBY_SPEC_VERSION,
        "export_timestamp": datetime.now().isoformat(),
        "original_column_names": {col[:10]: col for col in time_columns if len(col) > 10}
    }
    
    with open(f"{filename}_uby_metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


# 便捷函数
def check_gis_dependencies() -> Dict[str, bool]:
    """检查GIS相关依赖的可用性"""
    return {
        "geopandas": HAS_GEOPANDAS,
        "shapely": HAS_SHAPELY,
        "qgis": HAS_QGIS,
        "arcpy": HAS_ARCPY
    }


def get_supported_gis_formats() -> List[str]:
    """获取支持的GIS格式列表"""
    formats = ["geojson"]  # 基础支持
    
    if HAS_GEOPANDAS:
        formats.extend(["shapefile", "gpkg", "kml"])
    
    if HAS_QGIS:
        formats.extend(["qgis_layer"])
    
    if HAS_ARCPY:
        formats.extend(["feature_class", "geodatabase"])
    
    return formats
