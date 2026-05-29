import logging
import time
import inspect
from typing import List, Optional, Dict, Any

from core.config import get_config
from core.utils.healthcheck import start_healthcheck_from_env
from core.checks.base_check import BaseCheck
from core.checks.login_check import LoginCheck
from core.checks.center_check import CenterCheck
from core.checks.delivery_check import DeliveryCheck
from core.notifications import get_notification_manager


# Logger for this module
logger = logging.getLogger(__name__)


# Auto-discover checks  
def _discover_checks() -> Dict[str, type]:
    """
    Auto-discover all BaseCheck subclasses for pluggable architecture.
    Maps check name (snake_case from class name) to class.
    """
    checks = {}
    # Import all check modules to ensure classes are registered
    import core.checks.login_check
    import core.checks.center_check
    import core.checks.delivery_check
    
    # Discover all BaseCheck subclasses from imported modules
    for mod in [core.checks.login_check, core.checks.center_check, core.checks.delivery_check]:
        for name, obj in inspect.getmembers(mod):
            if inspect.isclass(obj) and issubclass(obj, BaseCheck) and obj != BaseCheck:
                # Convert class name to snake_case (e.g., LoginCheck -> login_check)
                check_key = ''.join(['_' + c.lower() if c.isupper() else c for c in obj.__name__]).lstrip('_')
                checks[check_key] = obj
    
    logger.debug(f"Discovered checks: {list(checks.keys())}")
    return checks


CHECK_MAP = _discover_checks()


# Run checks for a single city
def _run_checks_for_city(city_config, checks: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run selected checks for a single city and return a summary."""
    summary = {
        'city': getattr(city_config, 'city_code', 'UNKNOWN'),
        'results': [],
    }

    # Get notification manager singleton
    notification_manager = get_notification_manager()

    selected = checks or list(CHECK_MAP.keys())
    # Run each selected check
    for name in selected:
        cls = CHECK_MAP.get(name)
        if not cls:
            logger.warning(f"Unknown check '{name}'")
            continue

        try:
            # Initialize check with notification_manager
            check = cls(notification_manager=notification_manager)
            warnings = check.execute(city_config)
            result_summary = {
                'check': name,
                'warnings': len(warnings),
            }
            summary['results'].append(result_summary)
            logger.info(
                f"Check {name} city={summary['city']} warnings={result_summary['warnings']}"
            )
        except Exception as e:
            logger.error(f"Error running {name} for {summary['city']}: {e}")
    return summary


# Run checks once across specified cities
def run_once(cities: Optional[List[str]] = None, checks: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Run selected checks once across specified cities (or all)."""
    config = get_config()
    summaries: List[Dict[str, Any]] = []

    target_cities = cities or config.cities
    # Run checks for each target city
    for city_dir in target_cities:
        city_config = config.get_city_config(city_dir)
        if not city_config:
            logger.warning(f"No config for city {city_dir}")
            continue
        summaries.append(_run_checks_for_city(city_config, checks))
    return summaries


# Start the scheduler loop
def start_scheduler(interval_minutes: int = 3, cities: Optional[List[str]] = None, checks: Optional[List[str]] = None,
                    stop_after_cycles: Optional[int] = None) -> None:
    """Start a simple loop scheduler to run checks periodically.

    Args:
        interval_minutes: Interval between runs.
        cities: Optional list of city directories to run, defaults to all.
        checks: Optional list of checks to run (login, center, delivery).
        stop_after_cycles: If provided, stops after N cycles (useful for testing).
    """
    cycles = 0
    logger.info(
        f"Starting scheduler interval={interval_minutes}m cities={cities or 'ALL'} checks={checks or 'ALL'}"
    )
    # Start healthcheck server if configured via ENV
    hc = None
    try:
        hc = start_healthcheck_from_env()
    except Exception as e:
        logger.error(f"Failed to start healthcheck: {e}")

    try:
        while True:
            try:
                run_once(cities=cities, checks=checks)
            except Exception as e:
                logger.error(f"Scheduler run failed: {e}")

            cycles += 1
            if stop_after_cycles and cycles >= stop_after_cycles:
                logger.info("Scheduler stopping after requested cycles")
                break
            time.sleep(max(1, int(interval_minutes)) * 60)
    except KeyboardInterrupt:
        logger.info("Scheduler interrupted. Shutting down gracefully.")
    finally:
        try:
            if hc:
                hc.stop()
        except Exception:
            pass
