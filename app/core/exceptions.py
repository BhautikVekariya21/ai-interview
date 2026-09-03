"""
Custom exception hierarchy for the resume parser.
Provides granular error handling across the pipeline.
"""


class ResumeParserBaseException(Exception):
    """Base exception for all resume parser errors."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class FileExtractionError(ResumeParserBaseException):
    """Raised when file content extraction fails."""
    pass


class UnsupportedFileFormatError(ResumeParserBaseException):
    """Raised when an unsupported file format is uploaded."""
    pass


class FileSizeLimitError(ResumeParserBaseException):
    """Raised when file exceeds maximum allowed size."""
    pass


class TextPreprocessingError(ResumeParserBaseException):
    """Raised when text preprocessing/cleaning fails."""
    pass


class NERModelError(ResumeParserBaseException):
    """Raised when NER model inference fails."""
    pass


class NERModelNotFoundError(ResumeParserBaseException):
    """Raised when the trained NER model cannot be loaded."""
    pass


class SectionDetectionError(ResumeParserBaseException):
    """Raised when section detection logic fails."""
    pass


class EntityExtractionError(ResumeParserBaseException):
    """Raised when entity extraction produces invalid results."""
    pass


class SchemaValidationError(ResumeParserBaseException):
    """Raised when extracted data fails Pydantic validation."""
    pass


class EmptyResumeError(ResumeParserBaseException):
    """Raised when uploaded resume contains no extractable text."""
    pass