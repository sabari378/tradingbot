from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8100
    gateway_secret: str = Field(
        default="",
        validation_alias=AliasChoices("GATEWAY_SECRET", "MT5_GATEWAY_SECRET"),
    )
    mt5_mode: str = "DEMO"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
