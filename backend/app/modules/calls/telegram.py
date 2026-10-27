import logging
from typing import Optional, Tuple
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_telegram_briefing(
    briefing_text: str,
    video_room_url: Optional[str] = None,
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Sends a caregiver briefing message via Telegram Bot API using httpx.
    Non-blocking: if network fails or tokens are invalid, records the failure
    and never crashes or halts the phone call.
    """
    token = bot_token or settings.TELEGRAM_BOT_TOKEN
    target_chat = chat_id or settings.TELEGRAM_CHAT_ID

    if not settings.FEATURE_TELEGRAM and not bot_token:
        return False, "disabled (FEATURE_TELEGRAM=False)"

    if not token or not target_chat:
        return False, "unconfigured (missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID)"

    text_to_send = briefing_text
    if video_room_url:
        text_to_send = f"{briefing_text}\n\n📹 Video Room: {video_room_url}"

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": text_to_send,
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(api_url, json=payload)
            if resp.status_code == 200:
                logger.info(f"Telegram caregiver briefing sent to chat {target_chat}.")
                return True, "sent"
            else:
                err_msg = f"Telegram error {resp.status_code}: {resp.text}"
                logger.warning(err_msg)
                return False, f"failed: HTTP {resp.status_code}"
    except Exception as e:
        logger.warning(f"Telegram request failed ({e}); non-blocking, proceeding with direct call.")
        return False, f"failed: {str(e)}"
