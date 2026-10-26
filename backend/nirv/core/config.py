from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .enums import ExecutionMode


class Settings(BaseSettings):
    app_env: str = "development"
    nirv_mode: ExecutionMode = ExecutionMode.PAPER
    database_url: str = "sqlite+aiosqlite:///./nirv.db"
    redis_url: str = "redis://localhost:6379/0"
    api_key: str = ""
    default_symbol: str = "XAUUSD"
    default_risk_percent: float = Field(default=0.25, ge=0)
    max_risk_percent: float = Field(default=0.5, ge=0)
    max_daily_loss_percent: float = Field(default=2.0, ge=0)
    min_risk_reward: float = Field(default=1.5, ge=0)
    max_open_trades: int = Field(default=1, ge=1)
    max_spread: float = Field(default=0.5, ge=0)
    max_signal_age_seconds: int = Field(default=300, ge=1)
    log_level: str = "INFO"
    mt5_gateway_url: str = "http://127.0.0.1:8100"
    mt5_gateway_secret: str = ""
    voice_trading_enabled: bool = False
    demo_trading_enabled: bool = False
    cors_origins: str = "http://127.0.0.1:3000,http://localhost:3000"
    data_dir: str = "backend/data"
    paper_session_duration_seconds: int = Field(default=3600, ge=60)
    demo_session_duration_seconds: int = Field(default=7200, ge=60)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
