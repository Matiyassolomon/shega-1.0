# apps/payments/config.py - Pydantic Settings with env validation
from functools import lru_cache
from typing import Optional, List
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class PaymentSettings(BaseSettings):
    \"\"\"
    Payment module configuration using Pydantic Settings.
    All sensitive values loaded from environment variables.
    \"\"\"
    model_config = ConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'  # Allow extra env vars not defined here
    )
    
    # Database Configuration
    database_url: str = Field(
        default=\"postgresql://postgres:postgres@localhost:5432/shega_payments\",
        alias=\"DATABASE_URL\"
    )
    db_pool_size: int = Field(default=10, alias=\"DB_POOL_SIZE\")
    db_max_overflow: int = Field(default=20, alias=\"DB_MAX_OVERFLOW\")
    db_pool_timeout: int = Field(default=30, alias=\"DB_POOL_TIMEOUT\")
    
    # Application Settings
    app_name: str = Field(default=\"Shega Payments\", alias=\"APP_NAME\")
    debug: bool = Field(default=False, alias=\"DEBUG\")
    environment: str = Field(default=\"production\", alias=\"ENVIRONMENT\")
    
    # Security
    secret_key: str = Field(alias=\"SECRET_KEY\")  # Required, no default
    webhook_secret: Optional[str] = Field(default=None, alias=\"WEBHOOK_SECRET\")
    
    # Provider API Keys (No hardcoded defaults)
    # Telebirr
    telebirr_app_id: Optional[str] = Field(default=None, alias=\"TELEBIRR_APP_ID\")
    telebirr_app_key: Optional[str] = Field(default=None, alias=\"TELEBIRR_APP_KEY\")
    telebirr_private_key: Optional[str] = Field(default=None, alias=\"TELEBIRR_PRIVATE_KEY\")
    telebirr_public_key: Optional[str] = Field(default=None, alias=\"TELEBIRR_PUBLIC_KEY\")
    telebirr_base_url: str = Field(default=\"https://api.telebirr.com\", alias=\"TELEBIRR_BASE_URL\")
    
    # Chapa
    chapa_secret_key: Optional[str] = Field(default=None, alias=\"CHAPA_SECRET_KEY\")
    chapa_public_key: Optional[str] = Field(default=None, alias=\"CHAPA_PUBLIC_KEY\")
    chapa_base_url: str = Field(default=\"https://api.chapa.co\", alias=\"CHAPA_BASE_URL\")
    
    # CBE Bank
    cbe_merchant_id: Optional[str] = Field(default=None, alias=\"CBE_MERCHANT_ID\")
    cbe_api_key: Optional[str] = Field(default=None, alias=\"CBE_API_KEY\")
    cbe_private_key: Optional[str] = Field(default=None, alias=\"CBE_PRIVATE_KEY\")
    
    # Feature Flags
    enable_webhooks: bool = Field(default=True, alias=\"ENABLE_WEBHOOKS\")
    enable_refunds: bool = Field(default=True, alias=\"ENABLE_REFUNDS\")
    auto_capture: bool = Field(default=True, alias=\"AUTO_CAPTURE\")
    
    # Provider Availability
    enabled_providers: List[str] = Field(
        default_factory=lambda: [\"telebirr\", \"chapa\", \"cbe_bank\"],
        alias=\"ENABLED_PROVIDERS\"
    )
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(\"SECRET_KEY must be at least 32 characters\")
        return v
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {'development', 'staging', 'production'}
        if v.lower() not in allowed:
            raise ValueError(f\"Environment must be one of: {allowed}\")
        return v.lower()
    
    @property
    def is_development(self) -> bool:
        return self.environment == 'development'
    
    @property
    def is_production(self) -> bool:
        return self.environment == 'production'
    
    @property
    def telebirr_enabled(self) -> bool:
        return all([
            self.telebirr_app_id,
            self.telebirr_app_key,
            \"telebirr\" in self.enabled_providers
        ])
    
    @property
    def chapa_enabled(self) -> bool:
        return all([
            self.chapa_secret_key,
            \"chapa\" in self.enabled_providers
        ])
    
    def get_provider_config(self, provider: str) -> dict:
        \"\"\"Get configuration for specific provider.\"\"\"
        configs = {
            \"telebirr\": {
                \"app_id\": self.telebirr_app_id,
                \"app_key\": self.telebirr_app_key,
                \"private_key\": self.telebirr_private_key,
                \"public_key\": self.telebirr_public_key,
                \"base_url\": self.telebirr_base_url,
            },
            \"chapa\": {
                \"secret_key\": self.chapa_secret_key,
                \"public_key\": self.chapa_public_key,
                \"base_url\": self.chapa_base_url,
            },
            \"cbe_bank\": {
                \"merchant_id\": self.cbe_merchant_id,
                \"api_key\": self.cbe_api_key,
                \"private_key\": self.cbe_private_key,
            }
        }
        return configs.get(provider, {})


@lru_cache()
def get_settings() -> PaymentSettings:
    \"\"\"
    Get cached settings instance.
    Settings are loaded once and cached for performance.
    \"\"\"
    return PaymentSettings()


def reload_settings() -> PaymentSettings:
    \"\"\"
    Force reload of settings (useful for testing).
    \"\"\"
    get_settings.cache_clear()
    return get_settings()
