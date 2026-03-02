import asyncio
import logging
import sys
from app.app import App

async def main():
    app = App()
    try:
        await app.run()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Application stopped")
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Check for windows loop policy if needed, though 3.12 handles it well usually.
        # But for uvicorn + asyncio on windows, typically ProactorEventLoop is default.
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
