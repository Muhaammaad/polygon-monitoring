# core/checks/delivery_check.py

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import pymysql
from .base_check import BaseCheck
from ..polygons import get_polygon_registry
from ..config import get_config
from pathlib import Path

logger = logging.getLogger(__name__)


# DeliveryCheck implementation
class DeliveryCheck(BaseCheck):
    """Check for delivery drivers outside the delivery zone."""

    # Constructor
    def __init__(self, db_conn=None, polygon_registry=None, notification_manager=None):
        super().__init__(db_conn=db_conn, notification_manager=notification_manager)
        self.registry = polygon_registry or get_polygon_registry()

    # Helper to get delivery statuses
    def _get_delivery_statuses(self, city_config: Any, check_cfg: Any) -> List[str]:
        """Resolve raw DB statuses that represent active deliveries."""
        status_group = getattr(check_cfg, 'status_group', None) or (
            check_cfg.get('status_group') if isinstance(check_cfg, dict) else None
        )
        if not status_group:
            return []
        return self._raw_statuses_for_group(city_config, status_group)

    # Query candidates
    def query(self, city_config: Any) -> List[Dict[str, Any]]:
        """Query recent delivery activity candidates for a city."""
        check_cfg = self._get_check_config(city_config, 'delivery_check')
        if not check_cfg:
            return []

        time_window = getattr(check_cfg, 'time_window_minutes', None)
        if time_window is None and isinstance(check_cfg, dict):
            time_window = check_cfg.get('time_window_minutes')
        if not time_window:
            city_code = getattr(city_config, 'city_code', 'UNKNOWN')
            logger.error(f"delivery_check missing time_window_minutes in {city_code}")
            return []

        raw_statuses = self._get_delivery_statuses(city_config, check_cfg)
        if not raw_statuses:
            city_code = getattr(city_config, 'city_code', 'UNKNOWN')
            logger.info(f"No statuses mapped for delivery_check in {city_code}")
            return []

        placeholders = ','.join(['%s'] * len(raw_statuses))
        query = f"""
            SELECT DISTINCT t1.uuid, t1.latitude, t1.longitude, t1.location,
                           t1.status, t1.ts
            FROM uber_activity_log_live t1
            WHERE t1.ts BETWEEN DATE_SUB(NOW(), INTERVAL %s MINUTE) AND NOW()
            AND t1.location = %s
            AND t1.status IN ({placeholders})
        """

        try:
            cursor = self.db.cursor(pymysql.cursors.DictCursor)
            params = [time_window, city_config.city_code] + raw_statuses
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results if results else []     
        except Exception as e:
            logger.error(f"Error querying delivery candidates: {e}")
            return []

    # Evaluate candidate
    def evaluate(self, candidate: Dict[str, Any], city_config: Any) -> Optional[str]:
        """Return out_of_town if delivery candidate is outside delivery zone."""
        check_cfg = self._get_check_config(city_config, 'delivery_check')
        if not check_cfg:
            return None

        target_zone = getattr(check_cfg, 'target_zone', None)
        if target_zone is None and isinstance(check_cfg, dict):
            target_zone = check_cfg.get('target_zone')
        target_zone = target_zone or 'delivery_zone'

        try:
            latitude = candidate.get('latitude')
            longitude = candidate.get('longitude')
            city_code = candidate.get('location') or getattr(city_config, 'city_code', 'UNKNOWN')

            in_zone = self.registry.contains_point(city_code, target_zone, latitude, longitude)
            if not in_zone:
                logger.debug(f"Driver {candidate.get('uuid')} outside {target_zone}")
                return 'out_of_town'
            return None
        except Exception as e:
            logger.error(f"Error evaluating delivery candidate {candidate.get('uuid')}: {e}")
            return None

    # Execute check
    def execute(self, city_config: Any) -> List[Dict[str, Any]]:
        """Run delivery check workflow for a single city."""
        start_ts = datetime.utcnow()
        check_cfg = self._get_check_config(city_config, 'delivery_check')
        if not check_cfg:
            return []

        # Ensure polygons for this city are loaded into the registry
        try:
            cfg = get_config()
            city_code = getattr(city_config, 'city_code', None)
            city_dir = cfg.resolve_city_dir_by_code(city_code) or (str(city_code).lower() if city_code else None)
            cities_base = str(Path(__file__).resolve().parents[2] / "cities")
            if city_code and city_code not in self.registry.get_loaded_cities():
                self.registry.load_city(city_code, cities_base_path=cities_base, city_dir_name=city_dir)
        except Exception as e:
            logger.error(f"Failed to load polygons for city {getattr(city_config, 'city_code', 'UNKNOWN')}: {e}")

        candidates = self.query(city_config)
        warnings: List[Dict[str, Any]] = [] 

        # Evaluate each candidate
        for candidate in candidates:  
            note = self.evaluate(candidate, city_config)
            if not note:
                continue

            warning = {
                'uuid': candidate.get('uuid'),
                'warning_type': 'out_of_town',
                'note': note,
                'ts': candidate.get('ts'),
                'city_code': candidate.get('location') or getattr(city_config, 'city_code', 'UNKNOWN')
            }

            inserted = self._insert_warning(
                uuid=warning['uuid'],
                warning_type=warning['warning_type'],
                note=warning['note'],
                city_code=warning['city_code'],
                ts=warning['ts'],
                city_config=city_config
            )
            if inserted:
                warnings.append(warning)

        duration_ms = (datetime.utcnow() - start_ts).total_seconds() * 1000
        self._log_execution_summary(
            city_code=getattr(city_config, 'city_code', 'UNKNOWN'),
            candidates_count=len(candidates),
            warnings_count=len(warnings),
            execution_time_ms=duration_ms,
        )

        return warnings