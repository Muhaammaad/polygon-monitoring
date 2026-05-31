import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "db_seed"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Keep tests offline unless explicitly configured.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "dummy")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "dummy")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "dummy")
os.environ.setdefault("TWILIO_FROM_NUMBER", "+41000000000")


def _split_sql_statements(sql: str):
    for chunk in sql.split(";"):
        statement = chunk.strip()
        if statement and not all(
            line.strip().startswith("--") or not line.strip() for line in statement.splitlines()
        ):
            yield statement


@pytest.fixture(scope="session")
def ensure_schema():
    """Create integration-test tables when MySQL is available."""
    try:
        from core.db.database import close_db, get_db

        close_db()
        conn = get_db()
        schema = (FIXTURES / "schema.sql").read_text(encoding="utf-8")
        with conn.cursor() as cursor:
            for statement in _split_sql_statements(schema):
                cursor.execute(statement)
        conn.commit()
        close_db()
    except Exception:
        pass
    yield


@pytest.fixture
def db_conn(ensure_schema):
    """Yield a live DB connection or skip when MySQL is unavailable."""
    try:
        from core.db.database import close_db, get_db

        close_db()
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        yield conn
    except Exception as exc:
        pytest.skip(f"MySQL not available: {exc}")
    finally:
        try:
            from core.db.database import close_db

            close_db()
        except Exception:
            pass
