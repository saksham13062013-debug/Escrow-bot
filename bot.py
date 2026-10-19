"""Entry point alias for Railway / hosting that expects bot.py"""
from main import main
import asyncio

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
