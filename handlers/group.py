from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from config import ADMIN_IDS
from database import create_deal, add_user, get_fee
from locales import t

router = Router()


@router.message(Command("deal"), F.chat.type.in_({"group", "supergroup"}))
async def group_create_deal(message: Message):
    """
    Usage in group:
    /deal @seller 1500 USDT TRC20 Selling account
    or reply to a user: /deal 1500 INR (UPI) Product name
    """
    if message.from_user.id not in ADMIN_IDS and False:  # allow all for now, or restrict
        pass

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(
            "Usage:\n"
            "/deal @username amount currency description\n"
            "or reply to user:\n"
            "/deal amount currency description"
        )
        return

    text = args[1]
    seller_id = None

    # If reply
    if message.reply_to_message and message.reply_to_message.from_user:
        seller_id = message.reply_to_message.from_user.id
        parts = text.split(maxsplit=2)
    else:
        # Try to parse @username or ID first
        parts = text.split(maxsplit=3)
        if parts[0].startswith("@"):
            # username - we can't resolve easily without extra API, ask for ID
            await message.reply("Please use User ID or reply to the user message.\nExample: /deal 1500 USDT TRC20 desc")
            return
        try:
            seller_id = int(parts[0])
            parts = parts[1:]
        except ValueError:
            await message.reply("Invalid format. Reply to user or use numeric ID.")
            return

    if len(parts) < 2:
        await message.reply("Need: amount currency description")
        return

    try:
        amount = float(parts[0].replace(",", "."))
    except ValueError:
        await message.reply("Invalid amount")
        return

    currency = parts[1]
    description = parts[2] if len(parts) > 2 else "Group deal"

    # Detect type
    deal_type = "inr" if "INR" in currency.upper() or "UPI" in currency.upper() else "crypto"

    buyer_id = message.from_user.id
    if seller_id == buyer_id:
        await message.reply("Cannot deal with yourself")
        return

    await add_user(buyer_id, message.from_user.username, message.from_user.full_name)
    if message.reply_to_message:
        u = message.reply_to_message.from_user
        await add_user(seller_id, u.username, u.full_name)

    escrowed_by = "@Middleman"
    try:
        me = await message.bot.get_me()
        escrowed_by = f"@{me.username}" if me.username else "@Middleman"
    except Exception:
        pass

    deal_id = await create_deal(
        buyer_id, seller_id, amount, currency, description,
        deal_type=deal_type, group_id=message.chat.id,
        escrowed_by=escrowed_by
    )

    from formatters import deal_card
    from database import get_deal
    deal = await get_deal(deal_id)
    card = await deal_card(
        deal,
        buyer_name=message.from_user.full_name,
        seller_name=f'<a href="tg://user?id={seller_id}">User</a>'
    )
    await message.reply(card, parse_mode="HTML")

    for aid in ADMIN_IDS:
        try:
            await message.bot.send_message(aid, f"🆕 Group Deal\n\n{card}", parse_mode="HTML")
        except Exception:
            pass
    try:
        from logger import log_deal_created
        await log_deal_created(message.bot, deal)
    except Exception:
        pass

