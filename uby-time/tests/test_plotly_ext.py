"""
Tests for plotly extension functionality.
"""

import pytest
from unittest.mock import Mock, patch

# Test imports
def test_plotly_imports():
    """Test that plotly extension can be imported."""
    try:
        from uby_time.plotly_ext import UBYTickFormatter, setup_uby_xaxis, create_uby_timeline
        assert True
    except ImportError as e:
        pytest.skip(f"Plotly not available: {e}")


def test_uby_tick_formatter():
    """Test UBY tick formatter for plotly."""
    from uby_time.plotly_ext import UBYTickFormatter
    
    formatter = UBYTickFormatter()
    
    # Test different scales
    assert "UBY 13.79G" in formatter.format_tick(13787002026.0)  # Current time
    assert "UBY 380.0K" in formatter.format_tick(380000.0)       # CMB decoupling
    assert "UBY 1" in formatter.format_tick(1.0)                 # Early universe
    
    # Test edge cases
    assert formatter.format_tick(float('nan')) == ""
    assert formatter.format_tick(float('inf')) == ""


def test_tick_generation():
    """Test tick value and text generation."""
    from uby_time.plotly_ext import UBYTickFormatter
    
    formatter = UBYTickFormatter()
    
    # Test tick generation for different scales
    tickvals, ticktext = formatter.generate_tickvals_and_text(13787000000, 13787010000)
    assert len(tickvals) == len(ticktext)
    assert all(isinstance(val, (int, float)) for val in tickvals)
    assert all(isinstance(text, str) for text in ticktext)
    
    # Test empty range
    tickvals, ticktext = formatter.generate_tickvals_and_text(100, 100)
    assert tickvals == []
    assert ticktext == []


def test_setup_uby_xaxis():
    """Test x-axis setup function."""
    from uby_time.plotly_ext import setup_uby_xaxis
    
    # Mock plotly figure
    mock_fig = Mock()
    mock_fig.data = []
    mock_fig.update_xaxes = Mock()
    
    config = setup_uby_xaxis(mock_fig)
    
    # Verify axis was configured
    mock_fig.update_xaxes.assert_called_once()
    assert 'title' in config
    assert config['title'] == 'UBY Time'


def test_setup_uby_yaxis():
    """Test y-axis setup function."""
    from uby_time.plotly_ext import setup_uby_yaxis
    
    # Mock plotly figure
    mock_fig = Mock()
    mock_fig.data = []
    mock_fig.update_yaxes = Mock()
    
    config = setup_uby_yaxis(mock_fig)
    
    # Verify axis was configured
    mock_fig.update_yaxes.assert_called_once()
    assert 'title' in config
    assert config['title'] == 'UBY Time'


def test_create_uby_timeline():
    """Test timeline creation function."""
    from uby_time.plotly_ext import create_uby_timeline
    
    events = [
        {'uby': 13787002026, 'name': 'Present Day', 'color': 'red'},
        {'uby': 13787001969, 'name': 'Moon Landing', 'color': 'blue'},
        {'uby': 380000, 'name': 'CMB Decoupling', 'color': 'orange'}
    ]
    
    # Mock plotly
    with patch('plotly.graph_objects.Figure') as mock_figure_class:
        mock_fig = Mock()
        mock_figure_class.return_value = mock_fig
        mock_fig.data = []
        mock_fig.add_trace = Mock()
        mock_fig.update_xaxes = Mock()
        mock_fig.update_layout = Mock()
        
        with patch('plotly.graph_objects.Scatter') as mock_scatter:
            fig = create_uby_timeline(events)
            
            # Verify timeline was created
            mock_fig.add_trace.assert_called_once()
            mock_fig.update_layout.assert_called_once()


def test_create_uby_scatter():
    """Test scatter plot creation function."""
    from uby_time.plotly_ext import create_uby_scatter
    
    x_data = [13787002026, 13787001969, 380000]
    y_data = [1, 2, 3]
    
    # Mock plotly
    with patch('plotly.graph_objects.Figure') as mock_figure_class:
        mock_fig = Mock()
        mock_figure_class.return_value = mock_fig
        mock_fig.data = []
        mock_fig.add_trace = Mock()
        mock_fig.update_xaxes = Mock()
        mock_fig.update_layout = Mock()
        
        with patch('plotly.graph_objects.Scatter') as mock_scatter:
            fig = create_uby_scatter(x_data, y_data, x_is_uby=True)
            
            # Verify scatter plot was created
            mock_fig.add_trace.assert_called_once()
            mock_fig.update_layout.assert_called_once()


def test_conversion_functions():
    """Test JD/UBY conversion functions for plotly."""
    try:
        from uby_time.plotly_ext import jd_to_uby_plotly, uby_to_jd_plotly
    except ImportError:
        pytest.skip("Plotly not available")
    
    # Test single value conversion
    jd = 2461041.5  # 2026-01-01
    uby = jd_to_uby_plotly(jd)
    assert isinstance(uby, float)
    assert uby > 13787000000
    
    # Test round-trip conversion
    jd_back = uby_to_jd_plotly(uby)
    assert abs(jd_back - jd) < 0.1  # Within reasonable tolerance
    
    # Test list conversion
    jd_list = [2461041.5, 2461042.5]
    uby_list = jd_to_uby_plotly(jd_list)
    assert isinstance(uby_list, list)
    assert len(uby_list) == 2


def test_add_uby_hover_info():
    """Test adding UBY hover information."""
    from uby_time.plotly_ext import add_uby_hover_info
    
    # Mock figure with traces
    mock_trace = Mock()
    mock_trace.hovertemplate = "Original template"
    
    mock_fig = Mock()
    mock_fig.data = [mock_trace]
    
    uby_values = [13787002026, 13787001969]
    
    result_fig = add_uby_hover_info(mock_fig, uby_values)
    
    # Verify hover info was added
    assert result_fig == mock_fig
    # Note: Detailed verification would require checking the modified hovertemplate
