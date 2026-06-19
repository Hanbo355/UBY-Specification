"""
Tests for matplotlib extension functionality.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch

# Check if matplotlib is available
try:
    import matplotlib
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Test imports
def test_matplotlib_imports():
    """Test that matplotlib extension can be imported."""
    try:
        from uby_time.matplotlib_ext import UBYFormatter, UBYLocator, setup_uby_axis
        assert True
    except ImportError as e:
        pytest.skip(f"Matplotlib not available: {e}")


@pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="Matplotlib not available")
def test_uby_formatter():
    """Test UBY formatter for matplotlib."""
    from uby_time.matplotlib_ext import UBYFormatter
    
    formatter = UBYFormatter()
    
    # Test different scales
    assert "UBY 13.79G" in formatter(13787002026.0)  # Current time
    assert "UBY 380.0K" in formatter(380000.0)       # CMB decoupling
    assert "UBY 1" in formatter(1.0)                 # Early universe (no decimal for integers)
    
    # Test edge cases
    assert formatter(float('nan')) == ""
    assert formatter(float('inf')) == ""


@pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="Matplotlib not available")
def test_uby_locator():
    """Test UBY locator for matplotlib."""
    from uby_time.matplotlib_ext import UBYLocator
    
    locator = UBYLocator(max_ticks=5)
    
    # Test tick generation
    ticks = locator.tick_values(13787000000, 13787010000)
    assert len(ticks) <= 5
    assert all(13787000000 <= tick <= 13787010000 for tick in ticks)


@pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="Matplotlib not available")
def test_setup_uby_axis():
    """Test axis setup function."""
    from uby_time.matplotlib_ext import setup_uby_axis
    
    # Mock matplotlib axis
    mock_ax = Mock()
    mock_ax.xaxis = Mock()
    
    formatter, locator = setup_uby_axis(mock_ax)
    
    # Verify formatter and locator were set
    mock_ax.xaxis.set_major_formatter.assert_called_once()
    mock_ax.xaxis.set_major_locator.assert_called_once()


@pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="Matplotlib not available")
def test_plot_timeline():
    """Test timeline plotting function."""
    from uby_time.matplotlib_ext import plot_timeline
    
    events = [
        {'uby': 13787002026, 'name': 'Present Day', 'color': 'red'},
        {'uby': 13787001969, 'name': 'Moon Landing', 'color': 'blue'},
        {'uby': 380000, 'name': 'CMB Decoupling', 'color': 'orange'}
    ]
    
    # Mock matplotlib
    with patch('matplotlib.pyplot.subplots') as mock_subplots:
        mock_fig, mock_ax = Mock(), Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)
        mock_ax.scatter.return_value = Mock()
        
        # Mock the spines dictionary
        mock_ax.spines = {
            'left': Mock(),
            'right': Mock(), 
            'top': Mock()
        }
        
        # Mock xaxis for setup_uby_axis
        mock_ax.xaxis = Mock()
        
        ax = plot_timeline(events)
        
        # Verify plot was created
        mock_ax.scatter.assert_called_once()
        assert len(mock_ax.annotate.call_args_list) == len(events)


def test_conversion_functions():
    """Test JD/UBY conversion functions for matplotlib."""
    try:
        from uby_time.matplotlib_ext import jd_to_uby_axis, uby_to_jd_axis
    except ImportError:
        pytest.skip("Matplotlib not available")
    
    # Test single value conversion
    jd = 2461041.5  # 2026-01-01
    uby = jd_to_uby_axis(jd)
    assert isinstance(uby, float)
    assert uby > 13787000000
    
    # Test round-trip conversion
    jd_back = uby_to_jd_axis(uby)
    assert abs(jd_back - jd) < 0.1  # Within reasonable tolerance
    
    # Test array conversion
    jd_array = np.array([2461041.5, 2461042.5])
    uby_array = jd_to_uby_axis(jd_array)
    assert isinstance(uby_array, np.ndarray)
    assert len(uby_array) == 2
