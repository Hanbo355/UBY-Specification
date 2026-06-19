"""
UBY time formatting support for Plotly.

This module provides custom formatters and utilities for displaying UBY time
values in Plotly charts with appropriate scale-dependent formatting.
"""

import numpy as np
from typing import Optional, Union, List, Dict, Any
from .core import UBYTime
from .conversion import jd_to_uby, uby_to_jd


class UBYTickFormatter:
    """
    Custom tick formatter for UBY time values in Plotly charts.
    
    Automatically selects appropriate format based on the time scale.
    """
    
    def __init__(self, model_version: str = "LCDM-Planck2018", 
                 spec_version: str = "0.1.0"):
        """
        Initialize UBY formatter.
        
        Parameters
        ----------
        model_version : str
            Cosmological model version for UBY calculations
        spec_version : str
            UBY specification version
        """
        self.model_version = model_version
        self.spec_version = spec_version
    
    def format_tick(self, value: float) -> str:
        """Format single UBY value for display."""
        if np.isnan(value) or np.isinf(value):
            return ""
            
        # Cosmic scale (>1G years): Use G units
        if value >= 1e9:
            return f"UBY {value/1e9:.2f}G"
        # Geological scale (1M-1G years): Use M units  
        elif value >= 1e6:
            return f"UBY {value/1e6:.1f}M"
        # Historical scale: Try mnemonic format
        elif value >= 13786000000:  # Within Level 1 range
            try:
                uby_time = UBYTime(value, model_version=self.model_version)
                return uby_time.format_mnemonic_academic()
            except:
                return f"UBY {value:.0f}"
        # Early universe: K units or direct
        else:
            if value >= 1000:
                return f"UBY {value/1000:.1f}K"
            else:
                return f"UBY {value:.0f}"
    
    def generate_tickvals_and_text(self, vmin: float, vmax: float, 
                                   max_ticks: int = 8) -> tuple:
        """
        Generate tick values and corresponding text labels.
        
        Parameters
        ----------
        vmin, vmax : float
            Range of values to generate ticks for
        max_ticks : int
            Maximum number of ticks to generate
            
        Returns
        -------
        tickvals : list
            Numeric tick positions
        ticktext : list
            Formatted tick labels
        """
        if vmax <= vmin:
            return [], []
            
        span = vmax - vmin
        
        # Determine appropriate tick spacing based on scale
        if span >= 1e10:  # >10G years
            step = self._round_to_nice(span / max_ticks, [1e9, 5e8, 2e8, 1e8])
        elif span >= 1e9:  # 1-10G years
            step = self._round_to_nice(span / max_ticks, [5e8, 2e8, 1e8, 5e7])
        elif span >= 1e6:  # 1M-1G years
            step = self._round_to_nice(span / max_ticks, [1e8, 5e7, 1e7, 5e6, 1e6])
        elif span >= 1000:  # 1K-1M years
            step = self._round_to_nice(span / max_ticks, [1e5, 5e4, 1e4, 5e3, 1e3])
        else:  # <1K years
            step = self._round_to_nice(span / max_ticks, [500, 200, 100, 50, 20, 10, 5, 1])
        
        # Generate ticks
        start = np.ceil(vmin / step) * step
        end = np.floor(vmax / step) * step
        tickvals = list(np.arange(start, end + step/2, step))
        tickvals = [t for t in tickvals if t >= vmin and t <= vmax]
        
        # Generate labels
        ticktext = [self.format_tick(val) for val in tickvals]
        
        return tickvals, ticktext
    
    def _round_to_nice(self, value: float, candidates: List[float]) -> float:
        """Round value to nearest 'nice' number from candidates."""
        for candidate in candidates:
            if value >= candidate:
                return candidate
        return candidates[-1]


def setup_uby_xaxis(fig, model_version: str = "LCDM-Planck2018", 
                    spec_version: str = "0.1.0", **kwargs) -> Dict[str, Any]:
    """
    Configure Plotly figure x-axis for UBY time display.
    
    Parameters
    ----------
    fig : plotly.graph_objects.Figure
        Figure to configure
    model_version : str
        Cosmological model version
    spec_version : str
        UBY specification version
    **kwargs
        Additional axis configuration options
        
    Returns
    -------
    xaxis_config : dict
        The axis configuration applied
    """
    formatter = UBYTickFormatter(model_version=model_version, spec_version=spec_version)
    
    # Get current x-axis range
    if fig.data:
        x_values = []
        for trace in fig.data:
            if hasattr(trace, 'x') and trace.x is not None:
                x_values.extend(trace.x)
        
        if x_values:
            vmin, vmax = min(x_values), max(x_values)
            tickvals, ticktext = formatter.generate_tickvals_and_text(vmin, vmax)
        else:
            tickvals, ticktext = [], []
    else:
        tickvals, ticktext = [], []
    
    xaxis_config = {
        'title': kwargs.get('title', 'UBY Time'),
        'tickvals': tickvals,
        'ticktext': ticktext,
        'showgrid': kwargs.get('showgrid', True),
        'gridcolor': kwargs.get('gridcolor', 'lightgray'),
        'gridwidth': kwargs.get('gridwidth', 1),
        **{k: v for k, v in kwargs.items() if k not in ['title', 'showgrid', 'gridcolor', 'gridwidth']}
    }
    
    fig.update_xaxes(**xaxis_config)
    return xaxis_config


def setup_uby_yaxis(fig, model_version: str = "LCDM-Planck2018", 
                    spec_version: str = "0.1.0", **kwargs) -> Dict[str, Any]:
    """
    Configure Plotly figure y-axis for UBY time display.
    
    Parameters
    ----------
    fig : plotly.graph_objects.Figure
        Figure to configure
    model_version : str
        Cosmological model version
    spec_version : str
        UBY specification version
    **kwargs
        Additional axis configuration options
        
    Returns
    -------
    yaxis_config : dict
        The axis configuration applied
    """
    formatter = UBYTickFormatter(model_version=model_version, spec_version=spec_version)
    
    # Get current y-axis range
    if fig.data:
        y_values = []
        for trace in fig.data:
            if hasattr(trace, 'y') and trace.y is not None:
                y_values.extend(trace.y)
        
        if y_values:
            vmin, vmax = min(y_values), max(y_values)
            tickvals, ticktext = formatter.generate_tickvals_and_text(vmin, vmax)
        else:
            tickvals, ticktext = [], []
    else:
        tickvals, ticktext = [], []
    
    yaxis_config = {
        'title': kwargs.get('title', 'UBY Time'),
        'tickvals': tickvals,
        'ticktext': ticktext,
        'showgrid': kwargs.get('showgrid', True),
        'gridcolor': kwargs.get('gridcolor', 'lightgray'),
        'gridwidth': kwargs.get('gridwidth', 1),
        **{k: v for k, v in kwargs.items() if k not in ['title', 'showgrid', 'gridcolor', 'gridwidth']}
    }
    
    fig.update_yaxes(**yaxis_config)
    return yaxis_config


def create_uby_timeline(events: List[Dict[str, Any]], 
                        model_version: str = "LCDM-Planck2018",
                        **kwargs):
    """
    Create an interactive timeline plot with UBY formatting using Plotly.
    
    Parameters
    ----------
    events : list of dict
        List of events, each dict should contain 'uby', 'name', and optionally 
        'color', 'size', 'description'
    model_version : str
        Cosmological model version
    **kwargs
        Additional arguments for plot styling
        
    Returns
    -------
    fig : plotly.graph_objects.Figure
        Interactive timeline figure
        
    Examples
    --------
    >>> events = [
    ...     {'uby': 13787002026, 'name': 'Present Day', 'color': 'red'},
    ...     {'uby': 13787001969, 'name': 'Moon Landing', 'color': 'blue'},
    ...     {'uby': 380000, 'name': 'CMB Decoupling', 'color': 'orange'}
    ... ]
    >>> fig = create_uby_timeline(events)
    >>> fig.show()
    """
    try:
        import plotly.graph_objects as go
        import plotly.express as px
    except ImportError:
        raise ImportError("Plotly is required for this functionality. Install with: pip install plotly")
    
    # Extract data
    uby_values = [event['uby'] for event in events]
    names = [event['name'] for event in events]
    colors = [event.get('color', 'blue') for event in events]
    sizes = [event.get('size', 10) for event in events]
    descriptions = [event.get('description', event['name']) for event in events]
    
    # Create figure
    fig = go.Figure()
    
    # Add scatter trace
    fig.add_trace(go.Scatter(
        x=uby_values,
        y=[0] * len(uby_values),
        mode='markers+text',
        marker=dict(
            size=sizes,
            color=colors,
            line=dict(width=2, color='white')
        ),
        text=names,
        textposition="top center",
        hovertemplate='<b>%{text}</b><br>' +
                     'UBY: %{x}<br>' +
                     '<extra></extra>',
        name='Events'
    ))
    
    # Setup UBY formatting
    setup_uby_xaxis(fig, model_version=model_version)
    
    # Layout configuration
    fig.update_layout(
        title=kwargs.get('title', 'Timeline with UBY Formatting'),
        showlegend=False,
        height=kwargs.get('height', 400),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[-0.5, 0.5]
        ),
        hovermode='closest',
        plot_bgcolor='white'
    )
    
    return fig


def create_uby_scatter(x_data: List[float], y_data: List[float],
                       x_is_uby: bool = True, y_is_uby: bool = False,
                       model_version: str = "LCDM-Planck2018",
                       **kwargs):
    """
    Create a scatter plot with UBY formatting on specified axes.
    
    Parameters
    ----------
    x_data, y_data : list
        Data for x and y axes
    x_is_uby, y_is_uby : bool
        Whether each axis contains UBY values
    model_version : str
        Cosmological model version
    **kwargs
        Additional arguments for plot styling
        
    Returns
    -------
    fig : plotly.graph_objects.Figure
        Scatter plot figure with UBY formatting
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        raise ImportError("Plotly is required for this functionality. Install with: pip install plotly")
    
    fig = go.Figure()
    
    # Add scatter trace
    fig.add_trace(go.Scatter(
        x=x_data,
        y=y_data,
        mode=kwargs.get('mode', 'markers'),
        marker=kwargs.get('marker', {}),
        name=kwargs.get('name', 'Data')
    ))
    
    # Setup UBY formatting for appropriate axes
    if x_is_uby:
        setup_uby_xaxis(fig, model_version=model_version, 
                       title=kwargs.get('x_title', 'UBY Time'))
    
    if y_is_uby:
        setup_uby_yaxis(fig, model_version=model_version,
                       title=kwargs.get('y_title', 'UBY Time'))
    
    # Layout configuration
    fig.update_layout(
        title=kwargs.get('title', 'UBY Scatter Plot'),
        showlegend=kwargs.get('showlegend', True),
        height=kwargs.get('height', 500),
        plot_bgcolor='white'
    )
    
    return fig


def add_uby_hover_info(fig, uby_values: List[float], 
                       model_version: str = "LCDM-Planck2018"):
    """
    Add UBY-formatted hover information to existing Plotly traces.
    
    Parameters
    ----------
    fig : plotly.graph_objects.Figure
        Figure to modify
    uby_values : list
        UBY values corresponding to data points
    model_version : str
        Cosmological model version
        
    Returns
    -------
    fig : plotly.graph_objects.Figure
        Modified figure with UBY hover info
    """
    formatter = UBYTickFormatter(model_version=model_version)
    
    # Format UBY values for hover
    uby_formatted = [formatter.format_tick(val) for val in uby_values]
    
    # Update hover template for all traces
    for i, trace in enumerate(fig.data):
        if hasattr(trace, 'hovertemplate'):
            # Add UBY info to existing hover template
            current_template = trace.hovertemplate or ''
            new_template = current_template + '<br>UBY: ' + uby_formatted[i] + '<extra></extra>'
            fig.data[i].hovertemplate = new_template
    
    return fig


# Utility functions for data conversion
def jd_to_uby_plotly(jd_values: Union[float, List[float]], 
                     model_version: str = "LCDM-Planck2018") -> Union[float, List[float]]:
    """
    Convert Julian Day values to UBY for Plotly plotting.
    
    Parameters
    ----------
    jd_values : float or list
        Julian Day values to convert
    model_version : str
        Cosmological model version
        
    Returns
    -------
    uby_values : float or list
        Corresponding UBY values
    """
    if isinstance(jd_values, (int, float)):
        return jd_to_uby(jd_values, model_version=model_version)
    else:
        return [jd_to_uby(jd, model_version=model_version) for jd in jd_values]


def uby_to_jd_plotly(uby_values: Union[float, List[float]], 
                     model_version: str = "LCDM-Planck2018") -> Union[float, List[float]]:
    """
    Convert UBY values to Julian Day for Plotly plotting.
    
    Parameters
    ----------
    uby_values : float or list
        UBY values to convert
    model_version : str
        Cosmological model version
        
    Returns
    -------
    jd_values : float or list
        Corresponding Julian Day values
    """
    if isinstance(uby_values, (int, float)):
        return uby_to_jd(uby_values, model_version=model_version)
    else:
        return [uby_to_jd(uby, model_version=model_version) for uby in uby_values]
