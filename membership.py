"""Force join group and/or channel before using the bot."""

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from config import ADMIN_IDS
from database import get_setting


async def _check(bot: Bot, chat_id, user_id: int) -> bool:
    if not chat_id:
        return True
    try:
        chat_id = int(chat_id)
    except (TypeError, ValueError):
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.RESTRICTED,
        )
    except Exception:
        return False


async def is_member(bot: Bot, user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return True
    group_id = await get_setting("force_group_id", "") or ""
    channel_id = await get_setting("force_channel_id", "") or ""
    # fallback env
    from config import ESCROW_GROUP_ID
    if not group_id and ESCROW_GROUP_ID:
        group_id = str(ESCROW_GROUP_ID)

    if group_id and not await _check(bot, group_id, user_id):
        return False
    if channel_id and not await _check(bot, channel_id, user_id):
        return False
    return True


async def join_required_text() -> str:
    group_link = await get_setting("force_group_link", "")
    channel_link = await get_setting("force_channel_link", "")
    from config import ESCROW_GROUP_LINK
    if not group_link:
        group_link = ESCROW_GROUP_LINK or ""

    lines = ["<b>Join required</b>\n", "You must join our official group/channel before using this bot.\n"]
    if group_link:
        lines.append(f'Group: <a href="{group_link}">Join Group</a>')
    if channel_link:
        lines.append(f'Channel: <a href="{channel_link}">Join Channel</a>')
    if not group_link and not channel_link:
        lines.append("Ask admin for the invite link, then press /start again.")
    else:
        lines.append("\nAfter joining, press /start again.")
    return "\n".join(lines)
