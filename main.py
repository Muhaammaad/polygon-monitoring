# main.py
#!/usr/bin/env python3
"""
Uber Polygon Monitoring System - Main Entry Point
"""
import logging
import sys
from pathlib import Path

import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure core module is importable
sys.path.insert(0, str(Path(__file__).parent.parent))     


# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from core.config import config
from core.polygons import get_polygon_manager
from core.schedular.executor import start_scheduler

def setup_logging():
    """Configure logging based on the configuration"""
    logging_config = config.get_logging_config()
    log_level_str = logging_config.get('level', 'INFO').upper()
    log_level = getattr(logging, log_level_str)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set log level for external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('shapely').setLevel(logging.WARNING)

def main():
    """Main application entry point"""
    logger = logging.getLogger(__name__)
    
    try:
        # Set up logging
        setup_logging()
        
        logger.info("Starting Uber Polygon Monitoring System")
        
        # Initialize the polygon manager
        polygon_manager = get_polygon_manager()
        
        # Log loaded cities and zones
        for city_code in config.city_codes:
            city_config = config.get_city_config(city_code)
            if city_config:
                logger.info(f"Loaded city: {city_code} with zones: {', '.join(city_config.zones)}")
        
        # Start the scheduler for periodic checks
        logger.info("Starting scheduler...")
        interval_minutes = config.get_default_time_window_minutes()
        start_scheduler(interval_minutes)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")      
    except Exception as e:
        logger.exception("Fatal error in main loop")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())