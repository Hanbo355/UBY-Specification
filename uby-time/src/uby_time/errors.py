class UBYError(Exception):
    """Base exception for uby-time."""


class UBYParseError(UBYError):
    """Raised when a UBY expression cannot be parsed."""


class UBYValidationError(UBYError):
    """Raised when a UBY object violates normative constraints."""


class UBYPrecisionError(UBYError):
    """Raised when a precision-level rule is violated."""


class UBYModelError(UBYError):
    """Raised when a cosmology/model dependency is unavailable or invalid."""


class UBYAnchorError(UBYError):
    """Raised when an anchor is invalid or incompatible."""
