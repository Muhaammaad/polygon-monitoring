# core/polygons/__init__.py
"""
Polygon management module for geographic zone handling.

Provides polygon loading, caching, and point-in-polygon evaluation.
"""
import logging
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from shapely.geometry import Polygon as ShapelyPolygon, Point
from shapely import wkt
from core.config import get_config
from shapely.errors import ShapelyError
from .polygon_registry import (
    PolygonRegistry,
    PolygonLoadError,
    PolygonValidationError,
    get_polygon_registry,
    reset_polygon_registry,
)

__all__ = [
    'PolygonRegistry',
    'PolygonLoadError',
    'PolygonValidationError',
    'get_polygon_registry',
    'reset_polygon_registry',
]

logger = logging.getLogger(__name__)

# Polygon Manager class
class PolygonManager:
    def __init__(self, cities_dir: Optional[Union[str, Path]] = None):
        self.polygons: Dict[str, Dict[str, List[Tuple[ShapelyPolygon, str]]]] = {}
        self.cities_dir = Path(cities_dir) if cities_dir else Path(__file__).parent.parent.parent / "cities"
        self._config = get_config()
        self._load_all_polygons()

    # Load all polygons from cities directory
    def _load_all_polygons(self) -> None:
        """Load all polygons for all cities."""
        if not self.cities_dir.exists():
            logger.warning(f"Cities directory not found: {self.cities_dir}")
            return

        # Iterate over city directories
        for city_dir in self.cities_dir.iterdir():
            if city_dir.is_dir():
                # Support both YAML and JSON config files
                has_config = (city_dir / "config.yaml").exists() or (city_dir / "config.json").exists()
                if has_config:
                    self._load_city_polygons(city_dir.name)

    # Load polygons for a specific city
    def _load_city_polygons(self, city: str) -> None:
        """Load all polygons for a specific city.

        Polygons are indexed by the city's `city_code` (from city config). For
        backward compatibility the directory name is also stored as a key.
        """
        city_dir = self.cities_dir / city / "polygons"

        if not city_dir.exists():
            logger.warning(f"No polygons directory found for city: {city}")
            return

        # resolve canonical city code from loaded city configs
        city_config = self._config.get_city_config(city)
        city_code = None
        if city_config:
            city_code = getattr(city_config, "city_code", None)

        # load into a temporary structure then assign to keys
        zone_map: Dict[str, List[Tuple[ShapelyPolygon, str]]] = {}
        for zone_type_dir in city_dir.iterdir():
            if zone_type_dir.is_dir():
                zone_type = zone_type_dir.name
                zone_map[zone_type] = self._load_zone_polygons(zone_type_dir)

        # store under city directory name
        self.polygons[city] = zone_map

        # if city_code exists, store under that as well (uppercase for consistency)
        if city_code:
            key = str(city_code).upper()
            self.polygons[key] = zone_map
            logger.info(f"Registered polygons for city '{city}' under city_code '{key}'")

    # Load polygons from a zone directory
    def _load_zone_polygons(self, zone_dir: Path) -> List[Tuple[ShapelyPolygon, str]]:
        """Load all polygon files from a zone directory."""
        zone_polygons = []
        
        # Iterate over CSV files in the zone directory
        for poly_file in zone_dir.glob("*.csv"):
            try:
                with open(poly_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) < 2:
                            continue

                        # Some CSVs contain commas inside the WKT; allow the
                        # last column to be the polygon name and join the rest
                        # back into the WKT string to be robust against missing
                        # quoting in source files.
                        if len(row) == 2:
                            wkt_str, name = row[0].strip(), row[1].strip()
                        else:
                            wkt_str = ','.join(col for col in row[:-1]).strip()
                            name = row[-1].strip()
                        if not wkt_str or not name:
                            continue
                            
                        try:
                            polygon = wkt.loads(wkt_str)
                            # Clean geometry: remove duplicate coordinates, ensure closed
                            polygon = self._clean_polygon(polygon)
                            if polygon is None or not polygon.is_valid:
                                logger.warning(f"Invalid geometry in {poly_file}: {wkt_str}")
                                continue
                            zone_polygons.append((polygon, name))
                        except ShapelyError as e:
                            logger.error(f"Failed to parse WKT in {poly_file}: {e}")
                            
            except Exception as e:
                logger.error(f"Error reading polygon file {poly_file}: {e}")
                
        return zone_polygons

    # Clean polygon geometry
    def _clean_polygon(self, polygon: ShapelyPolygon) -> Optional[ShapelyPolygon]:
        """Return a cleaned Polygon: remove duplicate consecutive coordinates
        and ensure the linear ring is closed. Returns None if not a polygon.
        """
        try:
            if polygon.geom_type != 'Polygon':
                # attempt to get polygon from geometry
                logger.debug(f"Skipping non-Polygon geometry: {polygon.geom_type}")
                return None

            exterior = list(polygon.exterior.coords)
            if not exterior:
                return None

            # remove consecutive duplicate coordinates
            cleaned = [exterior[0]]
            for coord in exterior[1:]:
                if coord != cleaned[-1]:
                    cleaned.append(coord)

            # ensure closed
            if cleaned[0] != cleaned[-1]:
                cleaned.append(cleaned[0])

            return ShapelyPolygon(cleaned)
        except Exception as e:
            logger.error(f"Error cleaning polygon: {e}")
            return None

    # Check if point is in any polygon of a zone type
    def is_point_in_zone(
        self, 
        city: str, 
        zone_type: str, 
        point: Tuple[float, float], 
        polygon_name: Optional[str] = None
    ) -> bool:
        """Check if a point is inside any polygon of the specified zone type."""
        # try direct lookup, then try normalized forms
        lookup_keys = [city, city.upper(), city.lower()]
        found_key = None
        # Try different case variations for city key
        for k in lookup_keys:
            if k in self.polygons:
                found_key = k
                break

        # Check if city was found in polygons
        if not found_key:
            logger.warning(f"City not found: {city}")
            return False

        # Check if zone type exists for the city
        if zone_type not in self.polygons[found_key]:
            logger.warning(f"Zone type {zone_type} not found for city {found_key}")
            return False

        point_obj = Point(point[1], point[0])  # Note: Shapely uses (x,y) = (lng,lat)

        # Check each polygon in the zone type
        for polygon, name in self.polygons[found_key][zone_type]:
            if polygon_name and name != polygon_name:
                continue
            if point_obj.within(polygon):
                return True
                
        return False

# Global polygon manager instance
polygon_manager = None

# Get the global polygon manager instance
def get_polygon_manager() -> PolygonManager:
    """Get the global polygon manager instance."""
    global polygon_manager
    # Initialize if not already done
    if polygon_manager is None:
        polygon_manager = PolygonManager()
    return polygon_manager


# Reload the polygon manager
def reload_polygon_manager() -> PolygonManager:
    """Reload polygons by resetting the global manager."""
    global polygon_manager
    polygon_manager = None
    # Reset the global polygon manager instance to force reload
    return get_polygon_manager()