"""Logging: completed deals → completed channel (or log channel). Vouches → vouch channel."""

import logging
from database import get_setting
from config import ADMIN_IDS, LOG_CHANNEL_ID, VOUCH_CHANNEL_ID
from formatters import completed_card

log = logging.getLogger("escrow.logger")


async def _resolve_channel(key: str, env_fallback=None):
    val = await get_setting(key, "")
    if val:
        try:
            return int(val)
        except ValueError:
            pass
    return env_fallback


async def _send(bot, chat_id, text: str, retries: int = 3) -> bool:
    if not chat_id:
        log.warning("No channel id for log")
        return False
    for attempt in range(retries):
        try:
            await bot.send_message(int(chat_id), text, parse_mode="HTML")
            return True
        except Exception as e:
            log.warning("Log send fail %s/%s: %s", attempt + 1, retries, e)
    for aid in ADMIN_IDS:
        try:
            await bot.send_message(aid, f"Log delivery failed\n\n{text[:400]}", parse_mode="HTML")
            break
        except Exception:
            pass
    return False


async def log_deal_completed(bot, deal: dict):
    # Prefer dedicated completed channel, else log channel
    ch = await _resolve_channel("completed_channel_id")
    if not ch:
        ch = await _resolve_channel("log_channel_id", LOG_CHANNEL_ID)
    text = completed_card(deal)
    ok = await _send(bot, ch, text)
    log.info("Completed deal #%s logged=%s to %s", deal.get("id"), ok, ch)


async def log_vouch(bot, text: str):
    ch = await _resolve_channel("vouch_channel_id", VOUCH_CHANNEL_ID)
    if not ch:
        ch = await _resolve_channel("log_channel_id", LOG_CHANNEL_ID)
    await _send(bot, ch, text)


async def log_event(bot, text: str):
    """General events → logs channel."""
    ch = await _resolve_channel("log_channel_id", LOG_CHANNEL_ID)
    await _send(bot, ch, text)


async def log_deal_created(bot, deal): pass
async def log_payment_set(bot, deal): pass
async def log_payment_confirmed(bot, deal): pass
async def log_deal_refunded(bot, deal): pass
async def log_deal_disputed(bot, deal, by_user=None): pass
async def log_deal_cancelled(bot, deal): pass
