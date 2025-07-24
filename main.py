from telegram_client import get_client
from job_filter import fetch_and_filter_messages
from forwarder import forward_messages
from utils import load_config, save_to_file
from sheets import log_to_sheet
from report_generator import save_html_report
from stats_tracker import JobStats

import asyncio


async def main():
    config = load_config()
    client = get_client()
    stats = JobStats() # by default stats are not saved to file

    async with client:
        print("🔍 Searching for jobs...")
        filtered = await fetch_and_filter_messages(client, config)

        if not filtered:
            print("❌ No jobs found matching your criteria")
            return

        # Save reports
        if config.get("save_to_file", True):
            save_to_file(filtered)  # Original text file
            save_html_report(filtered)  # New HTML report

        # Forward messages
        if config.get("forward_to"):
            await forward_messages(client, filtered, config.get("forward_to"))

        # Log to Google Sheets
        if config.get("log_to_google_sheets"):
            log_to_sheet(filtered)

        # Update statistics
        stats.update_stats(filtered)

        # Print results
        print(f"\n✅ {len(filtered)} relevant jobs processed.")
        print("\n" + stats.get_summary())


if __name__ == "__main__":
    asyncio.run(main())