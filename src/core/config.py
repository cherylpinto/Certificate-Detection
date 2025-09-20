import os
from pathlib import Path
from functools import lru_cache


class Config:
    """Central configuration for the project."""

    def __init__(self):
        # Application Info
        self.app_name = "Fake Certificate Authority"
        self.app_version = "0.1.0"
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        # Sub-Configs
        self.storage = self._create_storage_config()
        self.security = self._create_security_config()
        self.monitoring = self._create_monitoring_config()

    # Storage Config
    def _create_storage_config(self):
        class StorageConfig:
            data_dir = Path(os.getenv("DATA_DIR", "./data"))
            output_dir = Path(os.getenv("OUTPUT_DIR", "./outputs"))
            cache_dir = Path(os.getenv("CACHE_DIR", "./cache"))
            temp_dir = Path(os.getenv("TEMP_DIR", "./temp"))
            log_file = Path(os.getenv("LOG_FILE", "./logs/app.log"))
            database_url = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/db")

            def __post_init__(self):
                for d in [self.data_dir, self.output_dir, self.cache_dir, self.temp_dir, self.log_file.parent]:
                    d.mkdir(parents=True, exist_ok=True)

        config = StorageConfig()
        config.__post_init__()
        return config

    # Security Config
    def _create_security_config(self):
        class SecurityConfig:
            secret_key = os.getenv("SECRET_KEY", "dev_secret_key_change_in_prod")
            encrypt_credentials = os.getenv("ENCRYPT_CREDENTIALS", "true").lower() == "true"
            enable_rate_limiting = True
            audit_logging = True

        return SecurityConfig()

    # Monitoring Config
    def _create_monitoring_config(self):
        class MonitoringConfig:
            enable_metrics = os.getenv("ENABLE_METRICS", "true").lower() == "true"
            metrics_port = int(os.getenv("METRICS_PORT", "8080"))
            enable_health_check = os.getenv("ENABLE_HEALTH_CHECK", "true").lower() == "true"
            track_token_usage = True
            track_processing_time = True

        return MonitoringConfig()

    # Helpers
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"


# Singleton 
@lru_cache()
def get_settings() -> Config:
    return Config()


settings = get_settings()


def reload_settings() -> Config:
    """Reload settings (useful in dev)."""
    get_settings.cache_clear()
    global settings
    settings = get_settings()
    return settings
