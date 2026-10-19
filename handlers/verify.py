"""
/verify <address or upi> — check if it belongs to a registered escrower.
"""

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from database import find_address_owner

router = Router()


def is_upi(value: str) -> bool:
    v = value.lower()
    return "@" in v or v.endswith("@upi") or "upi" in v


def verified_message(owner: dict, address: str) -> str:
    name = f"@{owner['username']}" if owner.get("username") else owner.get("full_name") or str(owner["user_id"])
    label = owner.get("label") or ("UPI" if is_upi(address) else "Crypto")
    kind = "UPI ID" if is_upi(address) else "Address"
    return (
        f"✅ <b>VERIFIED {kind.upper()}</b>\n\n"
        f"🏦 {kind}:\n<code>{address}</code>\n\n"
        f"🛡 Official Escrower: {name}\n"
        f"🏷 Label: {label}\n\n"
        f"This {kind.lower()} is registered in our escrow system.\n"
        f"You can safely continue the deal with this middleman."
    )


def scam_message(address: str) -> str:
    kind = "UPI ID" if is_upi(address) else "Address"
    return (
        f"🚨 <b>NOT VERIFIED — POSSIBLE SCAM</b>\n\n"
        f"🏦 {kind}:\n<code>{address}</code>\n\n"
        f"❌ This {kind.lower()} is <b>NOT</b> registered to any official escrower.\n\n"
        f"⚠️ Do <b>NOT</b> send money here.\n"
        f"Use only addresses / UPI verified by this bot with /verify.\n\n"
        f"Stay safe."
    )


@router.message(Command("verify"))
async def cmd_verify(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "Usage:\n"
            "<code>/verify TXyz...crypto_address</code>\n"
            "<code>/verify name@upi</code>\n\n"
            "Check if crypto address or UPI ID belongs to an official escrower.",
            parse_mode="HTML"
        )
        return

    address = parts[1].strip()
    if len(address) < 4:
        await message.reply("Too short. Paste the full address or UPI ID.")
        return

    owner = await find_address_owner(address)
    if owner:
        await message.reply(verified_message(owner, address), parse_mode="HTML")
    else:
        await message.reply(scam_message(address), parse_mode="HTML")
