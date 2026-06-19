from __future__ import annotations

from typing import Any

from .conversion import iso_to_uby, jd_to_uby
from .formatting import format_full, format_magnitude


def register_pandas_accessors() -> bool:
    """Register lightweight pandas Series accessor `.uby` if pandas is installed.

    Returns True when registration succeeds. Returns False when pandas is not installed.
    """
    try:
        import pandas as pd
    except Exception:
        return False

    @pd.api.extensions.register_series_accessor("uby")
    class UBYSeriesAccessor:
        def __init__(self, pandas_obj):
            self._obj = pandas_obj

        def from_iso(self, *, errors: str = "raise", **kwargs: Any):
            return self._map(lambda value: iso_to_uby(str(value), **kwargs), errors=errors)

        def from_jd(self, *, errors: str = "raise", **kwargs: Any):
            return self._map(lambda value: jd_to_uby(str(value), **kwargs), errors=errors)

        def format_full(self, *, errors: str = "raise", **kwargs: Any):
            return self._map(lambda value: format_full(value, **kwargs), errors=errors)

        def format_magnitude(self, *, errors: str = "raise", **kwargs: Any):
            return self._map(lambda value: format_magnitude(value, **kwargs), errors=errors)

        def _map(self, func, *, errors: str):
            if errors not in {"raise", "coerce", "ignore"}:
                raise ValueError("errors must be 'raise', 'coerce', or 'ignore'")

            def apply_one(value):
                try:
                    return func(value)
                except Exception:
                    if errors == "raise":
                        raise
                    if errors == "coerce":
                        return None
                    return value

            return self._obj.map(apply_one)

    return True


__all__ = ["register_pandas_accessors"]
