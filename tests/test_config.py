import subprocess
import sys
from pathlib import Path

from core.config import get_config

ROOT = Path(__file__).resolve().parents[1]


def test_all_city_configs_load():
    cfg = get_config()
    assert cfg.cities, "Expected at least one city config"

    for city_dir in cfg.cities:
        city = cfg.get_city_config(city_dir)
        assert city is not None, f"Missing config for {city_dir}"
        assert city.city_code
        assert city.language.default in city.language.supported
        assert "login_check" in city.checks
        assert city.status.mapping
        assert city.status.groups


def test_test_city_resolves_by_code():
    cfg = get_config()
    city = cfg.get_city_config("TEST")
    assert city is not None
    assert city.city_code == "TEST"


def test_cli_config_validate_exits_zero():
    result = subprocess.run(
        [sys.executable, str(ROOT / "cli" / "main.py"), "config", "validate"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
