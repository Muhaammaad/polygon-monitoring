#!/usr/bin/env python3
# cli/main.py

import argparse                       # CLI Parsing(argparse)
import logging                        # Logging
import sys                            # System-specific parameters and functions
from typing import List               # Type hinting for lists
from pathlib import Path              # Filesystem path manipulation

logger = logging.getLogger(__name__)


'''Ensures imports like core.config work even when running from CLI
Makes the project deployable without PYTHONPATH hacks'''

PROJECT_ROOT = Path(__file__).resolve().parent.parent    
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))



# Core imports (Core modules this CLI depends on)

from core.config import get_config                              #Loads all city configuration (YAML/JSON)
from core.logging.setup import configure_logging                #Logging setup utility
from core.polygons import get_polygon_manager                   #Polygon manager for handling city polygons
from core.schedular.executor import run_once, start_scheduler   #Scheduler for periodic checks
from core.polygons import reload_polygon_manager                #Reloads polygon definitions
from core.utils.healthcheck import HealthcheckServer            #Healthcheck server for monitoring system health


# Logging setup
def setup_logging(level: str = "INFO"):
    configure_logging(level)                      #Logging behavior is centralized (file/JSON/console handled elsewhere)


# List available cities
def cmd_list_cities():
    cfg = get_config()
    for c in cfg.cities:         # List all loaded city configurations
        logger.info(f"City: {c}")
        print(c)


# Validate polygon definitions
def cmd_validate_polygons():
    get_polygon_manager()  # loads and validates
    logger.info("Polygon definitions validated successfully") 
    print("Polygons validated successfully")



# Resolve city arguments (City Resolution Logic)
def _resolve_cities_arg(args):
    """Allow city selection by directory name or city_code; returns list or None."""
    cfg = get_config()
    inputs = args.cities or (args.city and [args.city]) or []
    if not inputs:
        return None

    resolved = []
    for entry in inputs:
        cc = cfg.get_city_config(entry)
        if not cc:
            logger.error(f"Unknown city identifier '{entry}'")
            sys.exit(2)
        # prefer directory key for executor consistency
        city_dir = cfg.resolve_city_dir_by_code(cc.city_code) or entry
        resolved.append(city_dir)
    return resolved

# Run checks once
def cmd_run_once(args):
    cities = _resolve_cities_arg(args)
    checks = args.checks
    summaries = run_once(cities=cities, checks=checks)
    # brief output summary
    total_warnings = sum(sum(r.get('warnings', 0) for r in s['results']) for s in summaries)
    logger.info(f"Run complete. Total warnings: {total_warnings}")
    print(f"Run complete. Total warnings: {total_warnings}")

# Start periodic check scheduler
def cmd_start_scheduler(args):
    cities = _resolve_cities_arg(args)
    checks = args.checks
    # Use CLI argument if provided, otherwise fall back to ENV/config
    config = get_config()
    interval = args.interval if args.interval != 3 else config._config.get('app', {}).get('scheduler_interval_minutes', 3)
    start_scheduler(interval_minutes=interval, cities=cities, checks=checks,
                    stop_after_cycles=args.stop_after)
       


#
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Uber Polygon Monitoring System CLI")
    parser.add_argument('--log-level', default='INFO', help='Logging level (DEBUG, INFO, WARNING, ERROR)')

    sub = parser.add_subparsers(dest='command')

    # list cities
    p_list = sub.add_parser('list-cities', help='List available cities')
    p_list.set_defaults(func=lambda a: cmd_list_cities())

    # validate polygons
    p_val = sub.add_parser('validate-polygons', help='Validate polygon definitions (alias: polygons validate)')
    p_val.set_defaults(func=lambda a: cmd_validate_polygons())

    # polygons reload
    p_reload = sub.add_parser('polygons-reload', help='Reload polygon registry (alias: polygons reload)')
    def _reload(_):
        
        reload_polygon_manager()
        logger.info("Polygons reloaded successfully")
        print("Polygons reloaded successfully")
    p_reload.set_defaults(func=_reload)

    # run once
    p_run = sub.add_parser('run-once', help='Run checks once (alias: monitor run)')
    p_run.add_argument('--city', help='Run for a single city')
    p_run.add_argument('--cities', nargs='*', help='Run for multiple cities')
    p_run.add_argument('--checks', nargs='*', choices=['login', 'center', 'delivery'], help='Checks to run')
    p_run.set_defaults(func=cmd_run_once)

    # start scheduler
    p_sched = sub.add_parser('start-scheduler', help='Start periodic check scheduler (alias: monitor start)')
    p_sched.add_argument('--city', help='Run for a single city')
    p_sched.add_argument('--cities', nargs='*', help='Run for multiple cities')
    p_sched.add_argument('--checks', nargs='*', choices=['login', 'center', 'delivery'], help='Checks to run')
    p_sched.add_argument('--interval', type=int, default=3, help='Interval in minutes between runs (default: from SCHEDULER_INTERVAL env var or 3)')
    p_sched.add_argument('--stop-after', type=int, help='Stop after N cycles (testing)')
    p_sched.set_defaults(func=cmd_start_scheduler)

    # config validate
    p_cfg = sub.add_parser('config-validate', help='Validate all city configs (alias: config validate)')
    def _cfg_validate(_):
        cfg = get_config()
        errors = []
        for city in cfg.cities:
            cc = cfg.get_city_config(city)
            # language block
            if not cc.language or not cc.language.default or not cc.language.supported:
                logger.warning(f"{city}: missing language block")
                errors.append(f"{city}: missing language block")
            else:
                if cc.language.default not in cc.language.supported:
                    logger.warning(f"{city}: default language not in supported languages")
                    errors.append(f"{city}: default language not in supported")
            # status mapping/groups minimal presence
            if not cc.status or not cc.status.mapping or not cc.status.groups:
                logger.warning(f"{city}: missing status mapping/groups")
                errors.append(f"{city}: missing status mapping/groups")
            # checks presence (login at minimum)
            if 'login_check' not in cc.checks:
                logger.warning(f"{city}: missing login_check")
                errors.append(f"{city}: missing login_check")
        if errors:
            logger.error("Config validation FAILED with errors:")
            print("Config validation FAILED:")
            for e in errors:
                logger.error(f" - {e}")
                print(" -", e)
            sys.exit(2)
        logger.info("All city configs validated successfully")
        print("All city configs validated successfully")
    p_cfg.set_defaults(func=_cfg_validate)

    # Aliases using grouped subcommands
    # polygons validate|reload
    p_polygons = sub.add_parser('polygons', help='Polygon operations')
    sp_poly = p_polygons.add_subparsers(dest='poly_cmd')
    sp_val = sp_poly.add_parser('validate', help='Validate polygon definitions')
    sp_val.set_defaults(func=lambda a: cmd_validate_polygons())
    sp_rel = sp_poly.add_parser('reload', help='Reload polygon registry')
    def _reload_alias(_):   
        reload_polygon_manager()
        logger.info("Polygons reloaded successfully")
        print("Polygons reloaded successfully")   
    sp_rel.set_defaults(func=_reload_alias)

    # monitor run|start
    p_monitor = sub.add_parser('monitor', help='Monitoring operations')
    sp_mon = p_monitor.add_subparsers(dest='mon_cmd')
    sp_run = sp_mon.add_parser('run', help='Run checks once')
    sp_run.add_argument('--city', help='Run for a single city')
    sp_run.add_argument('--cities', nargs='*', help='Run for multiple cities')
    sp_run.add_argument('--checks', nargs='*', choices=['login', 'center', 'delivery'], help='Checks to run')
    sp_run.set_defaults(func=cmd_run_once)

    # monitor start
    sp_start = sp_mon.add_parser('start', help='Start periodic check scheduler')
    sp_start.add_argument('--city', help='Run for a single city')
    sp_start.add_argument('--cities', nargs='*', help='Run for multiple cities')
    sp_start.add_argument('--checks', nargs='*', choices=['login', 'center', 'delivery'], help='Checks to run')
    sp_start.add_argument('--interval', type=int, default=3, help='Interval in minutes between runs (default: 3)')
    sp_start.add_argument('--stop-after', type=int, help='Stop after N cycles (testing)')
    sp_start.set_defaults(func=cmd_start_scheduler)

    # config validate alias
    p_conf = sub.add_parser('config', help='Configuration operations')
    sp_conf = p_conf.add_subparsers(dest='cfg_cmd')
    sp_conf_val = sp_conf.add_parser('validate', help='Validate all city configs')
    sp_conf_val.set_defaults(func=_cfg_validate)

    # healthcheck start
    p_hc = sub.add_parser('healthcheck', help='Healthcheck endpoint operations')
    sp_hc = p_hc.add_subparsers(dest='hc_cmd')
    def _hc_start(args):
        port = getattr(args, 'port', 8080)
        srv = HealthcheckServer(port=port)
        srv.start()
        logger.info(f"Healthcheck listening on :{port}. Press Ctrl+C to stop.")
        print(f"Healthcheck listening on :{port}. Press Ctrl+C to stop.")
        try:
            while True:
                pass
        except KeyboardInterrupt:
            srv.stop()
    sp_hc_start = sp_hc.add_parser('start', help='Start healthcheck server')
    sp_hc_start.add_argument('--port', type=int, default=8080)
    sp_hc_start.set_defaults(func=_hc_start)

    return parser

# Main entry point
def main(argv: List[str] = None):
    parser = build_parser()
    args = parser.parse_args(argv)
    setup_logging(args.log_level)   

    if not hasattr(args, 'func'):
        parser.print_help()
        sys.exit(1)
    args.func(args)



if __name__ == '__main__':
    main()