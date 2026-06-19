"""
UBY时间标注规范 - 数据库ORM适配器

支持主流ORM框架：
- SQLAlchemy (Python)
- Django ORM (Python)
- Peewee (Python)
- SQLModel (Python)
- 原生SQL支持
"""

import warnings
from typing import Optional, Union, List, Dict, Any, Type, Callable
from datetime import datetime
import json
import operator

from .conversion import jd_to_uby, uby_to_jd
from .models import UBYTime

# 可选依赖处理
try:
    import sqlalchemy as sa
    from sqlalchemy import TypeDecorator, String, Float
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False
    sa = TypeDecorator = String = Float = None
    declarative_base = sessionmaker = None

try:
    from django.db import models
    from django.core.exceptions import ValidationError
    HAS_DJANGO = True
except ImportError:
    HAS_DJANGO = False
    models = ValidationError = None

try:
    import peewee as pw
    HAS_PEEWEE = True
except ImportError:
    HAS_PEEWEE = False
    pw = None

try:
    from sqlmodel import SQLModel, Field
    HAS_SQLMODEL = True
except ImportError:
    HAS_SQLMODEL = False
    SQLModel = Field = None


# SQLAlchemy支持
if HAS_SQLALCHEMY:
    class UBYTimeType(TypeDecorator):
        """
        SQLAlchemy自定义类型：UBY时间
        在数据库中存储为字符串，在Python中使用为UBYTime对象
        """
        
        impl = String(50)  # UBY字符串最大长度
        cache_ok = True
        
        def process_bind_param(self, value: Union[UBYTime, str, None], dialect) -> Optional[str]:
            """将Python值转换为数据库值"""
            if value is None:
                return None
            elif isinstance(value, UBYTime):
                # 返回简化格式，仅保留数值部分（如果原始输入是简化格式）
                return value.to_uby_string(simplified=True)
            elif isinstance(value, str):
                # 验证UBY格式
                try:
                    UBYTime.from_uby_string(value)
                    return value
                except Exception:
                    raise ValueError(f"Invalid UBY time format: {value}")
            else:
                raise TypeError(f"Expected UBYTime or str, got {type(value)}")
        
        def process_result_value(self, value: Optional[str], dialect) -> Optional[UBYTime]:
            """将数据库值转换为Python值"""
            if value is None:
                return None
            try:
                return UBYTime.from_uby_string(value)
            except Exception:
                warnings.warn(f"Invalid UBY time in database: {value}")
                return None
    
    
    class UBYJulianDayType(TypeDecorator):
        """
        SQLAlchemy自定义类型：UBY时间（存储为儒略日）
        在数据库中存储为浮点数，在Python中使用为UBYTime对象
        """
        
        impl = Float
        cache_ok = True
        
        def process_bind_param(self, value: Union[UBYTime, float, None], dialect) -> Optional[float]:
            """将Python值转换为数据库值"""
            if value is None:
                return None
            elif isinstance(value, UBYTime):
                return value.to_julian_day()
            elif isinstance(value, (int, float)):
                return float(value)
            else:
                raise TypeError(f"Expected UBYTime or number, got {type(value)}")
        
        def process_result_value(self, value: Optional[float], dialect) -> Optional[UBYTime]:
            """将数据库值转换为Python值"""
            if value is None:
                return None
            try:
                return UBYTime.from_julian_day(value)
            except Exception:
                warnings.warn(f"Invalid Julian Day in database: {value}")
                return None


# Django支持
if HAS_DJANGO:
    class UBYTimeField(models.CharField):
        """
        Django自定义字段：UBY时间
        """
        
        description = "UBY Time field"
        
        def __init__(self, *args, **kwargs):
            kwargs.setdefault('max_length', 50)
            super().__init__(*args, **kwargs)
        
        def from_db_value(self, value, expression, connection):
            """从数据库值转换为Python值"""
            if value is None:
                return value
            try:
                return UBYTime.from_uby_string(value)
            except Exception:
                warnings.warn(f"Invalid UBY time in database: {value}")
                return None
        
        def to_python(self, value):
            """转换为Python值"""
            if isinstance(value, UBYTime):
                return value
            if value is None:
                return value
            try:
                return UBYTime.from_uby_string(value)
            except Exception:
                raise ValidationError(f"Invalid UBY time format: {value}")
        
        def get_prep_value(self, value):
            """准备存储到数据库的值"""
            if value is None:
                return value
            if isinstance(value, UBYTime):
                return value.to_uby_string(simplified=True)  # 使用简化格式
            if isinstance(value, str):
                # 验证格式
                try:
                    UBYTime.from_uby_string(value)
                    return value
                except Exception:
                    raise ValidationError(f"Invalid UBY time format: {value}")
            raise ValidationError(f"Expected UBYTime or str, got {type(value)}")
    
    
    class UBYJulianDayField(models.FloatField):
        """
        Django自定义字段：UBY时间（存储为儒略日）
        """
        
        description = "UBY Time field (stored as Julian Day)"
        
        def from_db_value(self, value, expression, connection):
            """从数据库值转换为Python值"""
            if value is None:
                return value
            try:
                return UBYTime.from_julian_day(value)
            except Exception:
                warnings.warn(f"Invalid Julian Day in database: {value}")
                return None
        
        def to_python(self, value):
            """转换为Python值"""
            if isinstance(value, UBYTime):
                return value
            if value is None:
                return value
            if isinstance(value, (int, float)):
                try:
                    return UBYTime.from_julian_day(float(value))
                except Exception:
                    raise ValidationError(f"Invalid Julian Day: {value}")
            raise ValidationError(f"Expected UBYTime or number, got {type(value)}")
        
        def get_prep_value(self, value):
            """准备存储到数据库的值"""
            if value is None:
                return value
            if isinstance(value, UBYTime):
                return value.to_julian_day()
            if isinstance(value, (int, float)):
                return float(value)
            raise ValidationError(f"Expected UBYTime or number, got {type(value)}")


# Peewee支持
if HAS_PEEWEE:
    class UBYTimeField(pw.CharField):
        """
        Peewee自定义字段：UBY时间
        """
        
        def __init__(self, *args, **kwargs):
            kwargs.setdefault('max_length', 50)
            super().__init__(*args, **kwargs)
        
        def db_value(self, value):
            """转换为数据库值"""
            if value is None:
                return None
            if isinstance(value, UBYTime):
                return value.to_uby_string(simplified=True)  # 使用简化格式
            if isinstance(value, str):
                # 验证格式
                try:
                    UBYTime.from_uby_string(value)
                    return value
                except Exception:
                    raise ValueError(f"Invalid UBY time format: {value}")
            raise TypeError(f"Expected UBYTime or str, got {type(value)}")
        
        def python_value(self, value):
            """转换为Python值"""
            if value is None:
                return None
            try:
                return UBYTime.from_uby_string(value)
            except Exception:
                warnings.warn(f"Invalid UBY time in database: {value}")
                return None
    
    
    class UBYJulianDayField(pw.FloatField):
        """
        Peewee自定义字段：UBY时间（存储为儒略日）
        """
        
        def db_value(self, value):
            """转换为数据库值"""
            if value is None:
                return None
            if isinstance(value, UBYTime):
                return value.to_julian_day()
            if isinstance(value, (int, float)):
                return float(value)
            raise TypeError(f"Expected UBYTime or number, got {type(value)}")
        
        def python_value(self, value):
            """转换为Python值"""
            if value is None:
                return None
            try:
                return UBYTime.from_julian_day(value)
            except Exception:
                warnings.warn(f"Invalid Julian Day in database: {value}")
                return None


# SQLModel支持
if HAS_SQLMODEL:
    def UBYTimeColumn(default=None, **kwargs):
        """
        SQLModel UBY时间列定义
        """
        return Field(default=default, sa_column=sa.Column(UBYTimeType), **kwargs)
    
    def UBYJulianDayColumn(default=None, **kwargs):
        """
        SQLModel UBY时间列定义（儒略日存储）
        """
        return Field(default=default, sa_column=sa.Column(UBYJulianDayType), **kwargs)


class UBYTimeQueryBuilder:
    """
    UBY时间查询构建器
    提供跨ORM的统一查询接口
    """
    
    def __init__(self, orm_type: str, model_class: Type, field_name: str):
        """
        初始化查询构建器
        
        Args:
            orm_type: ORM类型 ('sqlalchemy', 'django', 'peewee')
            model_class: 模型类
            field_name: UBY时间字段名
        """
        self.orm_type = orm_type.lower()
        self.model_class = model_class
        self.field_name = field_name
    
    def filter_by_uby_range(self, 
                           start_time: Union[str, UBYTime],
                           end_time: Union[str, UBYTime],
                           session=None):
        """
        按UBY时间范围过滤
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            session: 数据库会话（SQLAlchemy需要）
        
        Returns:
            查询对象或结果集
        """
        start_uby = start_time if isinstance(start_time, UBYTime) else UBYTime.from_uby_string(start_time)
        end_uby = end_time if isinstance(end_time, UBYTime) else UBYTime.from_uby_string(end_time)
        
        if self.orm_type == 'sqlalchemy':
            if not session:
                raise ValueError("SQLAlchemy requires a session")
            
            field_getter = operator.attrgetter(self.field_name)
            field = field_getter(self.model_class)
            # 使用简化格式进行SQL比较
            return session.query(self.model_class).filter(
                field >= start_uby.to_uby_string(simplified=True),
                field <= end_uby.to_uby_string(simplified=True)
            )
        
        elif self.orm_type == 'django':
            field_gte = f"{self.field_name}__gte"
            field_lte = f"{self.field_name}__lte"
            return self.model_class.objects.filter(**{
                field_gte: start_uby,
                field_lte: end_uby
            })
        
        elif self.orm_type == 'peewee':
            field_getter = operator.attrgetter(self.field_name)
            field = field_getter(self.model_class)
            return self.model_class.select().where(
                (field >= start_uby) & (field <= end_uby)
            )
        
        else:
            raise ValueError(f"Unsupported ORM type: {self.orm_type}")
    
    def filter_by_uby_scale(self, 
                           scale: str,
                           session=None):
        """
        按UBY时间尺度过滤
        
        Args:
            scale: 时间尺度 ('G', 'M', 'K', 等)
            session: 数据库会话（SQLAlchemy需要）
        """
        # 根据尺度确定范围
        scale_ranges = {
            'G': ('1G', '999G'),
            'M': ('1M', '999M'),
            'K': ('1K', '999K'),
            '': ('1', '999')  # 年尺度
        }
        
        if scale not in scale_ranges:
            raise ValueError(f"Unsupported scale: {scale}")
        
        start_str, end_str = scale_ranges[scale]
        return self.filter_by_uby_range(start_str, end_str, session)
    
    def order_by_uby_time(self, ascending: bool = True, session=None):
        """
        按UBY时间排序
        
        Args:
            ascending: 是否升序
            session: 数据库会话（SQLAlchemy需要）
        """
        if self.orm_type == 'sqlalchemy':
            if not session:
                raise ValueError("SQLAlchemy requires a session")
            
            field = getattr(self.model_class, self.field_name)
            order_func = field.asc() if ascending else field.desc()
            return session.query(self.model_class).order_by(order_func)
        
        elif self.orm_type == 'django':
            order_field = self.field_name if ascending else f"-{self.field_name}"
            return self.model_class.objects.order_by(order_field)
        
        elif self.orm_type == 'peewee':
            field = getattr(self.model_class, self.field_name)
            order_func = field.asc() if ascending else field.desc()
            return self.model_class.select().order_by(order_func)
        
        else:
            raise ValueError(f"Unsupported ORM type: {self.orm_type}")


class UBYTimeAggregator:
    """
    UBY时间聚合器
    提供时间数据的统计和聚合功能
    """
    
    def __init__(self, orm_type: str, model_class: Type, field_name: str):
        self.orm_type = orm_type.lower()
        self.model_class = model_class
        self.field_name = field_name
    
    def get_temporal_extent(self, session=None) -> Dict[str, str]:
        """
        获取数据的时间范围
        
        Returns:
            包含最早和最晚时间的字典
        """
        if self.orm_type == 'sqlalchemy':
            if not session:
                raise ValueError("SQLAlchemy requires a session")
            
            field_getter = operator.attrgetter(self.field_name)
            field = field_getter(self.model_class)
            result = session.query(
                sa.func.min(field).label('min_time'),
                sa.func.max(field).label('max_time')
            ).first()
            
            return {
                'earliest': result.min_time.to_uby_string(simplified=True) if result.min_time else None,
                'latest': result.max_time.to_uby_string(simplified=True) if result.max_time else None
            }
        
        elif self.orm_type == 'django':
            manager = getattr(self.model_class, "objects", None)
            if manager is None:
                raise RuntimeError("Django manager is not available for this operation")

            if HAS_DJANGO:
                from django.db.models import Min, Max

                result = manager.aggregate(
                    min_time=Min(self.field_name),
                    max_time=Max(self.field_name)
                )
            elif models is not None and hasattr(models, "Min") and hasattr(models, "Max"):
                # 支持测试/轻量 mock 场景：真实 Django 不存在，但调用方提供了
                # 兼容 aggregate 的 manager 和 Min/Max 占位对象。
                result = manager.aggregate(
                    min_time=models.Min(self.field_name),
                    max_time=models.Max(self.field_name)
                )
            else:
                result = manager.aggregate(
                    min_time=self.field_name,
                    max_time=self.field_name
                )

            return {
                'earliest': result['min_time'].to_uby_string(simplified=True) if result['min_time'] else None,
                'latest': result['max_time'].to_uby_string(simplified=True) if result['max_time'] else None
            }
        
        elif self.orm_type == 'peewee':
            if HAS_PEEWEE:
                field_getter = operator.attrgetter(self.field_name)
                field = field_getter(self.model_class)
                
                min_result = self.model_class.select(pw.fn.MIN(field)).scalar()
                max_result = self.model_class.select(pw.fn.MAX(field)).scalar()
                
                return {
                    'earliest': min_result.to_uby_string(simplified=True) if min_result else None,
                    'latest': max_result.to_uby_string(simplified=True) if max_result else None
                }
            else:
                # 如果Peewee不可用，抛出适当的异常
                raise RuntimeError("Peewee not available for this operation")
        
        else:
            raise ValueError(f"Unsupported ORM type: {self.orm_type}")
    
    def count_by_scale(self, session=None) -> Dict[str, int]:
        """
        按时间尺度统计记录数量
        
        Returns:
            各尺度的记录数量
        """
        # 这里需要根据具体ORM实现复杂的分组查询
        # 简化实现：获取所有记录并在Python中分组
        if self.orm_type == 'sqlalchemy':
            if not session:
                raise ValueError("SQLAlchemy requires a session")
            
            records = session.query(self.model_class).all()
            
        elif self.orm_type == 'django':
            manager = getattr(self.model_class, "objects", None)
            if manager is None:
                raise RuntimeError("Django manager is not available for this operation")
            records = list(manager.all())
                
        elif self.orm_type == 'peewee':
            if not hasattr(self.model_class, "select"):
                raise RuntimeError("Peewee select interface is not available for this operation")
            records = list(self.model_class.select())
                
        else:
            raise ValueError(f"Unsupported ORM type: {self.orm_type}")
        
        # 按尺度分组计数
        scale_counts = {'G': 0, 'M': 0, 'K': 0, 'year': 0}
        
        for record in records:
            field_getter = operator.attrgetter(self.field_name)
            uby_time = field_getter(record)
            if uby_time:
                # 如果uby_time是UBYTime对象，转换为字符串进行检测
                if isinstance(uby_time, UBYTime):
                    uby_str = uby_time.to_uby_string(simplified=True)
                else:
                    uby_str = str(uby_time)
                    
                if 'G' in uby_str:
                    scale_counts['G'] += 1
                elif 'M' in uby_str:
                    scale_counts['M'] += 1
                elif 'K' in uby_str:
                    scale_counts['K'] += 1
                else:
                    scale_counts['year'] += 1
        
        return scale_counts


def create_uby_migration_sql(table_name: str, 
                            column_name: str,
                            storage_type: str = 'string',
                            database_type: str = 'postgresql') -> str:
    """
    生成UBY时间字段的数据库迁移SQL
    
    Args:
        table_name: 表名
        column_name: 列名
        storage_type: 存储类型 ('string', 'julian_day')
        database_type: 数据库类型 ('postgresql', 'mysql', 'sqlite')
    
    Returns:
        SQL迁移语句
    """
    if storage_type == 'string':
        if database_type.lower() == 'postgresql':
            sql_type = "VARCHAR(50)"
        elif database_type.lower() == 'mysql':
            sql_type = "VARCHAR(50)"
        elif database_type.lower() == 'sqlite':
            sql_type = "TEXT"
        else:
            sql_type = "VARCHAR(50)"
    
    elif storage_type == 'julian_day':
        if database_type.lower() == 'postgresql':
            sql_type = "DOUBLE PRECISION"
        elif database_type.lower() == 'mysql':
            sql_type = "DOUBLE"
        elif database_type.lower() == 'sqlite':
            sql_type = "REAL"
        else:
            sql_type = "FLOAT"
    
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")
    
    return f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type};"


def check_orm_dependencies() -> Dict[str, bool]:
    """检查ORM相关依赖的可用性"""
    return {
        "sqlalchemy": HAS_SQLALCHEMY,
        "django": HAS_DJANGO,
        "peewee": HAS_PEEWEE,
        "sqlmodel": HAS_SQLMODEL
    }


def get_supported_orm_frameworks() -> List[str]:
    """获取支持的ORM框架列表"""
    frameworks = []
    
    if HAS_SQLALCHEMY:
        frameworks.append("sqlalchemy")
    
    if HAS_DJANGO:
        frameworks.append("django")
    
    if HAS_PEEWEE:
        frameworks.append("peewee")
    
    if HAS_SQLMODEL:
        frameworks.append("sqlmodel")
    
    return frameworks


# 便捷函数
def create_uby_query_builder(orm_type: str, model_class: Type, field_name: str) -> UBYTimeQueryBuilder:
    """创建UBY时间查询构建器"""
    return UBYTimeQueryBuilder(orm_type, model_class, field_name)


def create_uby_aggregator(orm_type: str, model_class: Type, field_name: str) -> UBYTimeAggregator:
    """创建UBY时间聚合器"""
    return UBYTimeAggregator(orm_type, model_class, field_name)
