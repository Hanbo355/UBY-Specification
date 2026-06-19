"""
UBY时间标注规范 - ORM扩展测试
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import warnings
from datetime import datetime

# 导入被测试模块
from uby_time.orm_ext import (
    UBYTimeQueryBuilder, UBYTimeAggregator,
    create_uby_migration_sql, check_orm_dependencies,
    get_supported_orm_frameworks, create_uby_query_builder,
    create_uby_aggregator
)
from uby_time.models import UBYTime


class TestORMDependencies(unittest.TestCase):
    """测试ORM依赖检查"""
    
    def test_check_orm_dependencies(self):
        """测试依赖检查函数"""
        deps = check_orm_dependencies()
        
        self.assertIsInstance(deps, dict)
        self.assertIn("sqlalchemy", deps)
        self.assertIn("django", deps)
        self.assertIn("peewee", deps)
        self.assertIn("sqlmodel", deps)
        
        for dep, available in deps.items():
            self.assertIsInstance(available, bool)
    
    def test_get_supported_orm_frameworks(self):
        """测试支持框架列表"""
        frameworks = get_supported_orm_frameworks()
        
        self.assertIsInstance(frameworks, list)
        # 至少应该有基础支持


class TestSQLAlchemyTypes(unittest.TestCase):
    """测试SQLAlchemy类型"""
    
    @patch('uby_time.orm_ext.HAS_SQLALCHEMY', True)
    def test_uby_time_type_import(self):
        """测试UBYTimeType导入"""
        try:
            from uby_time.orm_ext import UBYTimeType
            self.assertTrue(True)  # 导入成功
        except ImportError:
            # 如果没有SQLAlchemy，跳过测试
            self.skipTest("SQLAlchemy not available")
    
    @patch('uby_time.orm_ext.HAS_SQLALCHEMY', True)
    @patch('uby_time.orm_ext.String')
    def test_uby_time_type_process_bind_param(self, mock_string):
        """测试UBYTimeType的bind参数处理"""
        try:
            from uby_time.orm_ext import UBYTimeType
            
            uby_type = UBYTimeType()
            
            # 测试UBYTime对象
            uby_time = UBYTime.from_uby_string("13.8G")
            result = uby_type.process_bind_param(uby_time, None)
            self.assertEqual(result, "13.8G")
            
            # 测试字符串
            result = uby_type.process_bind_param("4.5G", None)
            self.assertEqual(result, "4.5G")
            
            # 测试None
            result = uby_type.process_bind_param(None, None)
            self.assertIsNone(result)
            
            # 测试无效类型
            with self.assertRaises(TypeError):
                uby_type.process_bind_param(123, None)
                
        except ImportError:
            self.skipTest("SQLAlchemy not available")
    
    @patch('uby_time.orm_ext.HAS_SQLALCHEMY', True)
    def test_uby_time_type_process_result_value(self):
        """测试UBYTimeType的result值处理"""
        try:
            from uby_time.orm_ext import UBYTimeType
            
            uby_type = UBYTimeType()
            
            # 测试有效UBY字符串
            result = uby_type.process_result_value("13.8G", None)
            self.assertIsInstance(result, UBYTime)
            self.assertEqual(result.to_uby_string(), "13.8G")
            
            # 测试None
            result = uby_type.process_result_value(None, None)
            self.assertIsNone(result)
            
            # 测试无效字符串（应该发出警告并返回None）
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = uby_type.process_result_value("invalid", None)
                self.assertIsNone(result)
                self.assertTrue(len(w) > 0)
                
        except ImportError:
            self.skipTest("SQLAlchemy not available")


class TestDjangoFields(unittest.TestCase):
    """测试Django字段"""
    
    @patch('uby_time.orm_ext.HAS_DJANGO', True)
    def test_django_field_import(self):
        """测试Django字段导入"""
        try:
            from uby_time.orm_ext import UBYTimeField
            self.assertTrue(True)  # 导入成功
        except ImportError:
            self.skipTest("Django not available")
    
    @patch('uby_time.orm_ext.HAS_DJANGO', True)
    @patch('uby_time.orm_ext.models')
    def test_uby_time_field_to_python(self, mock_models):
        """测试Django UBYTimeField的to_python方法"""
        try:
            from uby_time.orm_ext import UBYTimeField
            
            field = UBYTimeField()
            
            # 测试UBYTime对象
            uby_time = UBYTime.from_uby_string("13.8G")
            result = field.to_python(uby_time)
            self.assertEqual(result, uby_time)
            
            # 测试字符串
            result = field.to_python("4.5G")
            self.assertIsInstance(result, UBYTime)
            
            # 测试None
            result = field.to_python(None)
            self.assertIsNone(result)
            
        except ImportError:
            self.skipTest("Django not available")


class TestPeeweeFields(unittest.TestCase):
    """测试Peewee字段"""
    
    @patch('uby_time.orm_ext.HAS_PEEWEE', True)
    def test_peewee_field_import(self):
        """测试Peewee字段导入"""
        try:
            from uby_time.orm_ext import UBYTimeField
            # 注意：这里会有命名冲突，实际使用时需要别名
            self.assertTrue(True)
        except ImportError:
            self.skipTest("Peewee not available")


class TestUBYTimeQueryBuilder(unittest.TestCase):
    """测试UBY时间查询构建器"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_model = Mock()
        self.mock_model.__name__ = "TestModel"
    
    def test_query_builder_init(self):
        """测试查询构建器初始化"""
        builder = UBYTimeQueryBuilder("sqlalchemy", self.mock_model, "created_time")
        
        self.assertEqual(builder.orm_type, "sqlalchemy")
        self.assertEqual(builder.model_class, self.mock_model)
        self.assertEqual(builder.field_name, "created_time")
    
    def test_filter_by_uby_range_sqlalchemy(self):
        """测试SQLAlchemy范围过滤"""
        builder = UBYTimeQueryBuilder("sqlalchemy", self.mock_model, "created_time")
        
        # Mock session和field。不要 patch builtins.getattr，否则会破坏
        # unittest.mock 自身内部属性访问并在 Python 3.13 下触发递归。
        mock_session = Mock()
        mock_field = MagicMock()
        mock_field.__ge__.return_value = "ge_condition"
        mock_field.__le__.return_value = "le_condition"
        self.mock_model.created_time = mock_field
        
        with patch.object(mock_session, 'query') as mock_query:
            mock_query_obj = Mock()
            mock_query.return_value = mock_query_obj
            
            result = builder.filter_by_uby_range("1G", "10G", mock_session)
            
            mock_query.assert_called_once_with(self.mock_model)
            mock_query_obj.filter.assert_called_once()
    
    def test_filter_by_uby_range_django(self):
        """测试Django范围过滤"""
        builder = UBYTimeQueryBuilder("django", self.mock_model, "created_time")
        
        # Mock objects manager
        mock_objects = Mock()
        self.mock_model.objects = mock_objects
        
        result = builder.filter_by_uby_range("1G", "10G")
        
        mock_objects.filter.assert_called_once()
        # 验证调用参数包含正确的字段名
        call_args = mock_objects.filter.call_args[1]
        self.assertIn("created_time__gte", call_args)
        self.assertIn("created_time__lte", call_args)
    
    def test_filter_by_uby_range_peewee(self):
        """测试Peewee范围过滤"""
        builder = UBYTimeQueryBuilder("peewee", self.mock_model, "created_time")
        
        # Mock field和select。不要 patch builtins.getattr，否则会破坏
        # unittest.mock 自身内部属性访问并在 Python 3.13 下触发递归。
        mock_field = MagicMock()
        mock_field.__ge__.return_value = True
        mock_field.__le__.return_value = True
        mock_select_obj = Mock()
        self.mock_model.created_time = mock_field
        self.mock_model.select.return_value = mock_select_obj
        
        result = builder.filter_by_uby_range("1G", "10G")
        
        self.mock_model.select.assert_called_once()
        mock_select_obj.where.assert_called_once()
    
    def test_filter_by_uby_scale(self):
        """测试按尺度过滤"""
        builder = UBYTimeQueryBuilder("django", self.mock_model, "created_time")
        
        # Mock objects manager
        mock_objects = Mock()
        self.mock_model.objects = mock_objects
        
        # 测试G尺度
        result = builder.filter_by_uby_scale("G")
        mock_objects.filter.assert_called()
        
        # 测试无效尺度
        with self.assertRaises(ValueError):
            builder.filter_by_uby_scale("invalid")
    
    def test_order_by_uby_time_django(self):
        """测试Django排序"""
        builder = UBYTimeQueryBuilder("django", self.mock_model, "created_time")
        
        mock_objects = Mock()
        self.mock_model.objects = mock_objects
        
        # 测试升序
        result = builder.order_by_uby_time(ascending=True)
        mock_objects.order_by.assert_called_with("created_time")
        
        # 测试降序
        result = builder.order_by_uby_time(ascending=False)
        mock_objects.order_by.assert_called_with("-created_time")
    
    def test_unsupported_orm_type(self):
        """测试不支持的ORM类型"""
        builder = UBYTimeQueryBuilder("unsupported", self.mock_model, "created_time")
        
        with self.assertRaises(ValueError):
            builder.filter_by_uby_range("1G", "10G")


class TestUBYTimeAggregator(unittest.TestCase):
    """测试UBY时间聚合器"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_model = Mock()
        self.mock_model.__name__ = "TestModel"
    
    def test_aggregator_init(self):
        """测试聚合器初始化"""
        aggregator = UBYTimeAggregator("django", self.mock_model, "created_time")
        
        self.assertEqual(aggregator.orm_type, "django")
        self.assertEqual(aggregator.model_class, self.mock_model)
        self.assertEqual(aggregator.field_name, "created_time")
    
    def test_get_temporal_extent_django(self):
        """测试Django时间范围获取"""
        aggregator = UBYTimeAggregator("django", self.mock_model, "created_time")
        
        # Mock aggregate结果
        mock_objects = Mock()
        mock_min_time = UBYTime.from_uby_string("1G")
        mock_max_time = UBYTime.from_uby_string("10G")
        
        mock_objects.aggregate.return_value = {
            'min_time': mock_min_time,
            'max_time': mock_max_time
        }
        self.mock_model.objects = mock_objects
        
        with patch('uby_time.orm_ext.models') as mock_models:
            # Mock Min和Max
            mock_models.Min = Mock()
            mock_models.Max = Mock()
            
            result = aggregator.get_temporal_extent()
            
            self.assertEqual(result['earliest'], "1G")
            self.assertEqual(result['latest'], "10G")
            mock_objects.aggregate.assert_called_once()
    
    def test_count_by_scale_django(self):
        """测试Django按尺度计数"""
        aggregator = UBYTimeAggregator("django", self.mock_model, "created_time")
        
        # Mock记录
        mock_record1 = Mock()
        mock_record1.created_time = UBYTime.from_uby_string("13.8G")
        
        mock_record2 = Mock()
        mock_record2.created_time = UBYTime.from_uby_string("4.5M")
        
        mock_objects = Mock()
        mock_objects.all.return_value = [mock_record1, mock_record2]
        self.mock_model.objects = mock_objects
        
        result = aggregator.count_by_scale()
        
        self.assertEqual(result['G'], 1)
        self.assertEqual(result['M'], 1)
        self.assertEqual(result['K'], 0)
        self.assertEqual(result['year'], 0)
    
    def test_get_temporal_extent_sqlalchemy_no_session(self):
        """测试SQLAlchemy没有session时的错误"""
        aggregator = UBYTimeAggregator("sqlalchemy", self.mock_model, "created_time")
        
        with self.assertRaises(ValueError):
            aggregator.get_temporal_extent()


class TestMigrationSQL(unittest.TestCase):
    """测试迁移SQL生成"""
    
    def test_create_uby_migration_sql_string_postgresql(self):
        """测试PostgreSQL字符串类型迁移SQL"""
        sql = create_uby_migration_sql(
            "events", "created_time", "string", "postgresql"
        )
        
        expected = "ALTER TABLE events ADD COLUMN created_time VARCHAR(50);"
        self.assertEqual(sql, expected)
    
    def test_create_uby_migration_sql_julian_day_mysql(self):
        """测试MySQL儒略日类型迁移SQL"""
        sql = create_uby_migration_sql(
            "events", "created_time", "julian_day", "mysql"
        )
        
        expected = "ALTER TABLE events ADD COLUMN created_time DOUBLE;"
        self.assertEqual(sql, expected)
    
    def test_create_uby_migration_sql_sqlite(self):
        """测试SQLite迁移SQL"""
        sql = create_uby_migration_sql(
            "events", "created_time", "string", "sqlite"
        )
        
        expected = "ALTER TABLE events ADD COLUMN created_time TEXT;"
        self.assertEqual(sql, expected)
    
    def test_create_uby_migration_sql_invalid_storage_type(self):
        """测试无效存储类型"""
        with self.assertRaises(ValueError):
            create_uby_migration_sql(
                "events", "created_time", "invalid", "postgresql"
            )


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""
    
    def test_create_uby_query_builder(self):
        """测试创建查询构建器"""
        mock_model = Mock()
        builder = create_uby_query_builder("django", mock_model, "created_time")
        
        self.assertIsInstance(builder, UBYTimeQueryBuilder)
        self.assertEqual(builder.orm_type, "django")
        self.assertEqual(builder.model_class, mock_model)
        self.assertEqual(builder.field_name, "created_time")
    
    def test_create_uby_aggregator(self):
        """测试创建聚合器"""
        mock_model = Mock()
        aggregator = create_uby_aggregator("peewee", mock_model, "created_time")
        
        self.assertIsInstance(aggregator, UBYTimeAggregator)
        self.assertEqual(aggregator.orm_type, "peewee")
        self.assertEqual(aggregator.model_class, mock_model)
        self.assertEqual(aggregator.field_name, "created_time")


class TestIntegrationScenarios(unittest.TestCase):
    """测试集成场景"""
    
    def test_query_builder_workflow(self):
        """测试查询构建器工作流程"""
        mock_model = Mock()
        mock_objects = Mock()
        mock_model.objects = mock_objects
        
        # 创建查询构建器
        builder = UBYTimeQueryBuilder("django", mock_model, "event_time")
        
        # 模拟范围查询
        builder.filter_by_uby_range("1G", "10G")
        mock_objects.filter.assert_called()
        
        # 模拟排序
        builder.order_by_uby_time()
        mock_objects.order_by.assert_called()
    
    def test_aggregator_workflow(self):
        """测试聚合器工作流程"""
        mock_model = Mock()
        
        # 创建聚合器
        aggregator = UBYTimeAggregator("django", mock_model, "event_time")
        
        # Mock数据
        mock_record = Mock()
        mock_record.event_time = UBYTime.from_uby_string("13.8G")
        
        mock_objects = Mock()
        mock_objects.all.return_value = [mock_record]
        mock_model.objects = mock_objects
        
        # 测试按尺度计数
        result = aggregator.count_by_scale()
        self.assertIsInstance(result, dict)
        self.assertIn('G', result)
    
    def test_error_handling(self):
        """测试错误处理"""
        mock_model = Mock()
        
        # 测试无效ORM类型
        with self.assertRaises(ValueError):
            builder = UBYTimeQueryBuilder("invalid_orm", mock_model, "time_field")
            builder.filter_by_uby_range("1G", "10G")
        
        # 测试无效时间格式
        builder = UBYTimeQueryBuilder("django", mock_model, "time_field")
        with self.assertRaises(Exception):
            builder.filter_by_uby_range("invalid_time", "10G")


class TestSQLModelSupport(unittest.TestCase):
    """测试SQLModel支持"""
    
    @patch('uby_time.orm_ext.HAS_SQLMODEL', True)
    def test_sqlmodel_column_functions(self):
        """测试SQLModel列函数"""
        try:
            from uby_time.orm_ext import UBYTimeColumn, UBYJulianDayColumn
            
            # 测试函数存在
            self.assertTrue(callable(UBYTimeColumn))
            self.assertTrue(callable(UBYJulianDayColumn))
            
        except ImportError:
            self.skipTest("SQLModel not available")


if __name__ == '__main__':
    unittest.main()
