"""
Точка входа приложения Pearl Translation Service.
"""

import asyncio
import sys

from app.app import App


async def main() -> None:
    app = App()
    try:
        await app.run()
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        # К этому моменту loguru уже настроен — он перехватит logging
        import logging
        logging.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
