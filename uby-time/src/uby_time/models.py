from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional, Tuple
import re

from .constants import (
    DEFAULT_ANCHOR_ID,
    DEFAULT_ANCHOR_JD,
    DEFAULT_ANCHOR_UBY,
    DEFAULT_MODEL_VERSION,
    DEFAULT_ROUNDING_RULE,
    GENERATED_BY,
    UBY_SPEC_VERSION,
)


class PrecisionLevel(str, Enum):
    LEVEL_1 = "Level 1"
    LEVEL_2 = "Level 2"
    LEVEL_3 = "Level 3"


@dataclass(frozen=True)
class UBYAnchor:
    anchor_id: str
    anchor_iso: str
    anchor_jd: Decimal
    anchor_uby: Decimal
    model_version: str
    uby_version: str


@dataclass(frozen=True)
class UBYTime:
    uby_value: Decimal
    uby_version: str
    model_version: Optional[str]
    precision_level: PrecisionLevel
    source_time: Optional[str]
    source_system: Optional[str]
    rounding_rule: str
    generated_by: str
    anchor_id: str
    anchor_jd: Decimal
    anchor_uby: Decimal
    uncertainty_years: Optional[Decimal] = None
    confidence_level: Optional[Decimal] = None
    interval_start_uby: Optional[Decimal] = None
    interval_end_uby: Optional[Decimal] = None
    uncertainty_kind: Optional[str] = None
    propagation_note: Optional[str] = None

    @staticmethod
    def from_uby_string(uby_str: str) -> 'UBYTime':
        """从UBY字符串创建UBYTime实例，支持完整格式和简化格式"""
        from .parsing import parse_uby_expression
        from .constants import MAGNITUDE_FACTORS
        
        # 如果输入已经是完整UBY格式（以UBY开头），直接解析
        if uby_str.strip().upper().startswith('UBY'):
            parsed = parse_uby_expression(uby_str)
            
            # 从解析结果创建UBYTime实例
            return UBYTime(
                uby_value=parsed.uby_value,
                uby_version=parsed.uby_version or UBY_SPEC_VERSION,
                model_version=parsed.model_version,
                precision_level=parsed.precision_level or PrecisionLevel.LEVEL_1,
                source_time=parsed.raw,
                source_system="UBYExpression",
                rounding_rule=DEFAULT_ROUNDING_RULE,
                generated_by=GENERATED_BY,
                anchor_id=DEFAULT_ANCHOR_ID,
                anchor_jd=DEFAULT_ANCHOR_JD,
                anchor_uby=DEFAULT_ANCHOR_UBY,
            )
        else:
            # 处理简化格式，如 "1G", "13.8G", "500M" 等
            # 检查是否为带量级的格式
            mag_pattern = r'^(\d+(?:\.\d+)?)\s*([KMGTP])$'
            match = re.match(mag_pattern, uby_str.strip().upper())
            
            if match:
                value_part = match.group(1)
                magnitude = match.group(2)
                
                numeric_value = Decimal(value_part)
                multiplier = MAGNITUDE_FACTORS.get(magnitude, Decimal('1'))
                final_value = numeric_value * multiplier
                
                # 确定精度级别
                precision_level = PrecisionLevel.LEVEL_2  # 量级格式通常属于二级精度
                
                return UBYTime(
                    uby_value=final_value,
                    uby_version=UBY_SPEC_VERSION,
                    model_version=DEFAULT_MODEL_VERSION,
                    precision_level=precision_level,
                    source_time=uby_str,
                    source_system="UBYExpression",
                    rounding_rule=DEFAULT_ROUNDING_RULE,
                    generated_by=GENERATED_BY,
                    anchor_id=DEFAULT_ANCHOR_ID,
                    anchor_jd=DEFAULT_ANCHOR_JD,
                    anchor_uby=DEFAULT_ANCHOR_UBY,
                )
            else:
                # 如果不是量级格式，尝试解析为纯数字（年数）
                try:
                    numeric_value = Decimal(uby_str.strip())
                    
                    # 根据数值大小判断精度级别
                    if numeric_value < Decimal("1000000"):  # 小于1百万年，一级精度
                        precision_level = PrecisionLevel.LEVEL_1
                    elif numeric_value < Decimal("100000000000"):  # 小于1000亿年，二级精度
                        precision_level = PrecisionLevel.LEVEL_2
                    else:  # 更大的数值，三级精度
                        precision_level = PrecisionLevel.LEVEL_3
                    
                    return UBYTime(
                        uby_value=numeric_value,
                        uby_version=UBY_SPEC_VERSION,
                        model_version=DEFAULT_MODEL_VERSION,
                        precision_level=precision_level,
                        source_time=uby_str,
                        source_system="UBYExpression",
                        rounding_rule=DEFAULT_ROUNDING_RULE,
                        generated_by=GENERATED_BY,
                        anchor_id=DEFAULT_ANCHOR_ID,
                        anchor_jd=DEFAULT_ANCHOR_JD,
                        anchor_uby=DEFAULT_ANCHOR_UBY,
                    )
                except:
                    # 如果所有解析都失败，尝试加上"UBY "前缀再解析
                    try:
                        parsed = parse_uby_expression(f"UBY {uby_str}")
                        
                        return UBYTime(
                            uby_value=parsed.uby_value,
                            uby_version=parsed.uby_version or UBY_SPEC_VERSION,
                            model_version=parsed.model_version,
                            precision_level=parsed.precision_level or PrecisionLevel.LEVEL_1,
                            source_time=parsed.raw,
                            source_system="UBYExpression",
                            rounding_rule=DEFAULT_ROUNDING_RULE,
                            generated_by=GENERATED_BY,
                            anchor_id=DEFAULT_ANCHOR_ID,
                            anchor_jd=DEFAULT_ANCHOR_JD,
                            anchor_uby=DEFAULT_ANCHOR_UBY,
                        )
                    except:
                        raise ValueError(f"Cannot parse UBY string: {uby_str}")

    def to_uby_string(self, simplified: bool = False) -> str:
        """将UBYTime实例转换为UBY字符串格式"""
        # 如果明确指定使用简化格式，或者当前实例是由简化格式创建的，返回简化格式
        if simplified or (self.source_time and not self.source_time.upper().startswith('UBY ')):
            # 检查原始输入是否是简化格式（如"1G", "13.8G"等）
            if self.source_time:
                # 检查是否是量级格式
                mag_pattern = r'^(\d+(?:\.\d+)?)\s*([KMGTP])$'
                if re.match(mag_pattern, self.source_time.strip().upper()):
                    return self.source_time
        
        # 默认返回完整格式
        result = f"UBY {self.uby_value}"
        
        # 添加标签
        tags = []
        if self.model_version:
            tags.append(f"[model={self.model_version}]")
        if self.uby_version:
            tags.append(f"[spec={self.uby_version}]")
        
        if tags:
            result += " " + " ".join(tags)
        
        return result

    @staticmethod
    def from_julian_day(jd: float) -> 'UBYTime':
        """从儒略日创建UBYTime实例"""
        from .conversion import jd_to_uby
        
        # jd_to_uby 返回完整 UBYTime 对象；这里直接复用该参考转换结果，
        # 避免把 UBYTime 实例误写入 uby_value 字段。
        return jd_to_uby(
            Decimal(str(jd)),
            source_time=str(jd),
            source_system="JulianDay",
        )

    def to_julian_day(self) -> float:
        """将UBYTime实例转换为儒略日"""
        from .conversion import uby_to_jd
        
        # 使用转换函数将UBY转换为儒略日
        jd_value = uby_to_jd(self.uby_value)
        return float(jd_value)

    def with_uncertainty(self, 
                        uncertainty_years: Optional[Decimal] = None, 
                        confidence_level: Optional[Decimal] = None,
                        interval_start: Optional[Decimal] = None,
                        interval_end: Optional[Decimal] = None,
                        uncertainty_kind: Optional[str] = None) -> 'UBYTime':
        """
        创建带有不确定性信息的新UBYTime实例
        
        Args:
            uncertainty_years: 不确定性年数
            confidence_level: 置信水平
            interval_start: 区间开始值
            interval_end: 区间结束值
            uncertainty_kind: 不确定性类型
        
        Returns:
            带有不确定性信息的UBYTime实例
        """
        return UBYTime(
            uby_value=self.uby_value,
            uby_version=self.uby_version,
            model_version=self.model_version,
            precision_level=self.precision_level,
            source_time=self.source_time,
            source_system=self.source_system,
            rounding_rule=self.rounding_rule,
            generated_by=self.generated_by,
            anchor_id=self.anchor_id,
            anchor_jd=self.anchor_jd,
            anchor_uby=self.anchor_uby,
            uncertainty_years=uncertainty_years if uncertainty_years is not None else self.uncertainty_years,
            confidence_level=confidence_level if confidence_level is not None else self.confidence_level,
            interval_start_uby=interval_start if interval_start is not None else self.interval_start_uby,
            interval_end_uby=interval_end if interval_end is not None else self.interval_end_uby,
            uncertainty_kind=uncertainty_kind if uncertainty_kind is not None else self.uncertainty_kind,
            propagation_note=self.propagation_note
        )

    def get_confidence_interval(self) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """
        获取置信区间
        
        Returns:
            (下界, 上界) 元组
        """
        if self.interval_start_uby is not None and self.interval_end_uby is not None:
            return (self.interval_start_uby, self.interval_end_uby)
        elif self.uby_value is not None and self.uncertainty_years is not None:
            lower = self.uby_value - self.uncertainty_years
            upper = self.uby_value + self.uncertainty_years
            return (lower, upper)
        else:
            return (None, None)

    def get_relative_uncertainty(self) -> Optional[Decimal]:
        """
        获取相对不确定性（百分比）
        
        Returns:
            相对不确定性百分比
        """
        if self.uncertainty_years is not None and abs(self.uby_value) > Decimal('1e-10'):
            return (self.uncertainty_years / abs(self.uby_value)) * Decimal('100')
        return None

    def propagate_uncertainty_add(self, other: 'UBYTime') -> 'UBYTime':
        """
        传播加法运算的不确定性
        
        Args:
            other: 另一个UBYTime实例
        
        Returns:
            带有传播后不确定性的新UBYTime实例
        """
        from .uncertainty import decimal_sqrt
        
        # 计算合成不确定性 (RSS - Root Sum of Squares)
        unc1 = self.uncertainty_years or Decimal('0')
        unc2 = other.uncertainty_years or Decimal('0')
        
        combined_uncertainty = decimal_sqrt(unc1 ** 2 + unc2 ** 2)
        
        # 使用较低的置信水平，因为组合了多个不确定性源
        confidence = min(
            self.confidence_level or Decimal('0.68'),
            other.confidence_level or Decimal('0.68')
        )
        
        new_value = self.uby_value + other.uby_value
        
        return UBYTime(
            uby_value=new_value,
            uby_version=max(self.uby_version, other.uby_version),
            model_version=self.model_version or other.model_version,
            precision_level=min([self.precision_level, other.precision_level], 
                               key=lambda x: ["Level 1", "Level 2", "Level 3"].index(x.value)),
            source_time=f"Sum({self.source_time}, {other.source_time})",
            source_system="UncertaintyPropagation",
            rounding_rule=self.rounding_rule,
            generated_by=GENERATED_BY,
            anchor_id=self.anchor_id if self.anchor_id == other.anchor_id else DEFAULT_ANCHOR_ID,
            anchor_jd=self.anchor_jd if self.anchor_jd == other.anchor_jd else DEFAULT_ANCHOR_JD,
            anchor_uby=self.anchor_uby if self.anchor_uby == other.anchor_uby else DEFAULT_ANCHOR_UBY,
            uncertainty_years=combined_uncertainty,
            confidence_level=confidence,
            interval_start_uby=new_value - combined_uncertainty,
            interval_end_uby=new_value + combined_uncertainty,
            uncertainty_kind="propagated_addition",
            propagation_note=f"Propagated from addition of {self.uby_value}±{unc1} and {other.uby_value}±{unc2}"
        )

    def propagate_uncertainty_multiply(self, factor: Decimal) -> 'UBYTime':
        """
        传播乘法运算的不确定性
        
        Args:
            factor: 乘数因子
        
        Returns:
            带有传播后不确定性的新UBYTime实例
        """
        from .uncertainty import decimal_sqrt
        
        # 计算相对不确定性
        if self.uncertainty_years and abs(self.uby_value) > Decimal('1e-10'):
            rel_uncertainty = self.uncertainty_years / abs(self.uby_value)
            new_abs_uncertainty = abs(factor) * rel_uncertainty * abs(self.uby_value)
        else:
            new_abs_uncertainty = Decimal('0')
        
        new_value = self.uby_value * factor
        
        return UBYTime(
            uby_value=new_value,
            uby_version=self.uby_version,
            model_version=self.model_version,
            precision_level=self.precision_level,
            source_time=f"Product({self.source_time}, {factor})",
            source_system="UncertaintyPropagation",
            rounding_rule=self.rounding_rule,
            generated_by=self.generated_by,
            anchor_id=self.anchor_id,
            anchor_jd=self.anchor_jd,
            anchor_uby=self.anchor_uby,
            uncertainty_years=new_abs_uncertainty,
            confidence_level=self.confidence_level,
            interval_start_uby=new_value - new_abs_uncertainty,
            interval_end_uby=new_value + new_abs_uncertainty,
            uncertainty_kind="propagated_multiplication",
            propagation_note=f"Propagated from multiplication of {self.uby_value}±{self.uncertainty_years or 0} by {factor}"
        )

    def get_effective_precision_level(self) -> str:
        """
        根据不确定性确定有效的精度级别
        
        Returns:
            有效的精度级别
        """
        if self.uncertainty_years is None:
            return self.precision_level.value
        
        rel_uncertainty = (self.uncertainty_years / abs(self.uby_value)) * Decimal('100') if abs(self.uby_value) > Decimal('1e-10') else Decimal('0')
        
        # 根据相对不确定性确定精度级别
        if rel_uncertainty < Decimal('0.001'):  # < 0.001%
            return "Level 1"
        elif rel_uncertainty < Decimal('0.1'):   # < 0.1%
            return "Level 2"
        else:                                    # >= 0.1%
            return "Level 3"


@dataclass(frozen=True)
class ParsedUBYExpression:
    notation: str
    uby_value: Decimal
    model_version: Optional[str]
    uby_version: Optional[str]
    precision_level: Optional[PrecisionLevel]
    raw: str
    warnings: list[str] = field(default_factory=list)
    mnemonic_prefix: Optional[int] = None


@dataclass(frozen=True)
class ValidationMessage:
    code: str
    level: str
    message: str


@dataclass(frozen=True)
class UBYUncertainty:
    uncertainty_years: Optional[Decimal] = None
    confidence_level: Optional[Decimal] = None
    interval_start_uby: Optional[Decimal] = None
    interval_end_uby: Optional[Decimal] = None
    uncertainty_kind: Optional[str] = None
    propagation_note: Optional[str] = None
