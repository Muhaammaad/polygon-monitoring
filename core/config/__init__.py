# core/config/__init__.py
import os
import json
import yaml
from yaml.constructor import ConstructorError
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, validator
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Pydantic models for type validation
# Define models for various configuration sections
# this class structure can be expanded as needed
class LanguageConfig(BaseModel):
    default: str
    supported: List[str]

# Status mapping model
class StatusMapping(BaseModel):
    mapping: Dict[str, str]
    groups: Dict[str, List[str]]
    unknown_policy: str = "log_and_skip"

# Check configuration model
class CheckConfig(BaseModel):
    enabled: bool
    time_window_minutes: Optional[int] = None
    status_group: str
    target_zone: Optional[str] = None
    allowed_zones: Optional[List[str]] = None
    excluded_minutes: Optional[int] = None

# Notification channel configuration model
class NotificationChannelConfig(BaseModel):
    enabled: bool = True

# City configuration model
class CityConfig(BaseModel):
    city_code: str
    language: LanguageConfig
    zones: List[str]
    status: StatusMapping
    checks: Dict[str, CheckConfig]
    notifications: Dict[str, Union[bool, NotificationChannelConfig]] = {
        "telegram": NotificationChannelConfig(enabled=True),
        "sms_fallback": NotificationChannelConfig(enabled=True)
    }

# Database configuration model
class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 3306
    user: str
    password: str
    name: str
    charset: str = "utf8mb4"

# Notification configuration model
class NotificationConfig(BaseModel):
    telegram_bot_token: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_from_number: str

# Main configuration class
class Config:
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._city_configs: Dict[str, CityConfig] = {}
        # map city_code -> city directory name
        self._city_code_map: Dict[str, str] = {}
        # Load environment variables from .env file
        load_dotenv()
        self._load_environment()
        self._load_city_configs()

    @staticmethod
    def _yaml_load_unique(stream):
        """Load YAML enforcing unique keys in mappings."""
        
        class UniqueKeyLoader(yaml.SafeLoader):
            pass
        
        def _construct_mapping_unique(loader, node, deep=False):
            if not isinstance(node, yaml.MappingNode):
                raise ConstructorError(
                    None, None, f"expected a mapping node, got {node.id}", node.start_mark
                )
            mapping = {}
            for key_node, value_node in node.value:
                key = loader.construct_object(key_node, deep=deep)
                if key in mapping:
                    raise ConstructorError(
                        "while constructing a mapping",
                        node.start_mark,
                        f"found duplicate key ({key})",
                        key_node.start_mark,
                    )
                value = loader.construct_object(value_node, deep=deep)
                mapping[key] = value
            return mapping
        
        UniqueKeyLoader.construct_mapping = _construct_mapping_unique
        return yaml.load(stream, Loader=UniqueKeyLoader)


    # Load environment variables into configuration
    def _load_environment(self):
        """Load configuration from environment variables."""
        self._config = {
            "database": {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "3306")),
                "user": os.getenv("DB_USER", "root"),
                "password": os.getenv("DB_PASSWORD", ""),
                "name": os.getenv("DB_NAME", "test"),
                "charset": "utf8mb4"
            },
            "notifications": {
                "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
                "telegram_it_channel_id": os.getenv("TELEGRAM_IT_CHANNEL_ID", ""),
                "twilio_account_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
                "twilio_auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
                "twilio_from_number": os.getenv("TWILIO_FROM_NUMBER", ""),
                "enable_sms_fallback": os.getenv("ENABLE_SMS_FALLBACK", "true").lower() == "true",
                "telegram_retry_count": int(os.getenv("TELEGRAM_RETRY_COUNT", "1"))
            },
            "logging": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "format": os.getenv("LOG_FORMAT", "json")
            },
            "app": {
                "env": os.getenv("APP_ENV", "production"),
                "scheduler_interval_minutes": int(os.getenv("SCHEDULER_INTERVAL", "3")),
                "default_time_window_minutes": int(os.getenv("DEFAULT_TIME_WINDOW_MINUTES", "3"))
            }
        }

    # Load city configurations from files
    def _load_city_configs(self):
        """Load all city configurations from the cities directory (supports YAML and JSON)."""
        cities_dir = Path(__file__).parent.parent.parent / "cities"
        if not cities_dir.exists():
            logger.warning(f"Cities directory not found: {cities_dir}")
            return

        for city_dir in cities_dir.iterdir():
            if not city_dir.is_dir():
                continue
                
            # Check for config file: prefer YAML, fall back to JSON
            config_file = None
            file_type = None
            
            if (city_dir / "config.yaml").exists():
                config_file = city_dir / "config.yaml"
                file_type = "yaml"
            elif (city_dir / "config.json").exists():
                config_file = city_dir / "config.json"
                file_type = "json"
            
            if config_file:
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        if file_type == "yaml":
                            city_config = self._yaml_load_unique(f)
                        else:  # json
                            city_config = json.load(f)
                        
                        # Validate the city config against the model
                        validated_config = CityConfig(**city_config)
                        self._city_configs[city_dir.name] = validated_config               
                        # register code -> dir mapping
                        try:
                            code = str(validated_config.city_code).upper()
                            self._city_code_map[code] = city_dir.name
                        except Exception:
                            pass
                        logger.info(f"Loaded {file_type.upper()} config for city: {city_dir.name}")
                except Exception as e:
                    logger.error(f"Error loading config for city {city_dir.name}: {e}")


    # Get configuration for a specific city
    def get_city_config(self, city_name_or_code: str) -> Optional[CityConfig]:
        """Get configuration for a specific city by directory name or city_code."""
        if city_name_or_code is None:
            return None

        # Direct lookup by directory key
        cfg = self._city_configs.get(city_name_or_code)
        if cfg:
            return cfg

        # Fallback: resolve by city_code mapping
        city_dir = self.resolve_city_dir_by_code(city_name_or_code)
        if city_dir:
            return self._city_configs.get(city_dir)
        return None


    # Resolve city directory by city code
    def resolve_city_dir_by_code(self, city_code: str) -> Optional[str]:
        """Resolve the city directory name by city_code (case-insensitive)."""
        if city_code is None:
            return None
        return self._city_code_map.get(str(city_code).upper())

    # Get all city configurations
    def get_city_configs(self) -> List[CityConfig]:
        """Return all loaded city configurations as a list."""
        return list(self._city_configs.values())

    # Get database configuration
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self._config.get("database", {})

    # Get notification configuration
    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification configuration."""
        return self._config.get("notifications", {})

    # Get logging configuration
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self._config.get("logging", {})

    # Get global default time window in minutes
    def get_default_time_window_minutes(self) -> int:
        """Get global default time window in minutes."""
        return self._config.get("app", {}).get("default_time_window_minutes", 3)

    # Resolve time window for a check
    def resolve_time_window(self, check_config: CheckConfig) -> int:
        """Resolve time window: use check config value if present, else fall back to global default."""
        if check_config.time_window_minutes is not None:
            return check_config.time_window_minutes
        return self.get_default_time_window_minutes()

    # Get list of available cities
    @property
    def cities(self) -> List[str]:
        """Get list of available cities."""
        return list(self._city_configs.keys())

    # Get list of available city codes
    @property
    def city_codes(self) -> List[str]:
        """Get list of available city codes (uppercased)."""
        return list(self._city_code_map.keys())

# Global config instance
config = Config()

# Helper function to get global config
def get_config() -> Config:
    """Get the global config instance."""
    return config