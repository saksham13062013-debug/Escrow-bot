from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS
from database import (
    add_user, get_user, is_banned, create_deal, get_deal, get_user_deals,
    get_fee, is_maintenance, get_setting, set_user_lang, update_deal_status,
    get_stats, get_deals_by_status
)
from keyboards import (
    main_menu_kb, lang_kb, role_kb, deal_type_kb, currencies_kb,
    deal_actions_kb, accept_deal_kb, vouch_kb, nav_kb
)
from locales import t
from formatters import deal_card, mention, completed_card, vouch_post

router = Router()


class CreateDeal(StatesGroup):
    waiting_role = State()
    waiting_other = State()
    waiting_type = State()
    waiting_amount = State()
    waiting_currency = State()
    waiting_description = State()
    waiting_time = State()
    waiting_terms = State()


class VouchState(StatesGroup):
    waiting_text = State()


def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


async def get_lang(user_id: int) -> str:
    user = await get_user(user_id)
    return user["language"] if user else "en"


async def resolve_user_id(text: str, bot) -> int | None:
    """Resolve @username or numeric ID to user_id."""
    text = (text or "").strip()
    if text.startswith("@"):
        try:
            chat = await bot.get_chat(text)
            return chat.id
        except Exception:
            return None
    try:
        return int(text)
    except ValueError:
        return None


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await add_user(user.id, user.username, user.full_name)

    if await is_banned(user.id):
        await message.answer("⛔ You are banned from this service.")
        return

    from membership import is_member, join_required_text
    if not await is_member(message.bot, user.id):
        await message.answer(join_required_text(), parse_mode="HTML", disable_web_page_preview=True)
        return

    if await is_maintenance() and not is_admin(user.id):
        support = await get_setting("support_contact", "@support")
        await message.answer(f"🔧 Service under maintenance.\nSupport: {support}")
        return

    lang = await get_lang(user.id)
    text = (
        f"🛡 <b>SMOOTH ESCROW SERVICE</b>\n\n"
        f"Welcome {mention(user.id, user.first_name)}!\n\n"
        f"Trusted middleman for Crypto & INR deals.\n"
        f"Use the menu below to get started."
    )
    await message.answer(text, reply_markup=main_menu_kb(lang, is_admin(user.id)), parse_mode="HTML")


@router.callback_query(F.data == "nav_home")
async def nav_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    lang = await get_lang(callback.from_user.id)
    await callback.message.answer(
        "🏠 Home",
        reply_markup=main_menu_kb(lang, is_admin(callback.from_user.id))
    )
    await callback.answer()


@router.callback_query(F.data == "nav_cancel")
async def nav_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    lang = await get_lang(callback.from_user.id)
    await callback.message.edit_text("❌ Cancelled.")
    await callback.message.answer(
        "Home menu:",
        reply_markup=main_menu_kb(lang, is_admin(callback.from_user.id))
    )
    await callback.answer()


@router.message(F.text.in_(["Language", "🌐 Language"]))
async def change_lang(message: Message):
    await message.answer("Choose language:", reply_markup=lang_kb())


@router.callback_query(F.data.startswith("setlang:"))
async def set_lang(callback: CallbackQuery):
    lang = callback.data.split(":")[1]
    await set_user_lang(callback.from_user.id, lang)
    await callback.message.edit_text("✅ Language updated.")
    await callback.message.answer(
        "Menu:",
        reply_markup=main_menu_kb(lang, is_admin(callback.from_user.id))
    )
    await callback.answer()


@router.message(F.text.in_(["How it works", "ℹ️ How it works"]))
async def how_it_works(message: Message):
    fee = await get_fee()
    support = await get_setting("support_contact", "@support")
    text = (
        f"🛡 <b>SMOOTH ESCROW SERVICE</b>\n\n"
        f"1. Create a deal (Buyer or Seller)\n"
        f"2. Other party accepts\n"
        f"3. Middleman shares payment details\n"
        f"4. Buyer pays → Middleman confirms\n"
        f"5. Seller delivers → Buyer confirms\n"
        f"6. Middleman releases funds\n\n"
        f"<b>Fee:</b> {fee}%\n"
        f"<b>Support:</b> {support}\n\n"
        f"Always /verify addresses & UPI before paying."
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "Escrow Global Stats")
async def global_stats(message: Message):
    stats = await get_stats()
    fee = await get_fee()
    text = (
        f"📊 <b>SMOOTH ESCROW — Global Stats</b>\n\n"
        f"👥 Users: {stats['users']}\n"
        f"📦 Total Deals: {stats['total_deals']}\n"
        f"🔄 Active: {stats['active']}\n"
        f"✅ Completed: {stats['completed']}\n"
        f"⚠️ Disputed: {stats['disputed']}\n"
        f"💰 Volume: {stats['volume']}\n"
        f"⚙️ Fee: {fee}%"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "My Stats")
async def my_stats(message: Message):
    deals = await get_user_deals(message.from_user.id)
    completed = sum(1 for d in deals if d["status"] == "completed")
    active = sum(1 for d in deals if d["status"] not in ("completed", "refunded", "cancelled"))
    text = (
        f"💎 <b>Your Stats</b>\n\n"
        f"Total deals: {len(deals)}\n"
        f"Active: {active}\n"
        f"Completed: {completed}"
    )
    await message.answer(text, parse_mode="HTML")


# ---------- CREATE DEAL ----------

@router.message(F.text == "Create Deal")
async def create_deal_start(message: Message, state: FSMContext):
    if await is_banned(message.from_user.id):
        return
    from membership import is_member, join_required_text
    if not await is_member(message.bot, message.from_user.id):
        await message.answer(join_required_text(), parse_mode="HTML", disable_web_page_preview=True)
        return
    await state.set_state(CreateDeal.waiting_role)
    await message.answer(
        "🛡 <b>SMOOTH ESCROW — Create Deal</b>\n\nAre you the <b>Buyer</b> or <b>Seller</b>?",
        reply_markup=role_kb(),
        parse_mode="HTML"
    )


@router.callback_query(CreateDeal.waiting_role, F.data.startswith("role:"))
async def process_role(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split(":")[1]
    await state.update_data(my_role=role)
    await state.set_state(CreateDeal.waiting_other)
    await callback.message.edit_text(
        "Send the other party's <b>@username</b> or numeric User ID.\n\n"
        "Example: @username  or  123456789",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(CreateDeal.waiting_other)
async def process_other(message: Message, state: FSMContext):
    other_id = await resolve_user_id(message.text, message.bot)
    if not other_id:
        await message.answer("Could not resolve user. Send @username or numeric ID.")
        return
    if other_id == message.from_user.id:
        await message.answer("You cannot create a deal with yourself.")
        return
    await state.update_data(other_id=other_id)
    await state.set_state(CreateDeal.waiting_type)
    await message.answer("Choose deal type:", reply_markup=deal_type_kb())


@router.callback_query(CreateDeal.waiting_type, F.data.startswith("dealtype:"))
async def process_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(deal_type=callback.data.split(":")[1])
    await state.set_state(CreateDeal.waiting_amount)
    await callback.message.edit_text("Enter deal amount (e.g. 1500 or 99.50):")
    await callback.answer()


@router.message(CreateDeal.waiting_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(",", "."))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Enter a valid positive number.")
        return
    await state.update_data(amount=amount)
    data = await state.get_data()
    await state.set_state(CreateDeal.waiting_currency)
    await message.answer("Choose currency:", reply_markup=currencies_kb(data.get("deal_type", "crypto")))


@router.callback_query(CreateDeal.waiting_currency, F.data.startswith("currency:"))
async def process_currency(callback: CallbackQuery, state: FSMContext):
    await state.update_data(currency=callback.data.split(":", 1)[1])
    await state.set_state(CreateDeal.waiting_description)
    await callback.message.edit_text("Write a short description of the deal:")
    await callback.answer()


@router.message(CreateDeal.waiting_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(CreateDeal.waiting_time)
    await message.answer("Expected time? (e.g. 5 min / 1 hour)\nSend /skip to skip")


@router.message(CreateDeal.waiting_time)
async def process_time(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(expected_time=None if text.lower() == "/skip" else text)
    await state.set_state(CreateDeal.waiting_terms)
    await message.answer("Terms & Conditions (T/C)?\nSend /skip to skip")


@router.message(CreateDeal.waiting_terms)
async def process_terms(message: Message, state: FSMContext):
    terms = None if message.text.strip().lower() == "/skip" else message.text.strip()
    data = await state.get_data()
    my_role = data.get("my_role", "buyer")
    other_id = data["other_id"]
    amount = data["amount"]
    currency = data["currency"]
    deal_type = data.get("deal_type", "crypto")
    description = data.get("description", "")
    expected_time = data.get("expected_time")

    if my_role == "buyer":
        buyer_id, seller_id = message.from_user.id, other_id
    else:
        buyer_id, seller_id = other_id, message.from_user.id

    escrowed_by = "SMOOTH ESCROW"
    try:
        me = await message.bot.get_me()
        if me.username:
            escrowed_by = f"@{me.username}"
    except Exception:
        pass

    deal_id = await create_deal(
        buyer_id, seller_id, amount, currency, description, deal_type,
        expected_time=expected_time, terms=terms, escrowed_by=escrowed_by
    )
    await state.clear()

    deal = await get_deal(deal_id)
    card = await deal_card(deal)
    lang = await get_lang(message.from_user.id)
    await message.answer(card, parse_mode="HTML", reply_markup=main_menu_kb(lang, is_admin(message.from_user.id)))

    # Notify other party with accept/reject
    try:
        await message.bot.send_message(
            other_id,
            f"🔔 New deal invitation\n\n{card}\n\nAccept or reject:",
            parse_mode="HTML",
            reply_markup=accept_deal_kb(deal_id)
        )
    except Exception:
        await message.answer(
            f"Could not DM the other party. Ask them to /start the bot first.\n"
            f"Their ID: <code>{other_id}</code>",
            parse_mode="HTML"
        )

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"🆕 New Deal\n\n{card}",
                parse_mode="HTML",
                reply_markup=deal_actions_kb(deal_id, "admin")
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("accept_deal:"))
async def accept_deal(callback: CallbackQuery):
    deal_id = int(callback.data.split(":")[1])
    deal = await get_deal(deal_id)
    if not deal:
        await callback.answer("Deal not found", show_alert=True)
        return
    uid = callback.from_user.id
    if uid not in (deal["buyer_id"], deal["seller_id"]):
        await callback.answer("Not your deal", show_alert=True)
        return
    await update_deal_status(deal_id, "accepted")
    await callback.message.edit_text(
        f"✅ Deal accepted by {mention(uid)}\n\nWaiting for middleman payment details.",
        parse_mode="HTML"
    )
    await callback.answer()
    for aid in ADMIN_IDS:
        try:
            await callback.bot.send_message(aid, f"✅ Deal #{deal_id} accepted. Set payment details.")
        except Exception:
            pass


@router.callback_query(F.data.startswith("reject_deal:"))
async def reject_deal(callback: CallbackQuery):
    deal_id = int(callback.data.split(":")[1])
    deal = await get_deal(deal_id)
    if not deal:
        await callback.answer("Not found", show_alert=True)
        return
    uid = callback.from_user.id
    if uid not in (deal["buyer_id"], deal["seller_id"]):
        await callback.answer("Not your deal", show_alert=True)
        return
    await update_deal_status(deal_id, "cancelled", "Rejected by party")
    await callback.message.edit_text(f"❌ Deal rejected by {mention(uid)}", parse_mode="HTML")
    await callback.answer()


# ---------- MY DEALS ----------

@router.message(F.text.in_(["My Deals Info", "My Pending Deals", "📋 My Deals"]))
async def my_deals(message: Message):
    deals = await get_user_deals(message.from_user.id)
    pending_only = message.text and "Pending" in message.text
    if pending_only:
        deals = [d for d in deals if d["status"] not in ("completed", "refunded", "cancelled")]
    if not deals:
        await message.answer("No deals found.")
        return
    for deal in deals[:10]:
        role = "buyer" if deal["buyer_id"] == message.from_user.id else "seller"
        card = await deal_card(deal)
        await message.answer(card, parse_mode="HTML", reply_markup=deal_actions_kb(deal["id"], role))


@router.callback_query(F.data.startswith("buyer_confirm:"))
async def buyer_confirm(callback: CallbackQuery):
    deal_id = int(callback.data.split(":")[1])
    deal = await get_deal(deal_id)
    if not deal or deal["buyer_id"] != callback.from_user.id:
        await callback.answer("Not your deal", show_alert=True)
        return
    if deal["status"] not in ("paid", "shipped", "accepted"):
        await callback.answer("Deal not ready for confirmation", show_alert=True)
        return
    await update_deal_status(deal_id, "completed")
    from database import set_released_amount, get_fee
    fee_pct = await get_fee()
    net = deal["amount"] - round(deal["amount"] * fee_pct / 100, 2)
    await set_released_amount(deal_id, net)
    deal = await get_deal(deal_id)
    msg = completed_card(deal)
    await callback.message.edit_text(msg, parse_mode="HTML", reply_markup=vouch_kb(deal_id))
    await callback.answer()
    try:
        from logger import log_deal_completed
        await log_deal_completed(callback.bot, deal)
    except Exception:
        pass
    for uid in (deal["buyer_id"], deal["seller_id"]):
        if uid != callback.from_user.id:
            try:
                await callback.bot.send_message(uid, msg, parse_mode="HTML", reply_markup=vouch_kb(deal_id))
            except Exception:
                pass
    for aid in ADMIN_IDS:
        try:
            await callback.bot.send_message(aid, f"✅ Buyer confirmed Deal #{deal_id}. Release if needed.")
        except Exception:
            pass


@router.callback_query(F.data.startswith("seller_shipped:"))
async def seller_shipped(callback: CallbackQuery):
    deal_id = int(callback.data.split(":")[1])
    deal = await get_deal(deal_id)
    if not deal or deal["seller_id"] != callback.from_user.id:
        await callback.answer("Not your deal", show_alert=True)
        return
    await update_deal_status(deal_id, "shipped")
    await callback.message.edit_text(f"📦 Marked shipped for deal #{deal_id}")
    await callback.answer()
    try:
        await callback.bot.send_message(
            deal["buyer_id"],
            f"📦 Seller marked deal #{deal_id} as shipped. Confirm when received."
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("dispute:"))
async def open_dispute(callback: CallbackQuery):
    deal_id = int(callback.data.split(":")[1])
    deal = await get_deal(deal_id)
    if not deal or callback.from_user.id not in (deal["buyer_id"], deal["seller_id"]):
        await callback.answer("Not your deal", show_alert=True)
        return
    await update_deal_status(deal_id, "disputed")
    await callback.message.edit_text(f"⚠️ Dispute opened on deal #{deal_id}. Admin will review.")
    await callback.answer()
    for aid in ADMIN_IDS:
        try:
            await callback.bot.send_message(
                aid,
                f"⚠️ DISPUTE Deal #{deal_id}\nBy: {mention(callback.from_user.id)}\n"
                f"{deal['amount']} {deal['currency']}",
                parse_mode="HTML",
                reply_markup=deal_actions_kb(deal_id, "admin")
            )
        except Exception:
            pass


# ---------- VOUCH ----------

@router.callback_query(F.data.startswith("vouch:"))
async def vouch_start(callback: CallbackQuery, state: FSMContext):
    deal_id = int(callback.data.split(":")[1])
    deal = await get_deal(deal_id)
    if not deal or deal["status"] != "completed":
        await callback.answer("Only completed deals can be vouched", show_alert=True)
        return
    if callback.from_user.id not in (deal["buyer_id"], deal["seller_id"]):
        await callback.answer("Not your deal", show_alert=True)
        return
    await state.set_state(VouchState.waiting_text)
    await state.update_data(vouch_deal_id=deal_id)
    await callback.message.answer("⭐ Write your vouch message (short review):")
    await callback.answer()


@router.message(VouchState.waiting_text)
async def process_vouch(message: Message, state: FSMContext):
    data = await state.get_data()
    deal_id = data.get("vouch_deal_id")
    await state.clear()
    deal = await get_deal(deal_id)
    if not deal:
        await message.answer("Deal not found.")
        return
    text = vouch_post(deal, message.from_user.id, message.text.strip())
    try:
        from logger import log_vouch
        await log_vouch(message.bot, text)
        await message.answer("✅ Vouch posted. Thank you!")
    except Exception:
        await message.answer("Could not post vouch. Contact admin.")
