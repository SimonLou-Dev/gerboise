import logging

import httpx

from gerboise.schemas import ClickPayload

logger = logging.getLogger(__name__)


async def relay_click(callback_url: str, payload: ClickPayload) -> None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(callback_url, json=payload.model_dump(mode="json"))
            response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("Failed to relay button click to %s", callback_url)
