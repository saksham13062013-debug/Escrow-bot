from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu_kb(lang: str = "en", is_admin: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Create Deal")
    builder.button(text="My Stats")
    builder.button(text="My Deals Info")
    builder.button(text="My Pending Deals")
    builder.button(text="Escrow Global Stats")
    builder.button(text="Language")
    builder.button(text="How it works")
    if is_admin:
        builder.button(text="Admin Panel")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def lang_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="English", callback_data="setlang:en")
    b.button(text="Hindi", callback_data="setlang:hi")
    b.button(text="Back", callback_data="nav_home")
    b.adjust(2, 1)
    return b.as_markup()


def role_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="I am Buyer", callback_data="role:buyer")
    b.button(text="I am Seller", callback_data="role:seller")
    b.button(text="Cancel", callback_data="nav_cancel")
    b.adjust(1)
    return b.as_markup()


def deal_type_kb(lang: str = "en") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Crypto", callback_data="dealtype:crypto")
    b.button(text="INR (UPI/Bank)", callback_data="dealtype:inr")
    b.button(text="Cancel", callback_data="nav_cancel")
    b.adjust(1)
    return b.as_markup()


def currencies_kb(deal_type: str = "crypto") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if deal_type == "crypto":
        items = ["USDT TRC20", "USDT ERC20", "BTC", "ETH", "LTC", "SOL"]
    else:
        items = ["INR (UPI)", "INR (Bank)"]
    for cur in items:
        b.button(text=cur, callback_data=f"currency:{cur}")
    b.button(text="Cancel", callback_data="nav_cancel")
    b.adjust(2)
    return b.as_markup()


def deal_actions_kb(deal_id: int, role: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if role == "buyer":
        b.button(text="Confirm Receipt", callback_data=f"buyer_confirm:{deal_id}")
        b.button(text="Open Dispute", callback_data=f"dispute:{deal_id}")
    elif role == "seller":
        b.button(text="Mark Shipped", callback_data=f"seller_shipped:{deal_id}")
        b.button(text="Open Dispute", callback_data=f"dispute:{deal_id}")
    elif role == "admin":
        b.button(text="Set Payment Details", callback_data=f"admin_setpay:{deal_id}")
        b.button(text="Confirm Payment", callback_data=f"admin_confirm:{deal_id}")
        b.button(text="Release Funds", callback_data=f"admin_release:{deal_id}")
        b.button(text="Refund Buyer", callback_data=f"admin_refund:{deal_id}")
        b.button(text="Mark Dispute", callback_data=f"admin_dispute:{deal_id}")
        b.button(text="Cancel Deal", callback_data=f"admin_cancel:{deal_id}")
        b.button(text="Delete Deal", callback_data=f"admin_delete:{deal_id}")
        b.button(text="Full Details", callback_data=f"admin_dealinfo:{deal_id}")
    b.button(text="Home", callback_data="nav_home")
    b.adjust(1)
    return b.as_markup()


def accept_deal_kb(deal_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Accept Deal", callback_data=f"accept_deal:{deal_id}")
    b.button(text="Reject Deal", callback_data=f"reject_deal:{deal_id}")
    b.adjust(1)
    return b.as_markup()


def vouch_kb(deal_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Submit Vouch", callback_data=f"vouch:{deal_id}")
    b.button(text="Home", callback_data="nav_home")
    b.adjust(1)
    return b.as_markup()


def admin_panel_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Dashboard", callback_data="admin_stats")
    b.button(text="Full Report", callback_data="admin_full_report")
    b.button(text="Active Deals", callback_data="admin_active_deals")
    b.button(text="Pending Payment", callback_data="admin_pending_deals")
    b.button(text="Disputes", callback_data="admin_disputed_deals")
    b.button(text="Completed", callback_data="admin_completed_deals")
    b.button(text="Search Deal", callback_data="admin_search_deal")
    b.button(text="Users", callback_data="admin_all_users")
    b.button(text="Banned", callback_data="admin_banned_users")
    b.button(text="Ban User", callback_data="admin_ban_user")
    b.button(text="Unban User", callback_data="admin_unban_user")
    b.button(text="Escrowers", callback_data="admin_escrowers")
    b.button(text="Add Escrower", callback_data="admin_add_escrower")
    b.button(text="Wallets", callback_data="admin_wallets")
    b.button(text="Fee", callback_data="admin_set_fee")
    b.button(text="Broadcast", callback_data="admin_broadcast")
    # Channel settings
    b.button(text="Set Log Channel", callback_data="admin_set_log_channel")
    b.button(text="Set Completed Channel", callback_data="admin_set_completed_channel")
    b.button(text="Set Vouch Channel", callback_data="admin_set_vouch_channel")
    b.button(text="Set Force Group", callback_data="admin_set_force_group")
    b.button(text="Set Force Channel", callback_data="admin_set_force_channel")
    b.button(text="Maintenance", callback_data="admin_maintenance")
    b.button(text="Web Panel", callback_data="admin_web_info")
    b.button(text="Close", callback_data="back_main")
    b.adjust(2, 2, 2, 1, 2, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1)
    return b.as_markup()


def back_to_panel_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Admin Panel", callback_data="admin_panel_home")
    b.button(text="Home", callback_data="nav_home")
    b.adjust(2)
    return b.as_markup()


def nav_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Home", callback_data="nav_home")
    b.button(text="Cancel", callback_data="nav_cancel")
    b.adjust(2)
    return b.as_markup()
