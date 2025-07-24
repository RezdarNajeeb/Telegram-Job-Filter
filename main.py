from telegram_client import get_client
from job_filter import fetch_and_filter_messages
from forwarder import forward_messages
from utils import load_config, save_to_file
from sheets import log_to_sheet

import asyncio

async def main():
    config = load_config()
    client = get_client()

    async with client:
        filtered = await fetch_and_filter_messages(client, config)

        if config.get("save_to_file"):
            save_to_file(filtered)

        await forward_messages(client, filtered, config.get("forward_to"))

        if config.get("log_to_google_sheets"):
            log_to_sheet(filtered)

    print(f"✅ {len(filtered)} relevant jobs processed.")

if __name__ == "__main__":
    asyncio.run(main())
