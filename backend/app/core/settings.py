import os
from functools import lru_cache


def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    stripped = value.strip()
    return stripped if stripped else default


def _get_bool(name: str, default: bool) -> bool:
    raw = _get_env(name, "true" if default else "false")
    assert raw is not None
    return raw.lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    raw = _get_env(name)
    if raw is None:
        return default
    return int(raw)


def _get_csv(name: str, default: list[str]) -> list[str]:
    raw = _get_env(name)
    if raw is None:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


class AppSettings:
    def __init__(self) -> None:
        self.app_env = (_get_env("APP_ENV", "development") or "development").lower()
        self.app_title = (
            _get_env("APP_TITLE", "Music Platform Backend") or "Music Platform Backend"
        )
        self.app_version = _get_env("APP_VERSION", "1.0.0") or "1.0.0"
        self.secret_key = _get_env("SECRET_KEY", "dev-secret-key-change-me")
        self.admin_api_key = _get_env("ADMIN_API_KEY", "admin123") or "admin123"
        self.database_url = (
            _get_env("DATABASE_URL", "sqlite:///./music_platform.db")
            or "sqlite:///./music_platform.db"
        )
        self.database_echo = _get_bool("DATABASE_ECHO", False)
        self.db_pool_size = _get_int("DB_POOL_SIZE", 10)
        self.db_max_overflow = _get_int("DB_MAX_OVERFLOW", 20)
        self.db_pool_recycle = _get_int("DB_POOL_RECYCLE", 1800)
        self.db_pool_timeout = _get_int("DB_POOL_TIMEOUT", 30)
        self.docs_enabled = _get_bool("DOCS_ENABLED", self.app_env != "production")
        self.redoc_enabled = _get_bool("REDOC_ENABLED", False)
        self.cors_allow_credentials = _get_bool("CORS_ALLOW_CREDENTIALS", False)
        self.https_redirect = _get_bool("HTTPS_REDIRECT", self.app_env == "production")
        self.access_token_ttl_seconds = _get_int(
            "ACCESS_TOKEN_TTL_SECONDS",
            60 * 60 * 24,
        )
        self.max_upload_size_bytes = _get_int("MAX_UPLOAD_SIZE_BYTES", 10 * 1024 * 1024)
        self.log_level = _get_env("LOG_LEVEL", "INFO") or "INFO"
        self.rate_limit_per_minute = _get_int("RATE_LIMIT_PER_MINUTE", 60)
        self.recommendation_rate_limit_per_minute = _get_int(
            "RECOMMENDATION_RATE_LIMIT_PER_MINUTE",
            30,
        )
        self.redis_url = _get_env("REDIS_URL", "")
        self.recommendation_cache_ttl_seconds = _get_int(
            "RECOMMENDATION_CACHE_TTL_SECONDS",
            120,
        )
        self.trending_cache_ttl_seconds = _get_int(
            "TRENDING_CACHE_TTL_SECONDS",
            180,
        )
        self.youtube_trends_enabled = _get_bool("YOUTUBE_TRENDS_ENABLED", False)
        self.youtube_api_key = _get_env("YOUTUBE_API_KEY", "")
        self.youtube_region_default = _get_env("YOUTUBE_REGION_DEFAULT", "ET") or "ET"
        self.youtube_trends_max_results = _get_int("YOUTUBE_TRENDS_MAX_RESULTS", 25)
        self.youtube_trends_ttl_seconds = _get_int("YOUTUBE_TRENDS_TTL_SECONDS", 900)

        default_hosts = ["localhost", "127.0.0.1", "testserver"]
        default_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
        self.allowed_hosts = _get_csv("ALLOWED_HOSTS", default_hosts)
        self.allowed_origins = _get_csv("ALLOWED_ORIGINS", default_origins)

        self._validate()

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def _validate(self) -> None:
        valid_envs = {"development", "testing", "production"}
        if self.app_env not in valid_envs:
            raise ValueError(f"APP_ENV must be one of {sorted(valid_envs)}")

        if self.max_upload_size_bytes <= 0:
            raise ValueError("MAX_UPLOAD_SIZE_BYTES must be greater than 0")

        if self.access_token_ttl_seconds <= 0:
            raise ValueError("ACCESS_TOKEN_TTL_SECONDS must be greater than 0")

        if self.db_pool_size <= 0:
            raise ValueError("DB_POOL_SIZE must be greater than 0")

        if self.db_max_overflow < 0:
            raise ValueError("DB_MAX_OVERFLOW must be greater than or equal to 0")

        if self.db_pool_timeout <= 0:
            raise ValueError("DB_POOL_TIMEOUT must be greater than 0")

        if self.db_pool_recycle <= 0:
            raise ValueError("DB_POOL_RECYCLE must be greater than 0")

        if self.rate_limit_per_minute <= 0:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be greater than 0")

        if self.recommendation_rate_limit_per_minute <= 0:
            raise ValueError("RECOMMENDATION_RATE_LIMIT_PER_MINUTE must be greater than 0")

        if self.recommendation_cache_ttl_seconds <= 0:
            raise ValueError("RECOMMENDATION_CACHE_TTL_SECONDS must be greater than 0")

        if self.trending_cache_ttl_seconds <= 0:
            raise ValueError("TRENDING_CACHE_TTL_SECONDS must be greater than 0")

        if self.youtube_trends_max_results <= 0:
            raise ValueError("YOUTUBE_TRENDS_MAX_RESULTS must be greater than 0")

        if self.youtube_trends_ttl_seconds <= 0:
            raise ValueError("YOUTUBE_TRENDS_TTL_SECONDS must be greater than 0")

        if self.is_production:
            if self.secret_key == "dev-secret-key-change-me":
                raise ValueError(
                    "SECRET_KEY must be set to a strong value in production"
                )
            if self.admin_api_key == "admin123":
                raise ValueError("ADMIN_API_KEY must be changed in production")
            if not self.is_postgres:
                raise ValueError("Production requires a PostgreSQL DATABASE_URL")
            if not self.allowed_hosts:
                raise ValueError("ALLOWED_HOSTS must be configured in production")
            if not self.allowed_origins:
                raise ValueError("ALLOWED_ORIGINS must be configured in production")


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
