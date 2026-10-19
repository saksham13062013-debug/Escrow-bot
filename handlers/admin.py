from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS, WEB_PORT
from database import (
    get_deal, get_active_deals, update_deal_status, delete_deal, set_deal_payment,
    get_stats, get_fee, set_fee, ban_user, unban_user,
    get_all_users, get_banned_users, get_user, get_deals_by_status,
    get_setting, set_setting, is_maintenance, get_all_user_ids
)
from keyboards import admin_panel_kb, deal_actions_kb, back_to_panel_kb

router = Router()


class AdminStates(StatesGroup):
    waiting_fee = State()
    waiting_broadcast = State()
    waiting_search_deal = State()
    waiting_search_user = State()
    waiting_payment = State()
    waiting_wallet_crypto = State()
    waiting_wallet_upi = State()
    waiting_support = State()
    waiting_add_escrower = State()
    waiting_escrower_limit = State()
    waiting_my_address = State()
    waiting_channel_id = State()


def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


@router.message(F.text.in_(["Admin Panel", "🛠 Admin Panel", "🛠 एडमिन पैनल"]))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Access denied.")
        return
    await message.answer("🛠 <b>Admin Control Panel</b>", reply_markup=admin_panel_kb(), parse_mode="HTML")


@router.callback_query(F.data == "admin_panel_home")
async def admin_panel_home(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text("🛠 <b>Admin Control Panel</b>", reply_markup=admin_panel_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    stats = await get_stats()
    fee = await get_fee()
    maint = "🔴 ON" if await is_maintenance() else "🟢 OFF"
    text = (
        "📊 <b>Statistics</b>\n\n"
        f"👥 Users: {stats['users']} (Banned: {stats['banned']})\n"
        f"📦 Deals: {stats['total_deals']}\n"
        f"✅ Completed: {stats['completed']}\n"
        f"⚠️ Disputed: {stats['disputed']}\n"
        f"🔄 Active: {stats['active']}\n"
        f"💰 Volume: {stats['volume']}\n"
        f"⚙️ Fee: {fee}%\n"
        f"🔧 Maintenance: {maint}"
    )
    await callback.message.edit_text(text, reply_markup=admin_panel_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_full_report")
async def admin_full_report(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    stats = await get_stats()
    fee = await get_fee()
    crypto_w = await get_setting("default_crypto_wallet", "Not set")
    upi = await get_setting("default_upi_id", "Not set")
    support = await get_setting("support_contact", "@support")
    text = (
        "📈 <b>Full Report</b>\n\n"
        f"Users: {stats['users']} | Banned: {stats['banned']}\n"
        f"Deals: {stats['total_deals']} | Active: {stats['active']}\n"
        f"Completed: {stats['completed']} | Disputed: {stats['disputed']}\n"
        f"Volume: {stats['volume']}\n\n"
        f"Fee: {fee}%\nSupport: {support}\n\n"
        f"Default Crypto Wallet:\n<code>{crypto_w}</code>\n\n"
        f"Default UPI:\n<code>{upi}</code>"
    )
    await callback.message.edit_text(text, reply_markup=back_to_panel_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_active_deals")
async def admin_active_deals(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    deals = await get_active_deals()
    if not deals:
        await callback.message.edit_text("No active deals.", reply_markup=back_to_panel_kb())
        await callback.answer()
        return
    await callback.message.edit_text(f"📋 Active Deals ({len(deals)})", reply_markup=back_to_panel_kb())
    for deal in deals[:12]:
        text = (
            f"<b>#{deal['id']}</b> | {deal['status']} | {deal['deal_type']}\n"
            f"Buyer <code>{deal['buyer_id']}</code> → Seller <code>{deal['seller_id']}</code>\n"
            f"<b>{deal['amount']} {deal['currency']}</b>\n{deal['description'][:60]}"
        )
        if deal.get("payment_details"):
            text += f"\n🏦 <code>{deal['payment_details']}</code>"
        await callback.message.answer(text, parse_mode="HTML", reply_markup=deal_actions_kb(deal["id"], "admin"))
    await callback.answer()


@router.callback_query(F.data == "admin_disputed_deals")
async def admin_disputed(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    deals = await get_deals_by_status("disputed")
    if not deals:
        await callback.message.edit_text("No disputed deals.", reply_markup=back_to_panel_kb())
        await callback.answer()
        return
    await callback.message.edit_text(f"⚠️ Disputed ({len(deals)})", reply_markup=back_to_panel_kb())
    for d in deals:
        await callback.message.answer(
            f"<b>#{d['id']}</b> {d['amount']} {d['currency']}\n{d['description'][:50]}",
            parse_mode="HTML", reply_markup=deal_actions_kb(d["id"], "admin")
        )
    await callback.answer()


@router.callback_query(F.data == "admin_completed_deals")
async def admin_completed(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    deals = await get_deals_by_status("completed", 10)
    text = "✅ <b>Last 10 Completed</b>\n\n"
    for d in deals:
        text += f"#{d['id']} — {d['amount']} {d['currency']}\n"
    await callback.message.edit_text(text or "None", reply_markup=back_to_panel_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_search_deal")
async def search_deal_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_search_deal)
    await callback.message.answer("🔍 Send Deal ID:")
    await callback.answer()


@router.message(AdminStates.waiting_search_deal)
async def process_search_deal(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        did = int(message.text.strip())
    except ValueError:
        await message.answer("Invalid ID")
        return
    deal = await get_deal(did)
    await state.clear()
    if not deal:
        await message.answer("Not found")
        return
    text = (
        f"<b>Deal #{deal['id']}</b> | {deal['status']} | {deal['deal_type']}\n"
        f"Buyer: <code>{deal['buyer_id']}</code>\nSeller: <code>{deal['seller_id']}</code>\n"
        f"Amount: {deal['amount']} {deal['currency']}\n{deal['description']}\n"
        f"Payment: {deal.get('payment_details') or 'Not set'}\n"
        f"Note: {deal.get('admin_note') or '-'}"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=deal_actions_kb(did, "admin"))


# ----- Deal actions -----

@router.callback_query(F.data.startswith("admin_setpay:"))
async def admin_setpay_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    deal_id = int(callback.data.split(":")[1])
    deal = await get_deal(deal_id)
    if not deal:
        await callback.answer("Not found", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_payment)
    await state.update_data(deal_id=deal_id)
    hint = "crypto address" if deal["deal_type"] == "crypto" else "UPI ID / Bank details"
    await callback.message.answer(
        f"🏦 Set payment details for Deal #{deal_id}\n\n"
        f"Type: {deal['deal_type'].upper()}\nAmount: {deal['amount']} {deal['currency']}\n\n"
        f"Send the {hint} (you can add a note on next line):"
    )
    await callback.answer()


@router.message(AdminStates.waiting_payment)
async def process_payment_details(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    deal_id = data["deal_id"]
    lines = message.text.strip().split("\n", 1)
    details = lines[0]
    note = lines[1] if len(lines) > 1 else None
    await set_deal_payment(deal_id, details, note)
    await update_deal_status(deal_id, "payment_set")
    await state.clear()
    await message.answer(f"✅ Payment details set for Deal #{deal_id}")

    deal = await get_deal(deal_id)
    try:
        from logger import log_payment_set
        await log_payment_set(message.bot, deal)
    except Exception:
        pass

    for uid in [deal["buyer_id"], deal["seller_id"]]:
        try:
            text = (
                f"🏦 <b>Payment details for Deal #{deal_id}</b>\n\n"
                f"Amount: <b>{deal['amount']} {deal['currency']}</b>\n"
                f"<code>{details}</code>"
            )
            if note:
                text += f"\n\n{note}"
            text += "\n\nPlease pay and wait for middleman confirmation."
            await message.bot.send_message(uid, text, parse_mode="HTML")
        except Exception:
            pass


@router.callback_query(F.data.startswith("admin_confirm:"))
async def admin_confirm(callback: CallbackQuery):
    from formatters import payment_confirmed_msg
    if not is_admin(callback.from_user.id):
        return
    deal_id = int(callback.data.split(":")[1])
    deal = await get_deal(deal_id)
    if not deal:
        await callback.answer("Not found", show_alert=True)
        return
    await update_deal_status(deal_id, "paid")
    msg = payment_confirmed_msg(deal)
    await callback.message.edit_text(msg, parse_mode="HTML")
    await callback.answer()
    for uid in [deal["buyer_id"], deal["seller_id"]]:
        try:
            await callback.bot.send_message(uid, msg, parse_mode="HTML")
        except Exception:
            pass
    try:
        from logger import log_payment_confirmed
        await log_payment_confirmed(callback.bot, deal)
    except Exception:
        pass


@router.callback_query(F.data.startswith("admin_release:"))
async def admin_release(callback: CallbackQuery):
    from formatters import completed_card
    from database import set_released_amount, get_fee
    if not is_admin(callback.from_user.id):
        return
    deal_id = int(callback.data.split(":")[1])
    deal = await get_deal(deal_id)
    if not deal:
        return

    fee_pct = await get_fee()
    fee_amt = round(deal["amount"] * fee_pct / 100, 2)
    net = deal["amount"] - fee_amt
    await set_released_amount(deal_id, net)
    await update_deal_status(deal_id, "completed", "Released by middleman")

    deal = await get_deal(deal_id)
    msg = completed_card(deal)
    await callback.message.edit_text(msg, parse_mode="HTML")
    await callback.answer()
    for uid in [deal["buyer_id"], deal["seller_id"]]:
        try:
            await callback.bot.send_message(uid, msg, parse_mode="HTML")
        except Exception:
            pass

    try:
        from logger import log_deal_completed
        await log_deal_completed(callback.bot, deal)
    except Exception:
        pass


@router.callback_query(F.data.startswith("admin_refund:"))
async def admin_refund(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    deal_id = int(callback.data.split(":")[1])
    deal = await get_deal(deal_id)
    if not deal:
        return
    await update_deal_status(deal_id, "refunded", "Refunded by middleman")
    await callback.message.edit_text(f"↩️ Refunded — Deal #{deal_id}")
    try:
        from logger import log_deal_refunded
        await log_deal_refunded(callback.bot, deal)
    except Exception:
        pass
    await callback.answer()
    try:
        await callback.bot.send_message(deal["buyer_id"], f"↩️ Deal #{deal_id} refunded.")
        await callback.bot.send_message(deal["seller_id"], f"↩️ Deal #{deal_id} was refunded.")
    except Exception:
        pass


@router.callback_query(F.data.startswith("admin_dispute:"))
async def admin_dispute(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    deal_id = int(callback.data.split(":")[1])
    await update_deal_status(deal_id, "disputed")
    await callback.message.edit_text(f"⚠️ Marked disputed — #{deal_id}")
    try:
        from logger import log_deal_disputed
        deal = await get_deal(deal_id)
        if deal:
            await log_deal_disputed(callback.bot, deal)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("admin_cancel:"))
async def admin_cancel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    deal_id = int(callback.data.split(":")[1])
    await update_deal_status(deal_id, "cancelled", "Cancelled by middleman")
    await callback.message.edit_text(f"❌ Cancelled — #{deal_id}")
    try:
        from logger import log_deal_cancelled
        deal = await get_deal(deal_id)
        if deal:
            await log_deal_cancelled(callback.bot, deal)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("admin_delete:"))
async def admin_delete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    deal_id = int(callback.data.split(":")[1])
    await delete_deal(deal_id)
    await callback.message.edit_text(f"🗑 Deleted — #{deal_id}")
    await callback.answer()


# ----- Users -----

@router.callback_query(F.data == "admin_all_users")
async def admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    users = await get_all_users(40)
    text = "👥 <b>Latest Users</b>\n\n"
    for u in users:
        flag = "🚫" if u["is_banned"] else "✅"
        text += f"{flag} <code>{u['user_id']}</code> @{u['username'] or '—'} [{u['language']}]\n"
    await callback.message.edit_text(text, reply_markup=back_to_panel_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_banned_users")
async def admin_banned(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    users = await get_banned_users()
    text = "🚫 <b>Banned</b>\n\n" + "\n".join(f"<code>{u['user_id']}</code> @{u['username'] or '—'}" for u in users) if users else "None"
    await callback.message.edit_text(text, reply_markup=back_to_panel_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_search_user")
async def search_user_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_search_user)
    await callback.message.answer("🔎 Send User ID:")
    await callback.answer()


@router.message(AdminStates.waiting_search_user)
async def process_search_user(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("Invalid ID")
        return

    data = await state.get_data()
    action = data.get("action")
    await state.clear()

    if action == "ban":
        await ban_user(uid)
        await message.answer(f"⛔ User <code>{uid}</code> has been <b>BANNED</b>.", parse_mode="HTML", reply_markup=back_to_panel_kb())
        return
    if action == "unban":
        await unban_user(uid)
        await message.answer(f"✅ User <code>{uid}</code> has been <b>UNBANNED</b>.", parse_mode="HTML", reply_markup=back_to_panel_kb())
        return

    user = await get_user(uid)
    if not user:
        await message.answer("User not found in database.")
        return
    status = "🚫 Banned" if user["is_banned"] else "✅ Active"
    await message.answer(
        f"👤 <b>User Info</b>\n\n"
        f"ID: <code>{user['user_id']}</code>\n"
        f"Username: @{user['username'] or '—'}\n"
        f"Name: {user['full_name'] or '—'}\n"
        f"Language: {user['language']}\n"
        f"Status: {status}\n"
        f"Joined: {user['created_at']}",
        parse_mode="HTML", reply_markup=back_to_panel_kb()
    )



# ----- Broadcast & Settings -----

@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.message.answer("📢 Send message to broadcast (or /cancel):")
    await callback.answer()


@router.message(AdminStates.waiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text and message.text.lower() == "/cancel":
        await state.clear()
        await message.answer("Cancelled")
        return
    await state.clear()
    ids = await get_all_user_ids()
    ok = fail = 0
    status = await message.answer(f"Sending to {len(ids)}...")
    for uid in ids:
        try:
            await message.bot.send_message(uid, message.text or "Broadcast", parse_mode="HTML")
            ok += 1
        except Exception:
            fail += 1
    await status.edit_text(f"✅ Done\nSuccess: {ok}\nFailed: {fail}")


@router.callback_query(F.data == "admin_set_fee")
async def set_fee_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    cur = await get_fee()
    await state.set_state(AdminStates.waiting_fee)
    await callback.message.answer(f"Current fee: {cur}%\nSend new fee:")
    await callback.answer()


@router.message(AdminStates.waiting_fee)
async def process_fee(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        fee = float(message.text.strip().replace(",", "."))
        if not 0 <= fee <= 30:
            raise ValueError
    except ValueError:
        await message.answer("Invalid (0-30)")
        return
    await set_fee(fee)
    await state.clear()
    await message.answer(f"✅ Fee set to {fee}%")


@router.callback_query(F.data == "admin_wallets")
async def admin_wallets(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    crypto = await get_setting("default_crypto_wallet", "Not set")
    upi = await get_setting("default_upi_id", "Not set")
    await callback.message.answer(
        f"🏦 <b>Default Wallets</b>\n\nCrypto:\n<code>{crypto}</code>\n\nUPI:\n<code>{upi}</code>\n\n"
        "Send new crypto wallet address, or type 'upi' first to set UPI:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_wallet_crypto)
    await callback.answer()


@router.message(AdminStates.waiting_wallet_crypto)
async def process_wallet(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    text = message.text.strip()
    if text.lower() == "upi":
        await state.set_state(AdminStates.waiting_wallet_upi)
        await message.answer("Send UPI ID:")
        return
    await set_setting("default_crypto_wallet", text)
    await state.clear()
    await message.answer(f"✅ Crypto wallet updated:\n<code>{text}</code>", parse_mode="HTML")


@router.message(AdminStates.waiting_wallet_upi)
async def process_upi(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await set_setting("default_upi_id", message.text.strip())
    await state.clear()
    await message.answer(f"✅ UPI updated:\n<code>{message.text.strip()}</code>", parse_mode="HTML")


@router.callback_query(F.data == "admin_settings")
async def admin_settings(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    support = await get_setting("support_contact", "@support")
    await state.set_state(AdminStates.waiting_support)
    await callback.message.answer(f"Current support: {support}\nSend new support contact:")
    await callback.answer()


@router.message(AdminStates.waiting_support)
async def process_support(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await set_setting("support_contact", message.text.strip())
    await state.clear()
    await message.answer("✅ Support updated")


@router.callback_query(F.data == "admin_maintenance")
async def toggle_maint(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    cur = await is_maintenance()
    await set_setting("maintenance_mode", "0" if cur else "1")
    status = "DISABLED" if cur else "ENABLED"
    await callback.message.edit_text(f"🔧 Maintenance: <b>{status}</b>", reply_markup=back_to_panel_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_web_info")
async def web_info(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "🌐 <b>Web Admin Panel</b>\n\n"
        "After deploying on Railway, open:\n"
        "<code>https://your-app.up.railway.app</code>\n\n"
        "Login with the ADMIN_SECRET you set in environment variables.\n\n"
        "From the web panel you can manage all deals, users, stats and settings professionally.",
        reply_markup=back_to_panel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


# Commands
@router.message(Command("deal"))
async def cmd_deal(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Usage: /deal <id>")
        return
    try:
        did = int(parts[1])
    except ValueError:
        return
    deal = await get_deal(did)
    if not deal:
        await message.answer("Not found")
        return
    text = (
        f"<b>#{deal['id']}</b> {deal['status']} {deal['deal_type']}\n"
        f"Buyer <code>{deal['buyer_id']}</code> Seller <code>{deal['seller_id']}</code>\n"
        f"{deal['amount']} {deal['currency']}\n{deal['description']}\n"
        f"Pay: {deal.get('payment_details') or '—'}"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=deal_actions_kb(did, "admin"))


@router.message(Command("ban"))
async def cmd_ban(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        return
    try:
        uid = int(parts[1])
    except ValueError:
        return
    await ban_user(uid)
    await message.answer(f"Banned {uid}")


@router.message(Command("unban"))
async def cmd_unban(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        return
    try:
        uid = int(parts[1])
    except ValueError:
        return
    await unban_user(uid)
    await message.answer(f"Unbanned {uid}")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    stats = await get_stats()
    await message.answer(
        f"Users: {stats['users']}\nDeals: {stats['total_deals']}\n"
        f"Active: {stats['active']} Completed: {stats['completed']}\nVolume: {stats['volume']}"
    )


# ==================== EXTRA ADVANCED HANDLERS ====================

@router.callback_query(F.data == "admin_pending_deals")
async def admin_pending_deals(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    deals = await get_deals_by_status("pending_payment")
    if not deals:
        await callback.message.edit_text("⏳ No pending payment deals.", reply_markup=back_to_panel_kb())
        await callback.answer()
        return
    await callback.message.edit_text(f"⏳ <b>Pending Payment ({len(deals)})</b>", reply_markup=back_to_panel_kb(), parse_mode="HTML")
    for d in deals[:12]:
        text = f"<b>#{d['id']}</b> | {d.get('trade_id','')}\n{d['amount']} {d['currency']}\n{d['description'][:50]}"
        await callback.message.answer(text, parse_mode="HTML", reply_markup=deal_actions_kb(d["id"], "admin"))
    await callback.answer()


@router.callback_query(F.data == "admin_paid_deals")
async def admin_paid_deals(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    deals = await get_deals_by_status("paid")
    if not deals:
        await callback.message.edit_text("No paid deals waiting.", reply_markup=back_to_panel_kb())
        await callback.answer()
        return
    await callback.message.edit_text(f"💰 <b>Paid Deals ({len(deals)})</b>", reply_markup=back_to_panel_kb(), parse_mode="HTML")
    for d in deals[:12]:
        await callback.message.answer(
            f"<b>#{d['id']}</b> {d['amount']} {d['currency']}\n{d['description'][:50]}",
            parse_mode="HTML", reply_markup=deal_actions_kb(d["id"], "admin")
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_dealinfo:"))
async def admin_dealinfo(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    deal_id = int(callback.data.split(":")[1])
    deal = await get_deal(deal_id)
    if not deal:
        await callback.answer("Not found", show_alert=True)
        return

    from formatters import deal_card
    card = await deal_card(deal)
    text = card + f"\n\n📌 <b>Status:</b> <code>{deal['status']}</code>"
    if deal.get("admin_note"):
        text += f"\n📝 Note: {deal['admin_note']}"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=deal_actions_kb(deal_id, "admin"))
    await callback.answer()


@router.callback_query(F.data == "admin_ban_user")
async def admin_ban_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_search_user)  # reuse
    await state.update_data(action="ban")
    await callback.message.answer("⛔ Send the User ID to <b>BAN</b>:", parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_unban_user")
async def admin_unban_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_search_user)
    await state.update_data(action="unban")
    await callback.message.answer("✅ Send the User ID to <b>UNBAN</b>:", parse_mode="HTML")
    await callback.answer()




# ==================== ESCROWER MANAGEMENT ====================

@router.callback_query(F.data == "admin_escrowers")
async def admin_list_escrowers(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    from database import get_all_escrowers, get_escrower_addresses
    escrowers = await get_all_escrowers()
    if not escrowers:
        await callback.message.edit_text(
            "No escrowers yet.\nUse ➕ Add Escrower",
            reply_markup=back_to_panel_kb()
        )
        await callback.answer()
        return
    text = "🛡 <b>Official Escrowers</b>\n\n"
    for e in escrowers:
        uname = f"@{e['username']}" if e['username'] else "—"
        addrs = await get_escrower_addresses(e["user_id"])
        text += f"• <code>{e['user_id']}</code> {uname}\n  Limit: {e['deal_limit']} | Addresses: {len(addrs)}\n"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_panel_kb())
    await callback.answer()


@router.callback_query(F.data == "admin_add_escrower")
async def admin_add_escrower_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_add_escrower)
    await callback.message.answer(
        "➕ Send escrower User ID\n"
        "Optional: add limit after space\n"
        "Example: <code>123456789 15</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.waiting_add_escrower)
async def process_add_escrower(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.strip().split()
    try:
        uid = int(parts[0])
        limit = int(parts[1]) if len(parts) > 1 else 10
    except ValueError:
        await message.answer("Invalid. Send: user_id [limit]")
        return
    from database import add_escrower, get_user
    user = await get_user(uid)
    uname = user["username"] if user else None
    fname = user["full_name"] if user else None
    await add_escrower(uid, uname, fname, limit)
    await state.clear()
    await message.answer(
        f"✅ Escrower added\nID: <code>{uid}</code>\nLimit: {limit} active deals\n\n"
        f"They can now set addresses with /myaddress",
        parse_mode="HTML",
        reply_markup=back_to_panel_kb()
    )
    try:
        await message.bot.send_message(
            uid,
            "🛡 You have been added as an <b>Official Escrower</b>.\n\n"
            "Set your payment addresses with:\n"
            "<code>/myaddress USDT_TRC20 TXyz...</code>\n\n"
            "Users can verify your address with /verify",
            parse_mode="HTML"
        )
    except Exception:
        pass


@router.message(Command("myaddress"))
async def cmd_myaddress(message: Message):
    """Escrower sets their own address: /myaddress [label] address"""
    from database import is_escrower, add_escrower_address, get_escrower_addresses
    uid = message.from_user.id
    # Allow admins too
    if not await is_escrower(uid) and not is_admin(uid):
        await message.answer("⛔ Only official escrowers can set addresses.")
        return

    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 2:
        addrs = await get_escrower_addresses(uid)
        if not addrs:
            await message.answer(
                "You have no addresses yet.\n\n"
                "Usage:\n"
                "<code>/myaddress TXyz... OR name@upi</code>\n"
                "<code>/myaddress USDT_TRC20 TXyz...</code>",
                parse_mode="HTML"
            )
            return
        text = "🏦 <b>Your registered addresses</b>\n\n"
        for a in addrs:
            label = f"[{a['label']}] " if a['label'] else ""
            text += f"• {label}<code>{a['address']}</code>\n"
        text += "\nAdd more: <code>/myaddress label address</code>"
        await message.answer(text, parse_mode="HTML")
        return

    if len(parts) == 2:
        label = None
        address = parts[1].strip()
    else:
        label = parts[1].strip()
        address = parts[2].strip()

    await add_escrower_address(uid, address, label)
    await message.answer(
        f"✅ Address registered\n"
        f"{'Label: ' + label + chr(10) if label else ''}"
        f"<code>{address}</code>\n\n"
        f"Users can now verify it with:\n"
        f"<code>/verify {address}</code>",
        parse_mode="HTML"
    )


@router.message(Command("removeaddress"))
async def cmd_removeaddress(message: Message):
    from database import is_escrower, get_escrower_addresses, remove_escrower_address
    uid = message.from_user.id
    if not await is_escrower(uid) and not is_admin(uid):
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        addrs = await get_escrower_addresses(uid)
        text = "Your addresses (use /removeaddress ID):\n\n"
        for a in addrs:
            text += f"ID {a['id']}: <code>{a['address']}</code>\n"
        await message.answer(text or "None", parse_mode="HTML")
        return
    try:
        aid = int(parts[1])
    except ValueError:
        await message.answer("Send address ID number")
        return
    await remove_escrower_address(aid, uid)
    await message.answer("✅ Address removed")


# ==================== CHANNEL / GROUP SETTINGS ====================

CHANNEL_KEYS = {
    "admin_set_log_channel": ("log_channel_id", "Logs Channel"),
    "admin_set_completed_channel": ("completed_channel_id", "Deal Completed Channel"),
    "admin_set_vouch_channel": ("vouch_channel_id", "Vouch Channel"),
    "admin_set_force_group": ("force_group_id", "Force Join Group ID"),
    "admin_set_force_channel": ("force_channel_id", "Force Join Channel ID"),
}


@router.callback_query(F.data.in_(list(CHANNEL_KEYS.keys())))
async def admin_set_channel_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    key, label = CHANNEL_KEYS[callback.data]
    from database import get_setting
    current = await get_setting(key, "Not set")
    await state.set_state(AdminStates.waiting_channel_id)
    await state.update_data(channel_key=key, channel_label=label)
    extra = ""
    if "force_group" in key:
        extra = "\nAlso send invite link on next message or include: ID|https://t.me/+xxx"
    if "force_channel" in key:
        extra = "\nAlso send invite link on next message or include: ID|https://t.me/+xxx"
    await callback.message.answer(
        f"Current <b>{label}</b>: <code>{current}</code>\n\n"
        f"Send new channel/group ID (e.g. -1001234567890).{extra}\n"
        f"Send /clear to remove.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.waiting_channel_id)
async def process_channel_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    key = data.get("channel_key")
    label = data.get("channel_label", "Channel")
    text = (message.text or "").strip()
    await state.clear()

    from database import set_setting

    if text.lower() == "/clear":
        await set_setting(key, "")
        if key == "force_group_id":
            await set_setting("force_group_link", "")
        if key == "force_channel_id":
            await set_setting("force_channel_link", "")
        await message.answer(f"{label} cleared.", reply_markup=back_to_panel_kb())
        return

    # Support ID|link format
    link = ""
    if "|" in text:
        parts = text.split("|", 1)
        text, link = parts[0].strip(), parts[1].strip()

    try:
        cid = int(text)
    except ValueError:
        await message.answer("Invalid ID. Send numeric channel/group ID like -1001234567890")
        return

    await set_setting(key, str(cid))
    if link and key == "force_group_id":
        await set_setting("force_group_link", link)
    if link and key == "force_channel_id":
        await set_setting("force_channel_link", link)

    await message.answer(
        f"{label} set to <code>{cid}</code>"
        + (f"\nLink: {link}" if link else "")
        + "\n\nBot must be admin in that chat.",
        parse_mode="HTML",
        reply_markup=back_to_panel_kb()
    )
