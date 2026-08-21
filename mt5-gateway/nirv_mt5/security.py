from fastapi import Header, HTTPException

from .config import GatewaySettings


def validate_secret(settings: GatewaySettings, x_nirv_signature: str | None) -> None:
    if not settings.gateway_secret or x_nirv_signature != settings.gateway_secret:
        raise HTTPException(401, "invalid gateway signature")


def gateway_auth(settings: GatewaySettings):
    async def dependency(x_nirv_signature: str | None = Header(default=None)) -> None:
        validate_secret(settings, x_nirv_signature)

    return dependency
