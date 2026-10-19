import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "change_me_please")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./escrow.db")
WEB_PORT = int(os.getenv("WEB_PORT", "8080"))
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "en")

def _int_env(name):
    v = os.getenv(name, "")
    try:
        return int(v) if v else None
    except ValueError:
        return None

LOG_CHANNEL_ID = _int_env("LOG_CHANNEL_ID")
VOUCH_CHANNEL_ID = _int_env("VOUCH_CHANNEL_ID")
ESCROW_GROUP_ID = _int_env("ESCROW_GROUP_ID")
ESCROW_GROUP_LINK = os.getenv("ESCROW_GROUP_LINK", "")

SUPPORTED_CURRENCIES_CRYPTO = ["USDT TRC20", "USDT ERC20", "BTC", "ETH", "LTC", "SOL"]
SUPPORTED_CURRENCIES_INR = ["INR (UPI)", "INR (Bank)"]
ALL_CURRENCIES = SUPPORTED_CURRENCIES_CRYPTO + SUPPORTED_CURRENCIES_INR
