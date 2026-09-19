"""parch: fixed e-ink PDF pages."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("parch")
except PackageNotFoundError:
    __version__ = "unknown"


class Error(Exception):
    """Base package error."""


class ConfigError(Error):
    """Invalid or incomplete press spec."""


class TemplateError(Error):
    """External template tool is missing or failed."""
