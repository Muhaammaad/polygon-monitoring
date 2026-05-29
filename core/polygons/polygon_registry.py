# core/polygons/polygon_registry.py
"""
Polygon Registry Module

Manages loading, caching, and querying of polygon geometries for geographic zones.
Supports WKT format, Shapely objects, and point-in-polygon evaluation.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from shapely.geometry import Point, Polygon as ShapelyPolygon
from shapely.wkt import loads as wkt_loads
from shapely.validation import make_valid

logger = logging.getLogger(__name__)


# this function is for exception handling
class PolygonValidationError(Exception):
    """Raised when polygon validation fails."""
    pass

# this function is for exception handling
class PolygonLoadError(Exception):
    """Raised when polygon loading fails."""
    pass


# this class manages the registry of polygons
class PolygonRegistry:
    """
    Registry for managing geographic polygons per city and zone.
    
    Polygons are stored in CSV files (WKT format) under:
    cities/<city_code>/polygons/<zone_type>/
    
    Structure:
        polygons[city_code][zone_type] = [
            {'name': str, 'geometry': Polygon},
            ...
        ]
    """
    # Initialize the registry
    def __init__(self):
        """Initialize the polygon registry with empty cache."""
        self.polygons: Dict[str, Dict[str, List[Dict]]] = {}
        self.loaded_cities: List[str] = []
        self.failed_loads: Dict[str, List[str]] = {}

    # Load all polygons for a city
    def load_city(
        self, 
        city_code: str, 
        cities_base_path: str = "cities",
        city_dir_name: Optional[str] = None
    ) -> bool:
        """
        Load all polygons for a city from CSV files.
        
        Args:
            city_code: City code (e.g., 'GE', 'TEST')
            cities_base_path: Base path to cities directory
            city_dir_name: Directory name (if different from city_code.lower())
            
        Returns:
            bool: True if load successful, False otherwise
            
        Raises:
            PolygonLoadError: If city directory not found or no polygons loaded
        """
        if city_dir_name is None:
            city_dir_name = city_code.lower()
        
        city_path = Path(cities_base_path) / city_dir_name
        polygons_path = city_path / "polygons"
        
        if not polygons_path.exists():
            logger.error(f"Polygon directory not found: {polygons_path}")
            raise PolygonLoadError(f"Polygon directory not found for city {city_code}")
        
        if city_code not in self.polygons:
            self.polygons[city_code] = {}          
        
        zone_dirs = [d for d in polygons_path.iterdir() if d.is_dir()]
        
        if not zone_dirs:
            logger.warning(f"No zone directories found in {polygons_path}")
            return False
        
        total_loaded = 0
        
        for zone_dir in zone_dirs:
            zone_name = zone_dir.name
            csv_files = list(zone_dir.glob("*.csv"))
            
            if not csv_files:
                logger.debug(f"No CSV files found in zone {zone_name}")
                continue
            
            zone_polygons = []
            zone_failed = 0
            
            for csv_file in csv_files:
                try:
                    loaded = self._load_csv_file(csv_file, city_code, zone_name)
                    zone_polygons.extend(loaded)
                    total_loaded += len(loaded)
                except PolygonLoadError as e:
                    logger.warning(f"Failed to load {csv_file}: {e}")
                    zone_failed += 1
            
            if zone_polygons:
                self.polygons[city_code][zone_name] = zone_polygons
                logger.info(
                    f"Loaded {len(zone_polygons)} polygons for {city_code}/{zone_name}"
                )
            
            if zone_failed > 0:
                if city_code not in self.failed_loads:
                    self.failed_loads[city_code] = []    
                self.failed_loads[city_code].append(f"{zone_name} ({zone_failed} files)")
        
        if total_loaded == 0:
            logger.error(f"No polygons loaded for city {city_code}")
            raise PolygonLoadError(f"No polygons loaded for city {city_code}")
        
        self.loaded_cities.append(city_code)
        logger.info(f"Successfully loaded {total_loaded} polygons for city {city_code}")
        
        return True
    
    # Load polygons from a single CSV file
    def _load_csv_file(
        self, csv_file: Path, city_code: str, zone_name: str
    ) -> List[Dict]:
        """
        Load polygons from a single CSV file.
        
        CSV Format:
            Column 1: WKT Polygon string
            Column 2: Polygon name
            
        Example:
            POLYGON((6.60 46.50, 6.64 46.50, 6.64 46.54, 6.60 46.54, 6.60 46.50)),Login Zone
        
        Args:
            csv_file: Path to CSV file
            city_code: City code for logging
            zone_name: Zone name for logging
            
        Returns:
            List of loaded polygon dicts   
            
        Raises:
            PolygonLoadError: If file cannot be read or parsed
        """
        import csv
        polygons = []           
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for line_num, row in enumerate(reader, 1):
                    # Skip empty or comment lines
                    if not row:
                        continue
                    if row[0].strip().startswith('#'):
                        continue
                    if len(row) < 2:
                        logger.warning(
                            f"{csv_file}:{line_num} - Invalid format (missing polygon name)"
                        )
                        continue
                    
                    wkt_str = row[0].strip()
                    poly_name = row[1].strip()    
                    
                    if not wkt_str or not poly_name:
                        logger.warning(
                            f"{csv_file}:{line_num} - Empty WKT or polygon name"
                        )
                        continue
                    
                    # Parse and validate polygon
                    polygon = self._parse_and_validate_polygon(
                        wkt_str, csv_file, line_num
                    )
                    
                    if polygon is not None:
                        polygons.append({
                            'name': poly_name,
                            'geometry': polygon,
                            'source': str(csv_file),
                        })
                        logger.debug(
                            f"Loaded polygon '{poly_name}' from {city_code}/{zone_name}"
                        )
        except IOError as e:
            raise PolygonLoadError(f"Cannot read file {csv_file}: {e}")
        except Exception as e:
            logger.error(f"{csv_file} - Error reading CSV: {e}")
        
        if not polygons:
            raise PolygonLoadError(f"No valid polygons found in {csv_file}")
        
        return polygons
    
    # Parse and validate a WKT polygon string
    def _parse_and_validate_polygon(
        self, wkt_str: str, source_file: Path, line_num: int
    ) -> Optional[ShapelyPolygon]:
        """
        Parse WKT string and validate polygon geometry.
        
        Args:
            wkt_str: WKT polygon string
            source_file: Source file for logging
            line_num: Line number for logging
            
        Returns:
            Shapely Polygon object or None if invalid
        """
        try:
            # Parse WKT
            geometry = wkt_loads(wkt_str)
            
            # Validate it's a polygon
            if not isinstance(geometry, ShapelyPolygon):
                logger.warning(
                    f"{source_file}:{line_num} - Not a polygon: {type(geometry).__name__}"
                )
                return None
            
            # Check for validity and auto-fix if needed
            if not geometry.is_valid:
                logger.debug(
                    f"{source_file}:{line_num} - Invalid polygon, attempting to fix"
                )
                geometry = make_valid(geometry)
                
                if not geometry.is_valid:
                    logger.warning(
                        f"{source_file}:{line_num} - Could not fix invalid polygon"
                    )
                    return None
            
            # Check for minimum area
            if geometry.area < 0.00001:
                logger.warning(
                    f"{source_file}:{line_num} - Polygon too small (area: {geometry.area})"
                )
                return None
            
            return geometry
        
        except Exception as e:
            logger.error(f"{source_file}:{line_num} - WKT parse error: {e}")
            return None
    
    # Get a specific polygon by city, zone, and name
    def get_polygon(
        self, city_code: str, zone_name: str, polygon_name: str
    ) -> Optional[ShapelyPolygon]:
        """
        Get a specific polygon by city, zone, and name.
        
        Args:
            city_code: City code (e.g., 'GE', 'TEST')
            zone_name: Zone name (e.g., 'login_zone')
            polygon_name: Polygon name (e.g., 'Login Zone')
            
        Returns:
            Shapely Polygon object or None if not found
        """
        try:
            zone_polygons = self.polygons.get(city_code, {}).get(zone_name, [])
            
            for poly_dict in zone_polygons:
                if poly_dict['name'] == polygon_name:
                    return poly_dict['geometry']
            
            logger.warning(
                f"Polygon not found: {city_code}/{zone_name}/{polygon_name}"
            )
            return None
        
        except Exception as e:
            logger.error(f"Error getting polygon {city_code}/{zone_name}/{polygon_name}: {e}")
            return None
    
    # Get all polygons for a city/zone combination
    def get_all_polygons(
        self, city_code: str, zone_name: str
    ) -> List[ShapelyPolygon]:
        """
        Get all polygons for a city/zone combination.
        
        Args:
            city_code: City code (e.g., 'GE')
            zone_name: Zone name (e.g., 'login_zone')
            
        Returns:
            List of Shapely Polygon objects
        """
        try:
            zone_polygons = self.polygons.get(city_code, {}).get(zone_name, [])
            return [poly['geometry'] for poly in zone_polygons]
        
        except Exception as e:
            logger.error(f"Error getting polygons {city_code}/{zone_name}: {e}")
            return []
    
    # Get all polygon details for a zone
    def get_polygon_details(
        self, city_code: str, zone_name: str
    ) -> List[Dict]:
        """
        Get all polygon details (including names and source) for a zone.
        
        Args:
            city_code: City code
            zone_name: Zone name
            
        Returns:
            List of polygon detail dicts with 'name', 'geometry', 'source'
        """
        try:
            return self.polygons.get(city_code, {}).get(zone_name, [])
        
        except Exception as e:
            logger.error(f"Error getting polygon details {city_code}/{zone_name}: {e}")
            return []
    
    # Check if a point is inside any polygon for a city/zone
    def contains_point(
        self, city_code: str, zone_name: str, latitude: float, longitude: float
    ) -> bool:
        """
        Check if a point is inside any polygon for a city/zone.
        
        Args:
            city_code: City code
            zone_name: Zone name
            latitude: Point latitude
            longitude: Point longitude
            
        Returns:
            True if point is inside any polygon, False otherwise
        """
        try:
            point = Point(longitude, latitude)
            polygons = self.get_all_polygons(city_code, zone_name)
            
            for polygon in polygons:
                if polygon.contains(point):
                    return True
              
            return False
        
        except Exception as e:
            logger.error(
                f"Error checking point containment in {city_code}/{zone_name}: {e}"
            )                                                             
            return False
    
    # Get the name of the polygon containing a point
    def get_containing_polygon_name(
        self, city_code: str, zone_name: str, latitude: float, longitude: float
    ) -> Optional[str]:
        """
        Get the name of the polygon containing a point (if any).
        
        Args:
            city_code: City code
            zone_name: Zone name
            latitude: Point latitude
            longitude: Point longitude
            
        Returns:
            Polygon name if found, None otherwise
        """
        try:
            point = Point(longitude, latitude)
            details = self.get_polygon_details(city_code, zone_name)
            
            for poly_dict in details:
                if poly_dict['geometry'].contains(point):
                    return poly_dict['name']         
            
            return None
        
        except Exception as e:
            logger.error(
                f"Error finding containing polygon in {city_code}/{zone_name}: {e}"
            )
            return None
    
    # Get list of loaded city codes
    def get_loaded_cities(self) -> List[str]:   
        """Get list of loaded city codes."""
        return self.loaded_cities.copy()
    
    # Get list of zone names for a city
    def get_zones_for_city(self, city_code: str) -> List[str]:
        """Get list of zone names for a city."""
        return list(self.polygons.get(city_code, {}).keys())
    
    # Get count of polygons in a zone
    def get_zone_polygon_count(self, city_code: str, zone_name: str) -> int:
        """Get count of polygons in a zone."""
        return len(self.polygons.get(city_code, {}).get(zone_name, []))
    
    # Clear polygons for a city
    def clear_city(self, city_code: str) -> None:
        """Clear all polygons for a city from cache."""
        if city_code in self.polygons:
            del self.polygons[city_code]
            if city_code in self.loaded_cities:
                self.loaded_cities.remove(city_code)
            logger.info(f"Cleared polygons for city {city_code}")
    
    # Clear all cached polygons
    def clear_all(self) -> None:
        """Clear all cached polygons."""
        self.polygons.clear()   
        self.loaded_cities.clear()
        self.failed_loads.clear()
        logger.info("Cleared all cached polygons")
              
    # Get statistics about cached polygons      
    def get_cache_stats(self) -> Dict:
        """Get statistics about cached polygons."""
        stats = {
            'loaded_cities': len(self.loaded_cities),
            'cities': self.loaded_cities.copy(),
            'zones_per_city': {},
            'total_polygons': 0,
        }
        # Count polygons per city/zone
        for city_code, zones in self.polygons.items():
            zone_counts = {}
            for zone_name, polys in zones.items():
                count = len(polys)
                zone_counts[zone_name] = count
                stats['total_polygons'] += count
            stats['zones_per_city'][city_code] = zone_counts
        
        if self.failed_loads:
            stats['failed_loads'] = self.failed_loads
        
        return stats


# Global registry instance
_registry: Optional[PolygonRegistry] = None

# Get the global polygon registry instance
def get_polygon_registry() -> PolygonRegistry:
    """
    Get the global polygon registry instance  (singleton).
    
    Returns:
        PolygonRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = PolygonRegistry()
    return _registry

# Reset the global polygon registry (for testing)
def reset_polygon_registry() -> None:
    """Reset the global polygon registry (for testing)."""
    global _registry
    _registry = None
