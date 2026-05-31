from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.checks.login_check import LoginCheck
from core.config import get_config
from core.polygons.polygon_registry import get_polygon_registry, reset_polygon_registry

ROOT = Path(__file__).resolve().parents[1]
CITIES_DIR = str(ROOT / "cities")

LOGIN_UUIDS = ("uuid-login-in", "uuid-login-out", "uuid-login-old")
EXPECTED = {
    "uuid-login-in": "login_inside_zone",
    "uuid-login-out": "login_outside_zone",
}


@pytest.fixture(autouse=True)
def _reset_registry():
    reset_polygon_registry()
    yield
    reset_polygon_registry()


def test_login_check_evaluate_inside_and_outside():
    city = get_config().get_city_config("TEST")
    assert city is not None

    registry = get_polygon_registry()
    registry.load_city("TEST", cities_base_path=CITIES_DIR, city_dir_name="test_city")
    check = LoginCheck(db_conn=MagicMock(), polygon_registry=registry)

    inside = {
        "uuid": "uuid-login-in",
        "latitude": 46.5200,
        "longitude": 6.6200,
        "location": "TEST",
    }
    outside = {
        "uuid": "uuid-login-out",
        "latitude": 46.5200,
        "longitude": 6.7000,
        "location": "TEST",
    }

    assert check.evaluate(inside, city) == "login_inside_zone"
    assert check.evaluate(outside, city) == "login_outside_zone"


def test_login_check_integration(db_conn):
    """Run login_check against seeded TEST fixtures when MySQL is available."""
    from core.db.database import close_db

    fixtures = ROOT / "tests" / "fixtures" / "db_seed"
    for sql_file in ("seed_users_simple.sql", "seed_login_check_simple.sql"):
        sql = (fixtures / sql_file).read_text(encoding="utf-8")
        with db_conn.cursor() as cursor:
            for statement in _split_sql_statements(sql):
                cursor.execute(statement)
        db_conn.commit()

    try:
        city = get_config().get_city_config("TEST")
        registry = get_polygon_registry()
        registry.load_city("TEST", cities_base_path=CITIES_DIR, city_dir_name="test_city")

        check = LoginCheck(db_conn=db_conn, polygon_registry=registry)
        results = check.execute(city)
        by_uuid = {row["uuid"]: row["note"] for row in results}

        for uuid, note in EXPECTED.items():
            assert by_uuid.get(uuid) == note, f"{uuid}: expected {note}, got {by_uuid.get(uuid)}"
        assert "uuid-login-old" not in by_uuid
    finally:
        cleanup = (fixtures / "cleanup_simple.sql").read_text(encoding="utf-8")
        with db_conn.cursor() as cursor:
            for statement in _split_sql_statements(cleanup):
                cursor.execute(statement)
        db_conn.commit()
        close_db()


def _split_sql_statements(sql: str):
    for chunk in sql.split(";"):
        statement = chunk.strip()
        if statement and not all(
            line.strip().startswith("--") or not line.strip() for line in statement.splitlines()
        ):
            yield statement
