import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_IDS, WEB_PORT
from database import init_db
from handlers import user_router, admin_router, group_router, verify_router
from web.app import app as web_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_bot():
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        logger.error("BOT_TOKEN not set!")
        return

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(group_router)
    dp.include_router(verify_router)

    logger.info("Telegram bot starting...")
    await dp.start_polling(bot)


async def run_web():
    config = uvicorn.Config(web_app, host="0.0.0.0", port=WEB_PORT, log_level="info")
    server = uvicorn.Server(config)
    logger.info(f"Web admin panel starting on port {WEB_PORT}")
    await server.serve()


async def main():
    await init_db()
    logger.info("Database ready")

    if not ADMIN_IDS:
        logger.warning("No ADMIN_IDS configured")

    # Run bot + web together
    await asyncio.gather(run_bot(), run_web())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped")
