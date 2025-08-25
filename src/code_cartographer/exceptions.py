class CodeCartographerError(Exception):
    """Base exception for all errors raised by the application."""
    pass

class SourceNotFoundError(CodeCartographerError):
    """Raised when a specified source code path does not exist or is invalid."""
    pass

class ModelConstructionError(CodeCartographerError):
    """Raised for general errors during the model building process."""
    pass

class ModelStateError(CodeCartographerError):
    """Raised when an operation is attempted on the Metamodel in an invalid state,
    e.g., querying before a project has been loaded."""
    pass

class RenderingError(CodeCartographerError):
    """Raised for errors that occur during the presentation/rendering process."""
    pass