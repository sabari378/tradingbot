from pydantic_settings import BaseSettings


class GatewaySettings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8100
    gateway_secret: str = ""
    mt5_mode: str = "DEMO"
    model_config = {"env_file": ".env"}
