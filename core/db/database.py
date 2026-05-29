# core/db/database.py
import os
import pymysql
from typing import Any, Dict, Optional, List, Union
from pymysql.connections import Connection
from core.config import get_config

# Database connection helper
def get_db_connection() -> Connection:
    """Create and return a new database connection."""
    config = get_config().get_database_config()
    return pymysql.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['name'],
        charset=config['charset'],
        cursorclass=pymysql.cursors.DictCursor
    )


# Global connection pool
_db_connection: Optional[Connection] = None


# Database connection pool manager
def get_db() -> Connection:
    """Get a database connection from the pool."""
    global _db_connection
    try:
        # If connection is None or closed, reconnect
        if _db_connection is None or not _db_connection.open:
            _db_connection = get_db_connection()
        else:
            # Ping the connection to ensure it's alive; reconnect if not
            try:
                _db_connection.ping(reconnect=True)
            except Exception:
                _db_connection = get_db_connection()
    except Exception as e:
        # Log and raise for visibility
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Database reconnection failed: {e}")
        raise
    return _db_connection

# Close database connection
def close_db() -> None:
    """Close the database connection."""
    global _db_connection
    if _db_connection is not None:
        _db_connection.close()
        _db_connection = None

# Execute a database query
def execute_query(query: str, params: Optional[Union[tuple, List[tuple]]] = None) -> Any:
    """Execute a query and return the result."""
    connection = get_db()
    try:
        with connection.cursor() as cursor:
            # Handle multiple queries in one call
            if isinstance(query, list):
                results = []
                for q, p in zip(query, params or []):
                    cursor.execute(q, p or ())
                    if q.strip().upper().startswith('SELECT'):
                        results.append(cursor.fetchall())
                    else:
                        connection.commit()
                        results.append(cursor.lastrowid)
                return results
            # Single query
            else:
                cursor.execute(query, params or ())
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                connection.commit()
                return cursor.lastrowid
    except Exception as e:
        connection.rollback()
        raise e