TEXTS = {
    "welcome": "👋 Welcome to the <b>MM Escrow Bot</b>, {name}!\n\nI act as a trusted middleman for Crypto & INR deals.\n\n• Buyer pays → Middleman confirms\n• Seller delivers → Buyer confirms\n• Middleman releases funds\n\nUse the menu below.",
    "banned": "⛔ You are banned from using this bot.",
    "maintenance": "🔧 <b>Bot is under maintenance</b>\n\nPlease try again later.\nSupport: {support}",
    "how_it_works": (
        "<b>How Escrow Works</b>\n\n"
        "1. Create a deal (Crypto or INR)\n"
        "2. Middleman provides payment address / UPI\n"
        "3. Buyer pays → Middleman confirms\n"
        "4. Seller delivers\n"
        "5. Buyer confirms receipt\n"
        "6. Middleman releases funds\n\n"
        "<b>Fee:</b> {fee}%\n"
        "<b>Support:</b> {support}"
    ),
    "create_deal": "➕ Create Deal",
    "my_deals": "📋 My Deals",
    "how_works_btn": "ℹ️ How it works",
    "lang_btn": "🌐 Language",
    "admin_btn": "🛠 Admin Panel",
    "choose_type": "Choose deal type:",
    "type_crypto": "🪙 Crypto",
    "type_inr": "🇮🇳 INR (UPI/Bank)",
    "send_other_id": "👤 Send the <b>Telegram User ID</b> of the other party.\n\nThey can get it from @userinfobot",
    "invalid_id": "❌ Please send a valid numeric User ID.",
    "self_deal": "❌ You cannot create a deal with yourself.",
    "enter_amount": "💰 Enter the deal amount (example: 1500 or 99.50):",
    "invalid_amount": "❌ Please enter a valid positive number.",
    "choose_currency": "💱 Choose currency:",
    "enter_desc": "📝 Write a short description of the deal:",
    "deal_created": (
        "✅ <b>Deal #{id} created!</b>\n\n"
        "👤 Buyer: <code>{buyer}</code>\n"
        "👤 Seller: <code>{seller}</code>\n"
        "💰 Amount: <b>{amount} {currency}</b>\n"
        "📊 Fee ({fee}%): {fee_amount}\n"
        "💵 Total: <b>{total}</b>\n"
        "📝 {desc}\n\n"
        "<b>Status:</b> Waiting for middleman payment details"
    ),
    "no_deals": "You have no deals yet.",
    "deal_card": "{emoji} <b>Deal #{id}</b>\nAmount: {amount} {currency}\nStatus: <code>{status}</code>\n{desc}",
    "buyer_confirmed": "✅ You confirmed receipt for Deal #{id}.\nMiddleman will release the funds.",
    "seller_shipped": "📦 You marked Deal #{id} as shipped/delivered.",
    "dispute_opened": "⚠️ Dispute opened for Deal #{id}. Middleman will review.",
    "payment_received_notify": "💰 Middleman confirmed payment for <b>Deal #{id}</b>.\nSeller can now deliver.",
    "released_notify": "✅ Funds for Deal #{id} have been released.",
    "refunded_notify": "↩️ Deal #{id} has been refunded.",
    "group_deal_hint": "To create a deal in group, reply to a user or use /deal @username amount currency description",
}
