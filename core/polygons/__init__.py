# core/polygons/__init__.py
"""
Polygon management module for geographic zone handling.

Provides polygon loading, caching, and point-in-polygon evaluation.
"""
from .polygon_registry import (
    PolygonRegistry,
    PolygonLoadError,
    PolygonValidationError,
    get_polygon_registry,
    reset_polygon_registry,
    load_all_cities,
)

__all__ = [
    "PolygonRegistry",
    "PolygonLoadError",
    "PolygonValidationError",
    "get_polygon_registry",
    "reset_polygon_registry",
    "load_all_cities",
    "get_polygon_manager",
    "reload_polygon_manager",
]


def get_polygon_manager() -> PolygonRegistry:
    """Backward-compatible alias for loading all city polygons into the registry."""
    return load_all_cities()


def reload_polygon_manager() -> PolygonRegistry:
    """Reset and reload all city polygons into the shared registry."""
    reset_polygon_registry()
    return load_all_cities()
