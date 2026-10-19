"""Professional deal cards — SMOOTH ESCROW SERVICE style."""

from database import get_fee


def mention(user_id: int, label: str = None) -> str:
    """Always mention by user id — never plain name only."""
    text = label or str(user_id)
    return f'<a href="tg://user?id={user_id}">{text}</a>'


def format_currency(amount: float, currency: str) -> str:
    cur = (currency or "").upper()
    if "INR" in cur or "UPI" in cur or "BANK" in cur:
        return f"₹{amount:,.2f}"
    if "USDT" in cur:
        return f"{amount:,.2f} USDT"
    if "BTC" in cur:
        return f"{amount} BTC"
    if "ETH" in cur:
        return f"{amount} ETH"
    return f"{amount} {currency}"


async def deal_card(deal: dict, buyer_label: str = None, seller_label: str = None) -> str:
    fee_pct = await get_fee()
    fee_amt = round(deal["amount"] * fee_pct / 100, 2)
    net = deal["amount"] - fee_amt

    amount_str = format_currency(deal["amount"], deal["currency"])
    fee_str = format_currency(fee_amt, deal["currency"])
    net_str = format_currency(net, deal["currency"])
    trade_id = deal.get("trade_id") or f"DL-SE-{deal['id']}"
    escrowed = deal.get("escrowed_by") or "SMOOTH ESCROW"

    buyer = mention(deal["buyer_id"], buyer_label or "Buyer")
    seller = mention(deal["seller_id"], seller_label or "Seller")

    lines = [
        "🛡 <b>SMOOTH ESCROW SERVICE</b>",
        "",
        f"💰 <b>Deal Amount:</b> {amount_str}",
        f"📤 <b>Fee:</b> {fee_pct}% — {fee_str}",
        f"📤 <b>Net Release:</b> {net_str}",
        f"🆔 <b>Trade ID:</b> <code>{trade_id}</code>",
        "",
        f"🛒 <b>Buyer:</b> {buyer}",
        f"🏷 <b>Seller:</b> {seller}",
        f"📝 <b>Detail:</b> {deal.get('description') or '—'}",
    ]
    if deal.get("expected_time"):
        lines.append(f"⏱️ <b>Expected Time:</b> {deal['expected_time']}")
    if deal.get("terms"):
        lines.append(f"📌 <b>T/C:</b> {deal['terms']}")
    lines.append("")
    lines.append(f"🛡 <b>Escrowed By:</b> {escrowed}")

    if deal.get("payment_details"):
        lines.append("")
        lines.append(f"🏦 <b>Payment:</b>\n<code>{deal['payment_details']}</code>")
        if deal.get("payment_note"):
            lines.append(deal["payment_note"])

    status = deal.get("status")
    if status:
        lines.append("")
        lines.append(f"📌 <b>Status:</b> <code>{status}</code>")

    return "\n".join(lines)


def completed_card(deal: dict) -> str:
    trade_id = deal.get("trade_id") or f"DL-SE-{deal['id']}"
    released = deal.get("released_amount") or deal["amount"]
    released_str = format_currency(released, deal["currency"])
    escrowed = deal.get("escrowed_by") or "SMOOTH ESCROW"
    buyer = mention(deal["buyer_id"], "Buyer")
    seller = mention(deal["seller_id"], "Seller")

    return (
        f"✅ <b>DEAL COMPLETED</b>\n"
        f"🆔 Trade ID: <code>{trade_id}</code>\n"
        f"📤 Released: {released_str}\n"
        f"🛒 {buyer}  |  🏷 {seller}\n"
        f"🛡 Escrowed By: {escrowed}\n\n"
        f"Both parties may drop a vouch below 👇🏻"
    )


def payment_confirmed_msg(deal: dict) -> str:
    trade_id = deal.get("trade_id") or f"DL-SE-{deal['id']}"
    return (
        f"✅ <b>PAYMENT RECEIVED</b>\n"
        f"🆔 Trade ID: <code>{trade_id}</code>\n\n"
        f"Continue the deal in private.\n"
        f"<b>Screen recording must be ON.</b>"
    )


def vouch_post(deal: dict, from_user_id: int, text: str) -> str:
    trade_id = deal.get("trade_id") or f"DL-SE-{deal['id']}"
    amount = format_currency(deal.get("released_amount") or deal["amount"], deal["currency"])
    who = mention(from_user_id)
    return (
        f"⭐ <b>VOUCH</b>\n\n"
        f"{who} vouched for <b>SMOOTH ESCROW</b>\n"
        f"🆔 <code>{trade_id}</code> | {amount}\n\n"
        f"{text}"
    )
