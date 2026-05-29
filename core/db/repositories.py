# core/db/repositories.py

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pymysql.connections import Connection


logger = logging.getLogger(__name__)

# Repository for querying uber_activity_log_live table
class ActivityLogRepository:
    """Query uber_activity_log_live for check operations."""
    
    # Initialize with a database connection
    def __init__(self, db_connection: Connection):
        self.db = db_connection
    
    # Get drivers with new LOGIN_EVENT in time window
    def get_new_login_candidates(
        self,
        city_code: str,
        time_window_minutes: int = 3,
        excluded_minutes: int = 120
    ) -> List[Dict[str, Any]]:
        """Get drivers with new LOGIN_EVENT in time window."""
        query = """
        SELECT DISTINCT t1.uuid, t1.latitude, t1.longitude, t1.ts
        FROM uber_activity_log_live t1
        WHERE t1.ts BETWEEN DATE_SUB(NOW(), INTERVAL %s MINUTE) AND NOW()
        AND t1.location = %s
        AND NOT EXISTS (
            SELECT 1
            FROM uber_activity_log_live t2
            WHERE t2.uuid = t1.uuid
            AND t2.location = %s
            AND t2.ts BETWEEN DATE_SUB(NOW(), INTERVAL %s MINUTE) AND DATE_SUB(NOW(), INTERVAL %s MINUTE)
        )
        """
        
        try:
            cursor = self.db.cursor()
            cursor.execute(query, (
                time_window_minutes,
                city_code,
                city_code,
                excluded_minutes,
                time_window_minutes,
            ))
            results = cursor.fetchall()
            cursor.close()
            return results if results else []
        except Exception as e:
            logger.error(f"Error querying new login candidates: {e}")
            return []
        
    # Get recent activity for specific statuses
    def get_activity_by_status(
        self,
        city_code: str,
        statuses: List[str],
        time_window_minutes: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent activity for specific statuses."""
        if not statuses:
            return []
        
        placeholders = ','.join(['%s'] * len(statuses))
        query = f"""
        SELECT DISTINCT uuid, latitude, longitude, status, ts
        FROM uber_activity_log_live
        WHERE location = %s
        AND status IN ({placeholders})
        AND ts BETWEEN DATE_SUB(NOW(), INTERVAL %s MINUTE) AND NOW()
        ORDER BY uuid, ts DESC
        """
        
        try:
            cursor = self.db.cursor()
            params = [city_code] + statuses + [time_window_minutes]
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results if results else []
        except Exception as e:
            logger.error(f"Error querying activity by status: {e}")
            return []


# Repository for querying users table
class UserRepository:
    """Query users table for notification delivery."""
    
    # Initialize with a database connection
    def __init__(self, db_connection: Connection):
        self.db = db_connection
    
    # Get user info by UUID
    def get_user_by_uuid(self, uuid: str) -> Optional[Dict[str, Any]]:
        """Get user info for notification dispatch."""
        query = """
        SELECT uuid_id, first_name, telegram_id, telegram_language, 
               prefix, phone
        FROM users
        WHERE uuid_id = %s
        LIMIT 1
        """
        
        try:
            cursor = self.db.cursor()
            cursor.execute(query, (uuid,))
            row = cursor.fetchone()
            cursor.close()
            return row if row else None
        except Exception as e:
            logger.error(f"Error querying user {uuid}: {e}")
            return None
    
    # Get multiple users by UUID
    def get_users_by_uuids(self, uuids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple users by UUID."""
        if not uuids:
            return []
        
        placeholders = ','.join(['%s'] * len(uuids))
        query = f"""
        SELECT uuid_id, first_name, telegram_id, telegram_language, 
               prefix, phone
        FROM users
        WHERE uuid_id IN ({placeholders})
        """
        
        try:
            cursor = self.db.cursor()
            cursor.execute(query, uuids)
            rows = cursor.fetchall()
            cursor.close()
            return rows if rows else []
        except Exception as e:
            logger.error(f"Error querying multiple users: {e}")
            return []


# Repository for inserting warnings into uber_warnings table
class WarningRepository:
    """Insert warnings into uber_warnings."""
    
    # Initialize with a database connection
    def __init__(self, db_connection: Connection):
        self.db = db_connection
    
    # Insert a single warning
    def insert_warning(
        self,
        driver_id: str,
        note: str,
        city_code: str,
        check_name: str
    ) -> bool:
        """Insert a new warning record."""
        query = """
        INSERT INTO uber_warnings 
        (driver_id, note, city, check_name, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        """
        
        try:
            cursor = self.db.cursor()
            cursor.execute(query, (driver_id, note, city_code, check_name))
            self.db.commit()
            cursor.close()
            logger.debug(f"Inserted warning for {driver_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to insert warning for {driver_id}: {e}")
            try:
                self.db.rollback()
            except:
                pass
            return False
    
    # Insert multiple warnings in batch
    def insert_warnings_batch(self, warnings: List[Dict[str, str]]) -> int:
        """Insert multiple warnings in a batch."""
        if not warnings:
            return 0
        
        query = """
        INSERT INTO uber_warnings 
        (driver_id, note, city, check_name, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        """
        
        success_count = 0
        try:
            cursor = self.db.cursor()
            for warning in warnings:
                try:
                    cursor.execute(query, (
                        warning['driver_id'],
                        warning['note'],
                        warning['city_code'],
                        warning['check_name']
                    ))
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to insert warning: {e}")
            
            self.db.commit()
            cursor.close()
            logger.info(f"Inserted {success_count}/{len(warnings)} warnings")
            return success_count
        except Exception as e:
            logger.error(f"Error in batch insert: {e}")
            try:
                self.db.rollback()
            except:
                pass
            return success_count