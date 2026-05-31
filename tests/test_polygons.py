import subprocess
import sys
from pathlib import Path

import pytest

from core.config import get_config
from core.polygons import get_polygon_manager, load_all_cities, reload_polygon_manager
from core.polygons.polygon_registry import get_polygon_registry, reset_polygon_registry

ROOT = Path(__file__).resolve().parents[1]
CITIES_DIR = str(ROOT / "cities")


@pytest.fixture(autouse=True)
def _reset_registry():
    reset_polygon_registry()
    yield
    reset_polygon_registry()


def test_load_all_cities_loads_configured_cities():
    registry = load_all_cities()
    cfg = get_config()

    assert registry is get_polygon_registry()
    for city_dir in cfg.cities:
        city = cfg.get_city_config(city_dir)
        assert city is not None
        assert city.city_code in registry.get_loaded_cities()
        assert registry.get_zone_polygon_count(city.city_code, city.zones[0]) > 0


def test_get_polygon_manager_is_backward_compatible_alias():
    manager = get_polygon_manager()
    registry = get_polygon_registry()

    assert manager is registry
    assert "TEST" in registry.get_loaded_cities()


def test_reload_polygon_manager_resets_shared_registry():
    first = get_polygon_manager()
    assert first.get_loaded_cities()

    reloaded = reload_polygon_manager()

    assert reloaded is get_polygon_registry()
    assert reloaded is not first
    assert "TEST" in reloaded.get_loaded_cities()


def test_geneva_multi_column_wkt_csv_loads():
    registry = get_polygon_registry()
    registry.load_city("GE", cities_base_path=CITIES_DIR, city_dir_name="geneva")

    names = [p["name"] for p in registry.get_polygon_details("GE", "login_zone")]
    assert "Geneva Login Zone" in names


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
