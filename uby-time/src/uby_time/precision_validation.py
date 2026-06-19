"""
精度验证和警告机制
检测UBY时间计算中的精度丢失并提供警告和建议
"""

from __future__ import annotations

from decimal import Decimal, getcontext, localcontext
from typing import Optional, List, Tuple
from dataclasses import dataclass

from .models import UBYTime, ValidationMessage


@dataclass(frozen=True)
class PrecisionLossWarning:
    """精度丢失警告信息"""
    code: str
    level: str  # "warning" or "error"
    message: str
    original_precision: int
    lost_precision: int
    suggested_solution: str


def validate_precision_loss(
    uby_value: Decimal,
    original_components: List[Decimal],
    tolerance: Decimal = Decimal('1e-50')
) -> List[PrecisionLossWarning]:
    """
    检测精度丢失并发出警告
    
    Args:
        uby_value: 最终的UBY值
        original_components: 原始组成部分（如基准值和增量）
        tolerance: 精度丢失容忍度
    
    Returns:
        精度丢失警告列表
    """
    warnings = []
    
    if len(original_components) < 2:
        return warnings
    
    # 计算理论上的精确值
    with localcontext() as ctx:
        ctx.prec = 200  # 使用高精度计算
        theoretical_sum = sum(original_components)
    
    # 检查精度丢失
    difference = abs(theoretical_sum - uby_value)
    
    if difference > tolerance:
        # 分析精度丢失的程度
        if theoretical_sum != 0:
            relative_loss = (difference / abs(theoretical_sum)) * Decimal('100')
        else:
            relative_loss = Decimal('100')
        
        # 分析数量级差异
        magnitudes = [abs(comp).adjusted() if comp != 0 else -999 for comp in original_components]
        magnitude_range = max(magnitudes) - min(magnitudes) if magnitudes else 0
        
        # 确定警告级别
        if relative_loss > Decimal('0.001'):  # > 0.001%
            level = "error"
        else:
            level = "warning"
        
        # 生成建议解决方案
        if magnitude_range > 50:
            suggestion = "建议使用分离存储方案：将基准值和微小偏移量分开存储"
        elif magnitude_range > 20:
            suggestion = "建议使用高精度Decimal上下文或科学记数法表示"
        else:
            suggestion = "建议增加Decimal精度设置"
        
        warnings.append(PrecisionLossWarning(
            code="PRECISION_LOSS_DETECTED",
            level=level,
            message=f"检测到精度丢失：理论值与实际值差异为 {difference:.2e}，相对误差 {relative_loss:.6f}%",
            original_precision=len(str(theoretical_sum).replace('.', '').replace('-', '')),
            lost_precision=int(abs(difference.adjusted())) if difference != 0 else 0,
            suggested_solution=suggestion
        ))
    
    return warnings


def analyze_magnitude_compatibility(components: List[Decimal]) -> List[PrecisionLossWarning]:
    """
    分析组件之间的数量级兼容性
    
    Args:
        components: 要分析的数值组件列表
    
    Returns:
        兼容性警告列表
    """
    warnings = []
    
    if len(components) < 2:
        return warnings
    
    # 计算数量级
    magnitudes = []
    for comp in components:
        if comp == 0:
            magnitudes.append(-999)  # 特殊标记零值
        else:
            magnitudes.append(abs(comp).adjusted())
    
    # 过滤掉零值
    non_zero_magnitudes = [m for m in magnitudes if m != -999]
    
    if len(non_zero_magnitudes) < 2:
        return warnings
    
    magnitude_range = max(non_zero_magnitudes) - min(non_zero_magnitudes)
    
    # 根据数量级差异给出警告
    if magnitude_range > 100:
        warnings.append(PrecisionLossWarning(
            code="EXTREME_MAGNITUDE_DIFFERENCE",
            level="error",
            message=f"极端数量级差异：{magnitude_range}个数量级，严重精度丢失风险",
            original_precision=0,
            lost_precision=int(magnitude_range),
            suggested_solution="强烈建议使用分离存储或专用高精度算法"
        ))
    elif magnitude_range > 50:
        warnings.append(PrecisionLossWarning(
            code="HIGH_MAGNITUDE_DIFFERENCE",
            level="warning",
            message=f"高数量级差异：{magnitude_range}个数量级，可能存在精度丢失",
            original_precision=0,
            lost_precision=int(magnitude_range),
            suggested_solution="建议使用高精度Decimal上下文或分离存储"
        ))
    elif magnitude_range > 20:
        warnings.append(PrecisionLossWarning(
            code="MODERATE_MAGNITUDE_DIFFERENCE",
            level="warning",
            message=f"中等数量级差异：{magnitude_range}个数量级，建议注意精度",
            original_precision=0,
            lost_precision=int(magnitude_range),
            suggested_solution="建议增加Decimal精度或使用科学记数法"
        ))
    
    return warnings


def suggest_precision_strategy(
    base_value: Decimal,
    increment: Decimal,
    target_precision: int = 50
) -> Tuple[str, str]:
    """
    为给定的基准值和增量建议精度策略
    
    Args:
        base_value: 基准值
        increment: 增量值
        target_precision: 目标精度位数
    
    Returns:
        (策略名称, 详细建议)
    """
    if increment == 0:
        return ("standard", "使用标准精度即可")
    
    base_magnitude = abs(base_value).adjusted() if base_value != 0 else 0
    increment_magnitude = abs(increment).adjusted()
    magnitude_diff = base_magnitude - increment_magnitude
    
    if magnitude_diff > 100:
        return (
            "separated_storage",
            f"分离存储策略：基准值({base_value})和增量({increment})分开存储，"
            f"数量级差异{magnitude_diff}过大，需要专门处理"
        )
    elif magnitude_diff > 50:
        return (
            "high_precision_decimal",
            f"高精度Decimal策略：使用{target_precision * 2}位精度，"
            f"数量级差异{magnitude_diff}需要额外精度保证"
        )
    elif magnitude_diff > 20:
        return (
            "enhanced_precision",
            f"增强精度策略：使用{target_precision}位精度，"
            f"数量级差异{magnitude_diff}在可控范围内"
        )
    else:
        return (
            "standard_precision",
            f"标准精度策略：当前精度足够，数量级差异{magnitude_diff}较小"
        )


def create_precision_aware_uby_time(
    base_uby: Decimal,
    increment: Decimal,
    **kwargs
) -> Tuple[UBYTime, List[PrecisionLossWarning]]:
    """
    创建精度感知的UBYTime对象
    
    Args:
        base_uby: 基准UBY值
        increment: 增量值
        **kwargs: UBYTime的其他参数
    
    Returns:
        (UBYTime对象, 精度警告列表)
    """
    warnings = []
    
    # 分析数量级兼容性
    magnitude_warnings = analyze_magnitude_compatibility([base_uby, increment])
    warnings.extend(magnitude_warnings)
    
    # 计算最终值
    with localcontext() as ctx:
        ctx.prec = 200  # 使用高精度
        precise_value = base_uby + increment
    
    # 使用标准精度创建UBYTime对象
    final_uby_value = base_uby + increment
    
    # 检测精度丢失
    precision_warnings = validate_precision_loss(
        final_uby_value,
        [base_uby, increment]
    )
    warnings.extend(precision_warnings)
    
    # 创建UBYTime对象
    uby_time = UBYTime(
        uby_value=final_uby_value,
        **kwargs
    )
    
    return uby_time, warnings


def format_precision_warnings(warnings: List[PrecisionLossWarning]) -> str:
    """
    格式化精度警告信息
    
    Args:
        warnings: 警告列表
    
    Returns:
        格式化的警告文本
    """
    if not warnings:
        return "✅ 未检测到精度问题"
    
    lines = ["⚠️  精度验证报告:"]
    
    for i, warning in enumerate(warnings, 1):
        level_symbol = "❌" if warning.level == "error" else "⚠️"
        lines.append(f"\n{i}. {level_symbol} [{warning.code}] {warning.message}")
        lines.append(f"   建议: {warning.suggested_solution}")
    
    return "\n".join(lines)


# 为现有的validation模块添加精度验证
def validate_uby_time_with_precision(uby: UBYTime) -> List[ValidationMessage]:
    """
    扩展的UBY时间验证，包含精度检查
    
    Args:
        uby: UBYTime对象
    
    Returns:
        验证消息列表
    """
    from .validation import validate_uby_time
    
    # 获取标准验证消息
    messages = validate_uby_time(uby)
    
    # 添加精度相关的验证
    # 这里可以根据UBYTime对象的特征进行精度验证
    # 例如检查是否存在可能的精度丢失模式
    
    # 检查极端数量级
    if abs(uby.uby_value) > Decimal('1e50'):
        messages.append(ValidationMessage(
            "EXTREME_LARGE_VALUE",
            "warning",
            f"UBY值 {uby.uby_value} 非常大，可能存在精度问题"
        ))
    
    # 检查极小增量（通过检查小数位数）
    value_str = str(uby.uby_value)
    if '.' in value_str:
        decimal_places = len(value_str.split('.')[1].rstrip('0'))
        if decimal_places > 30:
            messages.append(ValidationMessage(
                "HIGH_DECIMAL_PRECISION",
                "info",
                f"UBY值包含{decimal_places}位小数，建议验证精度保持"
            ))
    
    return messages
