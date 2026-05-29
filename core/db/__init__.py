# core/__init__.py
# This file makes the core directory a Python package
from .database import get_db, close_db, execute_query

# Expose key database functions

__all__ = ['get_db', 'close_db', 'execute_query']