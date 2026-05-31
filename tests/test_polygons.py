import subprocess
import sys
from pathlib import Path

import pytest

from core.polygons.polygon_registry import get_polygon_registry, reset_polygon_registry

ROOT = Path(__file__).resolve().parents[1]
CITIES_DIR = str(ROOT / "cities")


@pytest.fixture(autouse=True)
def _reset_registry():
    reset_polygon_registry()
    yield
    reset_polygon_registry()


def test_test_city_login_zone_point_containment():
    registry = get_polygon_registry()
    registry.load_city("TEST", cities_base_path=CITIES_DIR, city_dir_name="test_city")

    # Inside simple_login_zone.csv bounds
    assert registry.contains_point("TEST", "login_zone", 46.5200, 6.6200)
    # Outside login zone
    assert not registry.contains_point("TEST", "login_zone", 46.5200, 6.7000)


def test_cli_polygons_validate_exits_zero():
    result = subprocess.run(
        [sys.executable, str(ROOT / "cli" / "main.py"), "polygons", "validate"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
