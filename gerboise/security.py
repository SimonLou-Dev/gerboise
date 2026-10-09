from fastapi import Header, HTTPException, status

from gerboise.config import settings


async def verify_api_key(authorization: str = Header(default="")) -> None:
    expected = f"Bearer {settings.api_key.get_secret_value()}"
    if authorization != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
