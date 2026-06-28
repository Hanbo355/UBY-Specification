"""
UBY time formatting support for Matplotlib.

This module provides custom formatters and locators for displaying UBY time
values on matplotlib axes with appropriate scale-dependent formatting.
"""

import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import numpy as np
from typing import Optional, Union, List
from .models import UBYTime
from .conversion import jd_to_uby, uby_to_jd
from .formatting import format_full, format_academic_mnemonic


class UBYFormatter(ticker.Formatter):
    """
    Custom formatter for UBY time values on matplotlib axes.
    
    Automatically selects appropriate format based on the time scale:
    - Cosmic scale (>1G years): Scientific notation or G/M units
    - Geological scale (1M-1G years): M units
    - Historical scale (<1M years): Mnemonic format when possible
    """
    
    def __init__(self, model_version: str = "LCDM-Planck2018", 
                 spec_version: str = "0.1.0",
                 auto_format: bool = True):
        """
        Initialize UBY formatter.
        
        Parameters
        ----------
        model_version : str
            Cosmological model version for UBY calculations
        spec_version : str
            UBY specification version
        auto_format : bool
            If True, automatically select format based on scale
        """
        self.model_version = model_version
        self.spec_version = spec_version
        self.auto_format = auto_format
        
    def __call__(self, x: float, pos: Optional[int] = None) -> str:
        """Format UBY value for display."""
        if np.isnan(x) or np.isinf(x):
            return ""
        
        # For formatting, we can work directly with the UBY value
        if self.auto_format:
            return self._auto_format_value(x)
        else:
            # Create a proper UBYTime object for full formatting.
            # UBYTime is a frozen dataclass, so use dataclasses.replace to set
            # the value instead of mutating the instance in place.
            from dataclasses import replace
            from decimal import Decimal
            from .conversion import jd_to_uby
            from .anchors import DEFAULT_ANCHOR

            base = jd_to_uby(DEFAULT_ANCHOR.anchor_jd, model_version=self.model_version)
            uby_time = replace(base, uby_value=Decimal(str(x)))
            return format_full(uby_time)
    
    def _auto_format_value(self, value: float) -> str:
        """Automatically select appropriate format based on scale."""
        # Cosmic scale (>1G years): Use G units
        if value >= 1e9:
            return f"UBY {value/1e9:.2f}G"
        # Geological scale (1M-1G years): Use M units
        elif value >= 1e6:
            return f"UBY {value/1e6:.1f}M"
        # Thousand-year scale: Use K units
        elif value >= 1000:
            return f"UBY {value/1000:.1f}K"
        # Sub-thousand-year scale: plain integer
        else:
            return f"UBY {value:.0f}"

    def _auto_format(self, uby_time: UBYTime) -> str:
        """Automatically select appropriate format based on scale.

        Convenience wrapper that delegates to ``_auto_format_value`` so the
        scale thresholds are defined in a single place.
        """
        return self._auto_format_value(float(uby_time.uby_value))


class UBYLocator(ticker.Locator):
    """
    Custom locator for UBY time values on matplotlib axes.
    
    Provides intelligent tick placement based on the time scale.
    """
    
    def __init__(self, max_ticks: int = 8):
        """
        Initialize UBY locator.
        
        Parameters
        ----------
        max_ticks : int
            Maximum number of ticks to generate
        """
        self.max_ticks = max_ticks
    
    def __call__(self):
        """Return tick locations for current axis limits."""
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin, vmax)
    
    def tick_values(self, vmin: float, vmax: float) -> np.ndarray:
        """Generate tick values for given range."""
        if vmax <= vmin:
            return np.array([])
            
        span = vmax - vmin
        
        # Determine appropriate tick spacing based on scale
        if span >= 1e10:  # >10G years
            step = self._round_to_nice(span / self.max_ticks, [1e9, 5e8, 2e8, 1e8])
        elif span >= 1e9:  # 1-10G years
            step = self._round_to_nice(span / self.max_ticks, [5e8, 2e8, 1e8, 5e7])
        elif span >= 1e6:  # 1M-1G years
            step = self._round_to_nice(span / self.max_ticks, [1e8, 5e7, 1e7, 5e6, 1e6])
        elif span >= 1000:  # 1K-1M years
            step = self._round_to_nice(span / self.max_ticks, [1e5, 5e4, 1e4, 5e3, 1e3])
        else:  # <1K years
            step = self._round_to_nice(span / self.max_ticks, [500, 200, 100, 50, 20, 10, 5, 1])
        
        # Generate ticks
        start = np.ceil(vmin / step) * step
        end = np.floor(vmax / step) * step
        ticks = np.arange(start, end + step/2, step)
        
        # Filter ticks within range and limit count
        valid_ticks = ticks[(ticks >= vmin) & (ticks <= vmax)]
        
        # Ensure we don't exceed max_ticks
        if len(valid_ticks) > self.max_ticks:
            # Take evenly spaced subset
            indices = np.linspace(0, len(valid_ticks)-1, self.max_ticks, dtype=int)
            valid_ticks = valid_ticks[indices]
        
        return valid_ticks
    
    def _round_to_nice(self, value: float, candidates: List[float]) -> float:
        """Round value to nearest 'nice' number from candidates."""
        for candidate in candidates:
            if value >= candidate:
                return candidate
        return candidates[-1]


def setup_uby_axis(ax, model_version: str = "LCDM-Planck2018", 
                   spec_version: str = "0.1.0"):
    """
    Configure matplotlib axis for UBY time display.
    
    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axis to configure
    model_version : str
        Cosmological model version
    spec_version : str
        UBY specification version
        
    Returns
    -------
    formatter : UBYFormatter
        The formatter applied to the axis
    locator : UBYLocator
        The locator applied to the axis
    """
    formatter = UBYFormatter(model_version=model_version, spec_version=spec_version)
    locator = UBYLocator()
    
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(locator)
    
    return formatter, locator


def jd_to_uby_axis(jd_values: Union[float, np.ndarray], 
                   model_version: str = "LCDM-Planck2018") -> Union[float, np.ndarray]:
    """
    Convert Julian Day values to UBY for matplotlib plotting.
    
    Parameters
    ----------
    jd_values : float or array-like
        Julian Day values to convert
    model_version : str
        Cosmological model version
        
    Returns
    -------
    uby_values : float or array-like
        Corresponding UBY values
    """
    if np.isscalar(jd_values):
        uby_time = jd_to_uby(jd_values, model_version=model_version)
        return float(uby_time.uby_value)
    else:
        return np.array([float(jd_to_uby(jd, model_version=model_version).uby_value) for jd in jd_values])


def uby_to_jd_axis(uby_values: Union[float, np.ndarray], 
                   model_version: str = "LCDM-Planck2018") -> Union[float, np.ndarray]:
    """
    Convert UBY values to Julian Day for matplotlib plotting.
    
    Parameters
    ----------
    uby_values : float or array-like
        UBY values to convert
    model_version : str
        Cosmological model version (currently not used, for API consistency)
        
    Returns
    -------
    jd_values : float or array-like
        Corresponding Julian Day values
    """
    if np.isscalar(uby_values):
        jd = uby_to_jd(uby_values)
        return float(jd)
    else:
        return np.array([float(uby_to_jd(uby)) for uby in uby_values])


# Convenience function for quick plotting
def plot_timeline(events: List[dict], ax=None, **kwargs):
    """
    Create a timeline plot with UBY formatting.
    
    Parameters
    ----------
    events : list of dict
        List of events, each dict should contain 'uby', 'name', and optionally 'color'
    ax : matplotlib.axes.Axes, optional
        Axis to plot on. If None, creates new figure
    **kwargs
        Additional arguments passed to scatter plot
        
    Returns
    -------
    ax : matplotlib.axes.Axes
        The axis with the timeline plot
        
    Examples
    --------
    >>> events = [
    ...     {'uby': 13787002026, 'name': 'Present Day', 'color': 'red'},
    ...     {'uby': 13787001969, 'name': 'Moon Landing', 'color': 'blue'},
    ...     {'uby': 380000, 'name': 'CMB Decoupling', 'color': 'orange'}
    ... ]
    >>> ax = plot_timeline(events)
    """
    import matplotlib.pyplot as plt
    
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 6))
    
    # Extract data
    uby_values = [event['uby'] for event in events]
    names = [event['name'] for event in events]
    colors = [event.get('color', 'blue') for event in events]
    
    # Create scatter plot
    y_pos = np.zeros(len(uby_values))
    scatter = ax.scatter(uby_values, y_pos, c=colors, s=100, **kwargs)
    
    # Add labels
    for i, (uby, name) in enumerate(zip(uby_values, names)):
        ax.annotate(name, (uby, 0), xytext=(0, 20), 
                   textcoords='offset points', ha='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # Setup UBY formatting
    setup_uby_axis(ax)
    
    # Styling
    ax.set_ylim(-0.5, 0.5)
    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('UBY Time')
    ax.set_title('Timeline with UBY Formatting')
    
    return ax
