"""
API Wrapper for Amcrest V3.26

https://support.amcrest.com/hc/en-us/articles/17903073032973-Amcrest-HTTP-API-SDK
"""

from importlib import metadata as importlib_metadata


def get_version() -> str:
    """Version."""
    try:
        return importlib_metadata.version(__name__)
    except importlib_metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


version: str = get_version()
