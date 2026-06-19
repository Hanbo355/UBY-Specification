"""
UBY时间标注规范 - 不确定性量化与误差传播模块

实现时间不确定性量化和误差传播计算，
特别是在跨尺度时间转换过程中的误差管理。
"""

from decimal import Decimal
from typing import Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import math


class UncertaintyType(Enum):
    """不确定性类型枚举"""
    ABSOLUTE = "absolute"          # 绝对误差（年）
    RELATIVE = "relative"          # 相对误差（百分比）
    GAUSSIAN = "gaussian"          # 高斯分布（标准差）
    INTERVAL = "interval"          # 区间估计
    CONFIDENCE = "confidence"      # 置信区间


@dataclass(frozen=True)
class UncertaintyEstimate:
    """不确定性估计值"""
    value: Decimal
    uncertainty_type: UncertaintyType
    confidence_level: Optional[Decimal] = None  # 置信水平（如0.95表示95%置信区间）
    distribution: Optional[str] = None          # 分布类型（如"normal", "uniform"等）
    notes: Optional[str] = None                 # 附加说明


def decimal_sqrt(d: Decimal) -> Decimal:
    """计算Decimal的平方根"""
    # 将Decimal转换为float进行平方根计算，然后再转回Decimal
    return Decimal(str(math.sqrt(float(d))))


class UncertaintyCalculator:
    """
    不确定性计算器
    提供时间转换过程中的误差传播计算功能
    """
    
    @staticmethod
    def calculate_absolute_uncertainty(
        base_value: Decimal, 
        relative_error_percent: Decimal
    ) -> Decimal:
        """
        根据相对误差计算绝对误差
        
        Args:
            base_value: 基础数值
            relative_error_percent: 相对误差百分比（如5.0表示5%）
        
        Returns:
            绝对误差值
        """
        return abs(base_value) * (relative_error_percent / Decimal('100.0'))
    
    @staticmethod
    def propagate_additive_uncertainty(
        uncertainties: list[Union[Decimal, UncertaintyEstimate]]
    ) -> UncertaintyEstimate:
        """
        计算加法运算的误差传播（平方和的平方根）
        
        Args:
            uncertainties: 不确定性列表
        
        Returns:
            传播后的不确定性估计
        """
        total_sq = Decimal('0')
        for unc in uncertainties:
            if isinstance(unc, UncertaintyEstimate):
                val = unc.value
            else:
                val = unc
            total_sq += val * val
        
        result_value = decimal_sqrt(total_sq)
        return UncertaintyEstimate(
            value=result_value,
            uncertainty_type=UncertaintyType.ABSOLUTE
        )
    
    @staticmethod
    def propagate_multiplicative_uncertainty(
        base_value: Decimal,
        uncertainties: list[Tuple[Decimal, UncertaintyEstimate]]  # (factor, uncertainty)
    ) -> UncertaintyEstimate:
        """
        计算乘法运算的误差传播
        
        Args:
            base_value: 基础值
            uncertainties: 因子及其不确定性列表 [(factor, uncertainty)]
        
        Returns:
            传播后的不确定性估计
        """
        # 使用相对误差传播公式
        relative_sq_sum = Decimal('0')
        
        for factor, unc_estimate in uncertainties:
            if unc_estimate.uncertainty_type == UncertaintyType.RELATIVE:
                rel_unc = unc_estimate.value / Decimal('100.0')  # 转换为小数形式
            else:
                # 如果是绝对误差，转换为相对误差
                if abs(factor) > Decimal('1e-20'):  # 避免除以零
                    rel_unc = unc_estimate.value / abs(factor)
                else:
                    rel_unc = Decimal('0')
            
            relative_sq_sum += rel_unc * rel_unc
        
        # 最终的相对误差
        final_rel_unc = decimal_sqrt(relative_sq_sum)
        # 转换为绝对误差
        absolute_unc = abs(base_value) * final_rel_unc
        
        return UncertaintyEstimate(
            value=absolute_unc,
            uncertainty_type=UncertaintyType.ABSOLUTE
        )
    
    @staticmethod
    def calculate_confidence_interval(
        central_value: Decimal,
        uncertainty: Union[Decimal, UncertaintyEstimate],
        confidence_level: Decimal = Decimal('0.95')
    ) -> Tuple[Decimal, Decimal]:
        """
        计算置信区间（假设正态分布）
        
        Args:
            central_value: 中心值
            uncertainty: 不确定性（如果是UncertaintyEstimate且为高斯类型，则使用标准差）
            confidence_level: 置信水平（如0.95表示95%）
        
        Returns:
            (下界, 上界) 元组
        """
        # 简化处理：使用标准正态分布的近似倍数
        # 95%置信区间约为1.96个标准差
        z_values = {
            Decimal('0.90'): Decimal('1.645'),
            Decimal('0.95'): Decimal('1.96'),
            Decimal('0.99'): Decimal('2.576')
        }
        
        z_factor = z_values.get(confidence_level, Decimal('1.96'))
        
        if isinstance(uncertainty, UncertaintyEstimate):
            unc_value = uncertainty.value
        else:
            unc_value = uncertainty
            
        margin = unc_value * z_factor
        
        lower_bound = central_value - margin
        upper_bound = central_value + margin
        
        return (lower_bound, upper_bound)
    
    @staticmethod
    def combine_uncertainties(
        estimates: list[UncertaintyEstimate],
        combination_method: str = "quadratic"  # "quadratic", "linear", "max"
    ) -> UncertaintyEstimate:
        """
        组合多个不确定性估计
        
        Args:
            estimates: 不确定性估计列表
            combination_method: 组合方法
        
        Returns:
            组合后的不确定性估计
        """
        if not estimates:
            return UncertaintyEstimate(
                value=Decimal('0'),
                uncertainty_type=UncertaintyType.ABSOLUTE
            )
        
        values = [est.value for est in estimates]
        
        if combination_method == "quadratic":
            # 二次组合（平方和的平方根）
            total_sq = sum(v*v for v in values)
            combined_value = decimal_sqrt(total_sq)
        elif combination_method == "linear":
            # 线性组合（简单相加）
            combined_value = sum(values)
        elif combination_method == "max":
            # 取最大值
            combined_value = max(values)
        else:
            raise ValueError(f"Unknown combination method: {combination_method}")
        
        return UncertaintyEstimate(
            value=combined_value,
            uncertainty_type=UncertaintyType.ABSOLUTE
        )


class UBYUncertaintyManager:
    """
    UBY不确定性管理器
    专门处理UBY时间值的不确定性
    """
    
    def __init__(self):
        self.calculator = UncertaintyCalculator()
    
    def estimate_conversion_uncertainty(
        self,
        from_precision_level: str,
        to_precision_level: str,
        base_value: Decimal
    ) -> UncertaintyEstimate:
        """
        估算跨精度级别转换的不确定性
        
        Args:
            from_precision_level: 源精度级别
            to_precision_level: 目标精度级别
            base_value: 基础值
        
        Returns:
            转换过程的不确定性估计
        """
        # 根据精度级别设置典型不确定性
        precision_uncertainties = {
            "Level 1": Decimal('100'),      # ±100年（相对精确计量级）
            "Level 2": Decimal('1000000'),  # ±100万年（比例叙事级）
            "Level 3": Decimal('10000000'), # ±1000万年（模型依赖级）
        }
        
        # 获取目标精度的固有不确定性
        base_uncertainty = precision_uncertainties.get(to_precision_level, Decimal('1000000'))
        
        # 根据值的大小调整不确定性（对于极大值可能需要更大容差）
        size_factor = Decimal('1')
        if base_value > Decimal('1e10'):  # 大于100亿年
            size_factor = Decimal('10')
        elif base_value > Decimal('1e9'):   # 大于10亿年
            size_factor = Decimal('5')
        elif base_value > Decimal('1e8'):   # 大于1亿年
            size_factor = Decimal('2')
        
        final_uncertainty = base_uncertainty * size_factor
        
        return UncertaintyEstimate(
            value=final_uncertainty,
            uncertainty_type=UncertaintyType.ABSOLUTE,
            confidence_level=Decimal('0.95')
        )
    
    def propagate_through_operations(
        self,
        initial_uncertainty: UncertaintyEstimate,
        operations: list[dict]  # [{'type': 'add', 'operand_unc': estimate}, ...]
    ) -> UncertaintyEstimate:
        """
        通过一系列操作传播不确定性
        
        Args:
            initial_uncertainty: 初始不确定性
            operations: 操作列表
        
        Returns:
            最终不确定性估计
        """
        current_unc = initial_uncertainty
        
        for op in operations:
            op_type = op.get('type')
            operand_unc = op.get('operand_uncertainty', current_unc)
            
            if op_type == 'add':
                current_unc = self.calculator.propagate_additive_uncertainty(
                    [current_unc.value, operand_unc.value]
                )
            elif op_type == 'multiply':
                # 这种情况需要特殊处理，因为我们只有一个操作数的不确定性
                # 简化处理：使用加法传播
                current_unc = self.calculator.propagate_additive_uncertainty(
                    [current_unc.value, operand_unc.value]
                )
            # 可以添加更多操作类型
        
        return current_unc
    
    def get_effective_precision(
        self,
        uby_value: Decimal,
        uncertainty: UncertaintyEstimate
    ) -> str:
        """
        根据不确定性确定有效的精度级别
        
        Args:
            uby_value: UBY值
            uncertainty: 不确定性估计
        
        Returns:
            有效精度级别
        """
        rel_uncertainty = (uncertainty.value / abs(uby_value)) * Decimal('100') if abs(uby_value) > Decimal('1e-10') else Decimal('0')
        
        # 根据相对不确定性确定精度级别
        if rel_uncertainty < Decimal('0.001'):  # < 0.001%
            return "Level 1"
        elif rel_uncertainty < Decimal('0.1'):   # < 0.1%
            return "Level 2"
        else:                                    # >= 0.1%
            return "Level 3"
    
    def format_with_uncertainty(
        self,
        uby_value: Decimal,
        uncertainty: Optional[UncertaintyEstimate] = None,
        precision_digits: int = 2
    ) -> str:
        """
        格式化带有不确定性的UBY值
        
        Args:
            uby_value: UBY值
            uncertainty: 不确定性估计
            precision_digits: 精度位数
        
        Returns:
            格式化的字符串表示
        """
        formatted_value = self._format_number(uby_value, precision_digits)
        
        if uncertainty is None:
            return f"UBY {formatted_value}"
        
        formatted_unc = self._format_number(uncertainty.value, precision_digits)
        
        if uncertainty.uncertainty_type == UncertaintyType.ABSOLUTE:
            result = f"UBY {formatted_value} ± {formatted_unc}"
        else:
            result = f"UBY {formatted_value} ({uncertainty.uncertainty_type.value}: {formatted_unc})"
        
        # 添加置信水平信息
        if uncertainty.confidence_level:
            conf_pct = uncertainty.confidence_level * Decimal('100')
            result += f" [{conf_pct}% CI]"
        
        return result
    
    def _format_number(self, num: Decimal, digits: int) -> str:
        """格式化数字到指定小数位数"""
        format_str = f"{{:.{digits}f}}"
        return format_str.format(num.normalize())


# 便利函数
def create_uby_uncertainty(
    uncertainty_years: Optional[Union[float, Decimal]] = None,
    confidence_level: Optional[Union[float, Decimal]] = None,
    interval_bounds: Optional[Tuple[Union[float, Decimal], Union[float, Decimal]]] = None
) -> dict:
    """
    创建UBY不确定性字典
    
    Args:
        uncertainty_years: 不确定性年数
        confidence_level: 置信水平
        interval_bounds: 区间边界
    
    Returns:
        不确定性参数字典
    """
    result = {}
    
    if uncertainty_years is not None:
        result['uncertainty_years'] = Decimal(str(uncertainty_years))
    
    if confidence_level is not None:
        result['confidence_level'] = Decimal(str(confidence_level))
    
    if interval_bounds is not None:
        result['interval_start_uby'] = Decimal(str(interval_bounds[0]))
        result['interval_end_uby'] = Decimal(str(interval_bounds[1]))
    
    return result


def calculate_conversion_uncertainty(
    from_time: Decimal,
    from_precision: str,
    to_precision: str
) -> UncertaintyEstimate:
    """
    计算时间转换的不确定性
    
    Args:
        from_time: 源时间值
        from_precision: 源精度级别
        to_precision: 目标精度级别
    
    Returns:
        不确定性估计
    """
    manager = UBYUncertaintyManager()
    return manager.estimate_conversion_uncertainty(from_precision, to_precision, from_time)


def combine_uncertainties_quadrature(uncertainties: list[Decimal]) -> Decimal:
    """
    使用二次组合方法组合不确定性（平方和的平方根）
    
    Args:
        uncertainties: 不确定性值列表
    
    Returns:
        组合后的不确定性
    """
    if not uncertainties:
        return Decimal('0')
    
    total_sq = sum(unc * unc for unc in uncertainties)
    return decimal_sqrt(total_sq)


def get_effective_interval(
    central_value: Decimal,
    uncertainty: Decimal,
    confidence_level: Decimal = Decimal('0.95')
) -> Tuple[Decimal, Decimal]:
    """
    获取有效的置信区间
    
    Args:
        central_value: 中心值
        uncertainty: 不确定性
        confidence_level: 置信水平
    
    Returns:
        (下界, 上界) 元组
    """
    calculator = UncertaintyCalculator()
    return calculator.calculate_confidence_interval(central_value, uncertainty, confidence_level)
