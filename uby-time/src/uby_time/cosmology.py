from __future__ import annotations

from decimal import Decimal
from typing import Dict, Optional, Tuple, Any

from .anchors import DEFAULT_ANCHOR
from .constants import DEFAULT_ROUNDING_RULE, GENERATED_BY, UBY_SPEC_VERSION
from .errors import UBYModelError
from .models import PrecisionLevel, UBYTime


class CosmologyManager:
    """
    宇宙学模型管理器，支持多种宇宙学参数集和动态切换
    """
    
    def __init__(self):
        self._current_cosmology = None
        self._custom_cosmologies = {}
        
    def get_available_cosmologies(self) -> Dict[str, str]:
        """获取所有可用的宇宙学模型"""
        try:
            from astropy.cosmology import available
            astropy_cosmologies = {name: f"Astropy built-in: {name}" for name in available}
        except Exception:
            astropy_cosmologies = {}
            
        # 预定义的标准宇宙学模型
        standard_cosmologies = {
            "Planck18": "Planck Collaboration 2018 (最新推荐)",
            "Planck15": "Planck Collaboration 2015",
            "Planck13": "Planck Collaboration 2013", 
            "WMAP9": "WMAP 9-year results",
            "WMAP7": "WMAP 7-year results",
            "WMAP5": "WMAP 5-year results",
            "Millennium": "Millennium Simulation parameters",
            "EdS": "Einstein-de Sitter (Ω_m=1, Ω_Λ=0)",
        }
        
        # 合并自定义宇宙学模型
        custom_cosmologies = {name: f"Custom: {desc}" for name, desc in self._custom_cosmologies.items()}
        
        return {**standard_cosmologies, **astropy_cosmologies, **custom_cosmologies}
    
    def add_custom_cosmology(self, name: str, H0: float, Om0: float, Ode0: float = None, 
                           Tcmb0: float = 2.725, description: str = ""):
        """
        添加自定义宇宙学模型
        
        Args:
            name: 模型名称
            H0: 哈勃常数 (km/s/Mpc)
            Om0: 物质密度参数
            Ode0: 暗能量密度参数 (如果为None，则假设平坦宇宙)
            Tcmb0: CMB温度 (K)
            description: 模型描述
        """
        if Ode0 is None:
            Ode0 = 1.0 - Om0  # 平坦宇宙假设
            
        self._custom_cosmologies[name] = {
            'H0': H0,
            'Om0': Om0, 
            'Ode0': Ode0,
            'Tcmb0': Tcmb0,
            'description': description or f"Custom cosmology: H0={H0}, Ωm={Om0}, ΩΛ={Ode0}"
        }
    
    def get_cosmology(self, name: str):
        """获取指定的宇宙学模型对象"""
        try:
            from astropy.cosmology import (
                Planck18, Planck15, Planck13, WMAP9, WMAP7, WMAP5,
                FlatLambdaCDM, LambdaCDM
            )
            from astropy import units as u
        except Exception as exc:
            raise UBYModelError(
                "Cosmology functions require astropy. Install with: pip install 'uby-time[cosmology]'"
            ) from exc
        
        # 标准预定义模型
        standard_models = {
            "Planck18": Planck18,
            "Planck15": Planck15, 
            "Planck13": Planck13,
            "WMAP9": WMAP9,
            "WMAP7": WMAP7,
            "WMAP5": WMAP5,
            "Millennium": FlatLambdaCDM(H0=73, Om0=0.25, Tcmb0=2.725),
            "EdS": FlatLambdaCDM(H0=70, Om0=1.0, Tcmb0=2.725),
        }
        
        if name in standard_models:
            return standard_models[name]
        elif name in self._custom_cosmologies:
            params = self._custom_cosmologies[name]
            if abs(params['Om0'] + params['Ode0'] - 1.0) < 1e-6:
                # 平坦宇宙
                return FlatLambdaCDM(
                    H0=params['H0'] * u.km / u.s / u.Mpc,
                    Om0=params['Om0'],
                    Tcmb0=params['Tcmb0'] * u.K
                )
            else:
                # 非平坦宇宙
                return LambdaCDM(
                    H0=params['H0'] * u.km / u.s / u.Mpc,
                    Om0=params['Om0'],
                    Ode0=params['Ode0'],
                    Tcmb0=params['Tcmb0'] * u.K
                )
        else:
            # 尝试从astropy获取
            try:
                from astropy.cosmology import get_cosmology
                return get_cosmology(name)
            except Exception:
                raise UBYModelError(f"Unknown cosmology: {name}")
    
    def set_default_cosmology(self, name: str):
        """设置默认宇宙学模型"""
        self._current_cosmology = self.get_cosmology(name)
        
    def get_default_cosmology(self):
        """获取当前默认宇宙学模型"""
        if self._current_cosmology is None:
            self._current_cosmology = self.get_cosmology("Planck18")
        return self._current_cosmology


# 全局宇宙学管理器实例
_cosmology_manager = CosmologyManager()


def get_cosmology_manager() -> CosmologyManager:
    """获取全局宇宙学管理器"""
    return _cosmology_manager


def redshift_to_uby(
    z: float,
    *,
    cosmology_name: str = "Planck18",
    model_version: str = "LCDM-Planck2018",
    uby_version: str = UBY_SPEC_VERSION,
    include_uncertainty: bool = True,
) -> UBYTime:
    """
    将宇宙学红移转换为UBY时间
    
    Args:
        z: 红移值
        cosmology_name: 宇宙学模型名称
        model_version: 模型版本标识
        uby_version: UBY规范版本
        include_uncertainty: 是否包含模型不确定性估计
        
    Returns:
        UBYTime对象，包含转换结果和不确定性信息
    """
    if z < 0:
        raise ValueError("redshift z must be non-negative")

    try:
        from astropy import units as u
    except Exception as exc:
        raise UBYModelError(
            "redshift_to_uby requires astropy. Install with: pip install 'uby-time[cosmology]'"
        ) from exc

    cosmology = _cosmology_manager.get_cosmology(cosmology_name)
    
    # 计算宇宙年龄
    age = cosmology.age(z)
    years = Decimal(str(age.to(u.yr).value))
    
    # 估计模型不确定性
    uncertainty_years = None
    uncertainty_method = None
    if include_uncertainty:
        uncertainty_years, uncertainty_method = _compute_cosmological_uncertainty(
            z, cosmology_name, years, cosmology
        )

    # 构建传播注释
    propagation_note = f"computed by astropy.cosmology.{cosmology_name}.age(z={z})"
    if hasattr(cosmology, 'H0'):
        propagation_note += f"; H0={cosmology.H0:.1f}, Om0={cosmology.Om0:.3f}"
        if hasattr(cosmology, 'Ode0'):
            propagation_note += f", Ode0={cosmology.Ode0:.3f}"
    if include_uncertainty:
        if uncertainty_method == "parameter-covariance-propagation":
            propagation_note += (
                "; uncertainty_years from first-order (linearized) propagation of "
                "published cosmological parameter uncertainties via numerical "
                "partial derivatives of age(z); off-diagonal covariances are "
                "neglected (uncorrelated-parameter approximation)"
            )
        else:
            propagation_note += (
                "; uncertainty_years is a heuristic annotation (no published parameter "
                "uncertainties available for this model), not a strict "
                "parameter-covariance re-integration"
            )

    return UBYTime(
        uby_value=years,
        uby_version=uby_version,
        model_version=model_version,
        precision_level=PrecisionLevel.LEVEL_3,
        source_time=f"z={z}",
        source_system="CosmologicalRedshift",
        rounding_rule=DEFAULT_ROUNDING_RULE,
        generated_by=GENERATED_BY,
        anchor_id=DEFAULT_ANCHOR.anchor_id,
        anchor_jd=DEFAULT_ANCHOR.anchor_jd,
        anchor_uby=DEFAULT_ANCHOR.anchor_uby,
        uncertainty_years=uncertainty_years,
        uncertainty_kind="model",
        propagation_note=propagation_note,
    )


# Published 1-sigma uncertainties for the cosmological parameters that dominate
# the age(z) error budget, per parameter set. Values are taken from the
# corresponding published results and are used for first-order (linearized)
# error propagation, NOT as ad hoc scaling factors.
#
# Units:
#   H0  : km/s/Mpc
#   Om0 : dimensionless
#
# Sources:
#   Planck18 : Planck Collaboration 2018, A&A 641, A6 (TT,TE,EE+lowE+lensing):
#              H0 = 67.36 +/- 0.54, Om0 = 0.3153 +/- 0.0073
#   Planck15 : Planck Collaboration 2015, A&A 594, A13:
#              H0 = 67.74 +/- 0.46, Om0 = 0.3089 +/- 0.0062
#   Planck13 : Planck Collaboration 2013, A&A 571, A16:
#              H0 = 67.77 +/- 1.30, Om0 = 0.3071 +/- 0.0085 (approx.)
#   WMAP9    : Hinshaw et al. 2013, ApJS 208, 19:
#              H0 = 69.32 +/- 0.80, Om0 = 0.2865 +/- 0.0096
#   WMAP7    : Komatsu et al. 2011, ApJS 192, 18:
#              H0 = 70.40 +/- 1.40, Om0 = 0.2720 +/- 0.0250 (approx.)
#   WMAP5    : Komatsu et al. 2009, ApJS 180, 330:
#              H0 = 70.50 +/- 1.30, Om0 = 0.2740 +/- 0.0300 (approx.)
#
# Models without a published parameter covariance here (e.g. the illustrative
# Millennium and EdS cosmologies) intentionally have no entry and fall back to
# the clearly-labelled heuristic estimate.
PARAMETER_UNCERTAINTIES: Dict[str, Dict[str, float]] = {
    "Planck18": {"H0": 0.54, "Om0": 0.0073},
    "Planck15": {"H0": 0.46, "Om0": 0.0062},
    "Planck13": {"H0": 1.30, "Om0": 0.0085},
    "WMAP9": {"H0": 0.80, "Om0": 0.0096},
    "WMAP7": {"H0": 1.40, "Om0": 0.0250},
    "WMAP5": {"H0": 1.30, "Om0": 0.0300},
}


def _compute_cosmological_uncertainty(
    z: float,
    cosmology_name: str,
    age_years: Decimal,
    cosmology: Any,
) -> Tuple[Decimal, str]:
    """Compute the 1-sigma uncertainty of the cosmic age at redshift ``z``.

    Prefers a first-order (linearized) propagation of published cosmological
    parameter uncertainties. Falls back to a clearly-labelled heuristic when no
    published parameter covariance is available for the model.

    Returns
    -------
    (uncertainty_years, method) where ``method`` is one of
    ``"parameter-covariance-propagation"`` or ``"heuristic"``.
    """
    params = PARAMETER_UNCERTAINTIES.get(cosmology_name)
    if params is not None:
        propagated = _propagate_parameter_uncertainty(z, cosmology, params)
        if propagated is not None:
            return propagated, "parameter-covariance-propagation"

    return _heuristic_cosmological_uncertainty(z, cosmology_name, age_years), "heuristic"


def _propagate_parameter_uncertainty(
    z: float,
    cosmology: Any,
    param_sigmas: Dict[str, float],
) -> Optional[Decimal]:
    """First-order propagation of parameter uncertainties to the age at ``z``.

    The cosmic age ``t(z; H0, Om0, ...)`` is differentiated with respect to each
    parameter using a central finite difference, and the contributions are
    combined in quadrature (uncorrelated-parameter approximation, i.e. diagonal
    covariance only):

        sigma_t^2 = sum_i ( dt/dp_i * sigma_p_i )^2

    Returns ``None`` if the propagation cannot be performed (e.g. astropy/numpy
    unavailable, or the cosmology cannot be cloned with new parameters), so the
    caller can fall back to the heuristic.
    """
    try:
        from astropy import units as u
        import math
    except Exception:
        return None

    def age_years_for(clone: Any) -> float:
        return float(clone.age(z).to(u.yr).value)

    variance = 0.0
    any_term = False

    for name, sigma in param_sigmas.items():
        if sigma <= 0:
            continue

        # Central value of the parameter from the cosmology object.
        try:
            if name == "H0":
                central = float(cosmology.H0.value)
            else:
                central = float(getattr(cosmology, name))
        except Exception:
            continue

        # Step for the central difference: a small fraction of the 1-sigma
        # uncertainty, which keeps the linearization valid while staying well
        # above numerical noise.
        step = max(abs(sigma) * 0.5, abs(central) * 1e-4)
        if step == 0:
            continue

        try:
            if name == "H0":
                hi = cosmology.clone(H0=(central + step) * u.km / u.s / u.Mpc)
                lo = cosmology.clone(H0=(central - step) * u.km / u.s / u.Mpc)
            else:
                hi = cosmology.clone(**{name: central + step})
                lo = cosmology.clone(**{name: central - step})
            d_age = (age_years_for(hi) - age_years_for(lo)) / (2.0 * step)
        except Exception:
            # This parameter cannot be perturbed on this cosmology; skip it.
            continue

        variance += (d_age * sigma) ** 2
        any_term = True

    if not any_term:
        return None

    return Decimal(str(math.sqrt(variance)))


def _heuristic_cosmological_uncertainty(z: float, cosmology_name: str, age_years: Decimal) -> Decimal:
    """Heuristic fallback uncertainty for models without published parameter sigmas.

    This is an explicitly non-rigorous, order-of-magnitude annotation used only
    when no published parameter covariance is available (see
    ``PARAMETER_UNCERTAINTIES``). It must not be interpreted as a strict error
    estimate. The redshift-binned percentages and per-model factors below are
    illustrative engineering placeholders, not derived quantities.
    """
    if z < 0.1:
        relative_uncertainty = Decimal('0.025')
    elif z < 1.0:
        relative_uncertainty = Decimal('0.04')
    elif z < 6.0:
        relative_uncertainty = Decimal('0.075')
    else:
        relative_uncertainty = Decimal('0.15')

    model_factors = {
        "Planck18": Decimal('1.0'),
        "Planck15": Decimal('1.1'),
        "Planck13": Decimal('1.2'),
        "WMAP9": Decimal('1.3'),
        "WMAP7": Decimal('1.4'),
        "WMAP5": Decimal('1.5'),
        "Millennium": Decimal('1.8'),
        "EdS": Decimal('2.0'),
    }

    factor = model_factors.get(cosmology_name, Decimal('1.5'))
    return abs(age_years) * relative_uncertainty * factor


def uby_to_redshift(
    uby_value: Decimal | float | str,
    *,
    cosmology_name: str = "Planck18",
    max_iterations: int = 100,
    tolerance: float = 1e-6,
) -> float:
    """
    将UBY时间转换为宇宙学红移（逆向转换）
    
    使用数值方法求解红移值
    
    Args:
        uby_value: UBY时间值
        cosmology_name: 宇宙学模型名称
        max_iterations: 最大迭代次数
        tolerance: 收敛容差
        
    Returns:
        对应的红移值
    """
    try:
        from astropy import units as u
        import numpy as np
    except Exception as exc:
        raise UBYModelError(
            "uby_to_redshift requires astropy and numpy. Install with: pip install 'uby-time[cosmology]'"
        ) from exc
    
    cosmology = _cosmology_manager.get_cosmology(cosmology_name)
    target_age = float(uby_value)
    
    # 使用二分法求解
    z_low, z_high = 0.0, 20.0
    
    for _ in range(max_iterations):
        z_mid = (z_low + z_high) / 2.0
        age_mid = cosmology.age(z_mid).to(u.yr).value
        
        if abs(age_mid - target_age) < tolerance * target_age:
            return z_mid
            
        if age_mid > target_age:
            z_low = z_mid
        else:
            z_high = z_mid
    
    raise UBYModelError(f"Failed to converge on redshift for age {target_age} years")


def compare_cosmologies(z: float, cosmology_names: list[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    比较不同宇宙学模型在给定红移下的预测
    
    Args:
        z: 红移值
        cosmology_names: 要比较的宇宙学模型列表
        
    Returns:
        包含各模型预测结果的字典
    """
    if cosmology_names is None:
        cosmology_names = ["Planck18", "Planck15", "WMAP9", "WMAP7"]
    
    results = {}
    
    for name in cosmology_names:
        try:
            uby_time = redshift_to_uby(z, cosmology_name=name)
            cosmology = _cosmology_manager.get_cosmology(name)
            
            results[name] = {
                'age_years': float(uby_time.uby_value),
                'uncertainty_years': float(uby_time.uncertainty_years) if uby_time.uncertainty_years else None,
                'H0': float(cosmology.H0.value) if hasattr(cosmology, 'H0') else None,
                'Om0': float(cosmology.Om0) if hasattr(cosmology, 'Om0') else None,
                'Ode0': float(cosmology.Ode0) if hasattr(cosmology, 'Ode0') else None,
            }
        except Exception as e:
            results[name] = {'error': str(e)}
    
    return results


def get_cosmological_parameters(cosmology_name: str) -> Dict[str, float]:
    """
    获取指定宇宙学模型的参数
    
    Args:
        cosmology_name: 宇宙学模型名称
        
    Returns:
        包含宇宙学参数的字典
    """
    cosmology = _cosmology_manager.get_cosmology(cosmology_name)
    
    params = {}
    if hasattr(cosmology, 'H0'):
        params['H0'] = float(cosmology.H0.value)
    if hasattr(cosmology, 'Om0'):
        params['Om0'] = float(cosmology.Om0)
    if hasattr(cosmology, 'Ode0'):
        params['Ode0'] = float(cosmology.Ode0)
    if hasattr(cosmology, 'Ok0'):
        params['Ok0'] = float(cosmology.Ok0)
    if hasattr(cosmology, 'Tcmb0'):
        params['Tcmb0'] = float(cosmology.Tcmb0.value)
    if hasattr(cosmology, 'Neff'):
        params['Neff'] = float(cosmology.Neff)
    if hasattr(cosmology, 'm_nu'):
        params['m_nu'] = [float(m.value) for m in cosmology.m_nu]
        
    return params
