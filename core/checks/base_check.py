# core/checks/base_check.py
"""
Abstract base class for all check implementations.

This module defines the interface that all checks must implement,
providing a consistent execution pattern across different check types.

Requirements from V2 Spec:
- query(city_config) -> List[Dict]: Get candidates from database
- evaluate(candidate, city_config) -> Optional[str]: Return warning note or None
- execute(city_config) -> List[Dict]: Orchestrate query + evaluate + insert warnings
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import pymysql

# Set up logging
logger = logging.getLogger(__name__)


# Abstract BaseCheck class definition (to be extended by all checks)
class BaseCheck(ABC):
    """
    Abstract base class for all check implementations.
    
    The check lifecycle follows these steps:
    1. query(city_config) - Retrieve candidates from the database
    2. evaluate(candidate, city_config) - Check each candidate against rules
    3. execute(city_config) - Orchestrate query + evaluate + insert warnings
    
    Subclasses must implement all three abstract methods.
    """
    
    # Constructor with optional dependencies
    def __init__(self, db_conn=None, notification_manager=None):
        """
        Initialize the check with a database connection and notification manager.
        
        Args:
            db_conn: Database connection (optional, uses default if None)
            notification_manager: NotificationManager instance (optional, uses default if None)
        """
        if db_conn is None:
            from ..db.database import get_db
            db_conn = get_db()
        
        # Lazy import to avoid circular dependencies
        if notification_manager is None:
            from ..notifications import get_notification_manager
            notification_manager = get_notification_manager()
        
        self.db = db_conn
        self.notification_manager = notification_manager
        self.check_name = self.__class__.__name__
    
    # Abstract methods to be implemented by subclasses
    @abstractmethod
    def query(self, city_config: Any) -> List[Dict[str, Any]]:
        """
        Query the database for candidates to check.
        
        This method retrieves all entities that need to be evaluated
        for the current check based on the city configuration.
        
        Args:
            city_config: City-specific configuration object containing
                        check parameters, time windows, status mappings, etc.
        
        Returns:
            List of candidate records (typically from activity log).
            Each record must include: uuid, latitude, longitude, ts
        
        Example:
            [
                {
                    'uuid': 'abc123',
                    'latitude': 46.52,
                    'longitude': 6.62,
                    'ts': datetime(2024, 1, 15, 10, 30),
                    'status': 'LOGIN_EVENT'
                }
            ]
        
        Raises:
            Exception: If database query fails (caught by execute())
        """
        pass
    
    # Abstract method to evaluate a single candidate
    @abstractmethod
    def evaluate(self, candidate: Dict[str, Any], city_config: Any) -> Optional[str]:
        """
        Evaluate a single candidate against check rules.
        
        This method contains the core business logic for determining whether
        a candidate violates the check's rules.
        
        Args:
            candidate: A single record from query() results
            city_config: City-specific configuration for rule evaluation
        
        Returns:
            Warning note string if violation detected, None if candidate is valid.
            The warning note should be descriptive (e.g., "Login outside zone")
        
        Example return values:
            - "Login event outside designated login zone"
            - "Driver paused in waiting zone instead of center zone"
            - None (no violation)
        
        Raises:
            Exception: If evaluation fails (caught by execute())
        """
        pass
    
    # Abstract method to execute the full check workflow
    @abstractmethod
    def execute(self, city_config: Any) -> List[Dict[str, Any]]:
        """
        Execute the complete check workflow.
        
        This is the main entry point that orchestrates:
        1. Query candidates using query()
        2. Evaluate each candidate using evaluate()
        3. Insert warnings to database for violations
        4. Return list of generated warnings
        
        Args:
            city_config: City-specific configuration
        
        Returns:
            List of warnings that were generated. Each warning dict contains:
            - uuid: Driver UUID
            - warning_type: Type of warning (check name)
            - note: Description of the violation
            - ts: Timestamp of the check
            - city_code: City where violation occurred
        
        Example:
            [
                {
                    'uuid': 'abc123',
                    'warning_type': 'login',
                    'note': 'Login outside zone',
                    'ts': datetime(2024, 1, 15, 10, 30),
                    'city_code': 'GE'
                }
            ]
        
        Note:
            Implementations should handle errors gracefully and log appropriately.
            Database failures should not crash the entire monitoring system.
        """
        pass
    
    # Helper methods (common across all checks)
    # These can be used by subclasses as needed.
    def _raw_statuses_for_group(self, city_config: Any, status_group_name: str) -> List[str]:
        """
        Convert a status group name to raw database status values.
        
        This helper resolves the indirection: status_group → canonical_statuses → raw_statuses
        
        Args:
            city_config: City configuration with status mapping and groups
            status_group_name: Name of the status group (e.g., 'login_candidates')
        
        Returns:
            List of raw database status strings that belong to this group
        
        Example:
            Input: status_group_name='login_candidates'
            Config has:
                mapping: {'LOGIN_EVENT': 'login_event', 'NEW_LOGIN': 'login_event'}
                groups: {'login_candidates': ['login_event']}
            Output: ['LOGIN_EVENT', 'NEW_LOGIN']
        """
        raw_statuses = [] 
        
        # Handle different config structures (dict vs object)
        if hasattr(city_config, 'status'):
            status_config = city_config.status
        else:
            status_config = city_config.get('status', {})
        
        # Extract mapping and groups
        if hasattr(status_config, 'mapping'):
            mapping = status_config.mapping
            groups = status_config.groups
        else:
            mapping = status_config.get('mapping', {})
            groups = status_config.get('groups', {})
        
        # Get canonical statuses for this group
        canonical_statuses = groups.get(status_group_name, [])
        
        # Find all raw statuses that map to these canonical statuses
        for raw_status, canonical_status in mapping.items():
            if canonical_status in canonical_statuses:   
                raw_statuses.append(raw_status)
        
        # Log warning if no statuses found
        if not raw_statuses:
            if hasattr(city_config, 'city_code'):
                city_code = city_config.city_code
            elif hasattr(city_config, 'get'):
                city_code = city_config.get('city_code', 'UNKNOWN')
            else:
                city_code = 'UNKNOWN'
            logger.warning(
                f"No raw statuses found for group '{status_group_name}' "
                f"in city {city_code}"
            )
        
        return raw_statuses
    
    # Helper to fetch user details for notification
    def _get_user(self, uuid: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user details from database for notification.
        
        Args:
            uuid: Driver UUID
        
        Returns:
            User dict with telegram_id, phone, prefix, etc. or None if not found
        """
        query = """
        SELECT uuid_id, first_name, prefix, phone, telegram_id, telegram_language
        FROM users
        WHERE uuid_id = %s
        """
        
        try:
            cursor = self.db.cursor(pymysql.cursors.DictCursor)
            cursor.execute(query, (uuid,))
            user = cursor.fetchone()
            cursor.close()
            return user
        except Exception as e:
            logger.error(f"Failed to fetch user {uuid}: {e}")
            return None
    
    # Helper to insert warning and send notification
    def _insert_warning(
        self,
        uuid: str,
        warning_type: str,
        note: str,
        city_code: str,
        ts: Optional[datetime] = None,
        city_config: Any = None
    ) -> bool:
        """
        Insert a warning record into the database (uber_warnings) and send notification.
        
        Args:
            uuid: Driver UUID
            warning_type: Type of warning ('login', 'pause', 'out_of_town')
            note: Description of the violation
            city_code: City code where violation occurred
            ts: Timestamp of the warning (defaults to now)
            city_config: City configuration (required for notification sending)
        
        Returns:
            True if insert succeeded, False otherwise
        
        Side Effects:
            Inserts a row into uber_warnings table
            Sends notification via Telegram/SMS
        """
        if ts is None:
            ts = datetime.utcnow()
        
        # Actual schema: id, driver_id, note, counter, ts
        query = """
        INSERT INTO uber_warnings 
        (driver_id, note, ts)
        VALUES (%s, %s, %s)
        """
        
        try:
            cursor = self.db.cursor()
            cursor.execute(query, (uuid, note, ts))
            self.db.commit()
            cursor.close()
            
            logger.info(
                f"Inserted warning for {uuid} in {city_code}: {note}"
            )
            
            # Send notification after successful insert
            if city_config and self.notification_manager:
                user = self._get_user(uuid)
                if user:
                    try:
                        # Use sync wrapper since we're in sync context
                        sent = self.notification_manager.send_sync(user, note, city_config)
                        if sent:
                            logger.info(f"Notification sent to {uuid} for {note}")
                        else:
                            logger.warning(f"Notification failed for {uuid} for {note}")
                    except Exception as e:
                        logger.error(f"Error sending notification to {uuid}: {e}")
                else:
                    logger.warning(f"User {uuid} not found for notification; notification not sent for warning '{note}' in city '{city_code}'")
                    # Do not trigger IT channel notification for None
            
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to insert warning for {uuid}: {e}",
                exc_info=True
            )
            try:
                self.db.rollback()
            except:
                pass
            return False
    
    # Helper to get check configuration from city config
    def _get_check_config(self, city_config: Any, check_name: Optional[str] = None) -> Optional[Any]:
        """
        Get the configuration for this specific check from city config.
        
        Args:
            city_config: City configuration object
            check_name: Name of the check (defaults to class name in snake_case)
        
        Returns:
            Check configuration object if found and enabled, None otherwise
        
        Example:
            check_cfg = self._get_check_config(city_config)
            if check_cfg:
                time_window = check_cfg.time_window_minutes
        """
        if check_name is None:
            # Convert class name to snake_case (e.g., LoginCheck -> login_check)
            check_name = ''.join(
                ['_' + c.lower() if c.isupper() else c for c in self.check_name]
            ).lstrip('_')
        
        # Handle different config structures (dict vs object)
        if hasattr(city_config, 'checks'):
            checks = city_config.checks
        else:
            checks = city_config.get('checks', {})
        
        # Fetch specific check config
        if isinstance(checks, dict):
            check_cfg = checks.get(check_name)
        else:
            check_cfg = getattr(checks, check_name, None)
        
        # Check if config exists
        if not check_cfg:
            if hasattr(city_config, 'city_code'):
                city_code = city_config.city_code
            elif hasattr(city_config, 'get'):
                city_code = city_config.get('city_code', 'UNKNOWN')
            else:
                city_code = 'UNKNOWN'
            logger.debug(f"Check '{check_name}' not configured for city {city_code}")
            return None
        
        # Check if the check is enabled
        if hasattr(check_cfg, 'enabled'):
            enabled = check_cfg.enabled
        elif isinstance(check_cfg, dict):
            enabled = check_cfg.get('enabled', True)
        else:
            enabled = True
        
        # Return None if disabled
        if not enabled:
            if hasattr(city_config, 'city_code'):
                city_code = city_config.city_code
            elif hasattr(city_config, 'get'):
                city_code = city_config.get('city_code', 'UNKNOWN')
            else:
                city_code = 'UNKNOWN'
            logger.debug(f"Check '{check_name}' is disabled for city {city_code}")
            return None
        
        return check_cfg
    
    # Helper to log execution summary
    def _log_execution_summary(
        self,
        city_code: str,
        candidates_count: int,
        warnings_count: int,
        execution_time_ms: float
    ) -> None:
        """
        Log a summary of check execution.
        
        Args:
            city_code: City that was checked
            candidates_count: Number of candidates evaluated
            warnings_count: Number of warnings generated
            execution_time_ms: Execution time in milliseconds
        """
        logger.info(
            f"{self.check_name} completed for {city_code}: "
            f"{candidates_count} candidates, {warnings_count} warnings, "
            f"{execution_time_ms:.2f}ms"
        )


# custom exceptions for check errors
# These can be raised by check implementations
# to signal specific failure modes. 
class CheckExecutionError(Exception):
    """Exception raised when check execution fails."""
    
    def __init__(self, check_name: str, city_code: str, message: str):
        self.check_name = check_name
        self.city_code = city_code
        self.message = message
        super().__init__(f"{check_name} failed for {city_code}: {message}")

# custom exceptions for check errors
# These can be raised by check implementations
# to signal specific failure modes.
class CheckValidationError(Exception):
    """Exception raised when check configuration validation fails."""
    
    # Constructor
    def __init__(self, check_name: str, city_code: str, message: str):
        self.check_name = check_name
        self.city_code = city_code
        self.message = message
        super().__init__(f"{check_name} validation failed for {city_code}: {message}")