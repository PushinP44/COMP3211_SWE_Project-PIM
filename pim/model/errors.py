class PimError(Exception):
    """Base class for all PIM domain errors."""


class ValidationError(PimError):
    """Raised when a PIR's field values fail validation."""


class PIRNotFoundError(PimError):
    """Raised when an operation references an id that doesn't exist."""


class ParseError(PimError):
    """Raised when a search-criterion expression can't be parsed."""


class StorageError(PimError):
    """Raised when a .pim file can't be saved or loaded."""
