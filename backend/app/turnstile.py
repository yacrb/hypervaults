from fastapi import HTTPException, status
import httpx

from app.config import get_settings


settings = get_settings()
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
DEV_BYPASS_TOKEN = "dev-bypass-token"


async def verify_turnstile_token(token: str, remote_ip: str | None = None) -> None:
    if settings.turnstile_dev_bypass:
        # The bypass is explicit: it requires a dedicated env flag and a sentinel token.
        if token == DEV_BYPASS_TOKEN:
            return
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid local Turnstile bypass token")

    payload = {
        "secret": settings.turnstile_secret_key.get_secret_value(),
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(TURNSTILE_VERIFY_URL, data=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Turnstile verification unavailable") from exc

    result = response.json()
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Turnstile verification failed")
