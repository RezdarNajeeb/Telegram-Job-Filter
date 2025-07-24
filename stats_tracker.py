import json
import os
from datetime import datetime
from collections import Counter

from forwarder import forward_messages
from job_filter import fetch_and_filter_messages
from report_generator import save_html_report
from sheets import log_to_sheet
from telegram_client import get_client
from utils import load_config, save_to_file


class JobStats:
    def __init__(self, stats_file="job_stats.json", save_to_file=False):
        self.stats_file = stats_file
        self.save_to_file = save_to_file
        self.stats = self.load_stats()

    def load_stats(self):
        """Load existing stats or create new ones"""
        if self.save_to_file and os.path.exists(self.stats_file):
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "total_jobs_found": 0,
            "channels_stats": {},
            "keyword_stats": {},
            "daily_stats": {},
            "jobs_with_contact": 0,
            "last_updated": None
        }

    def update_stats(self, messages):
        """Update statistics with new messages"""
        if not messages:
            return

        today = datetime.now().strftime('%Y-%m-%d')

        # Update totals
        self.stats["total_jobs_found"] += len(messages)
        self.stats["last_updated"] = datetime.now().isoformat()

        # Daily stats
        if today not in self.stats["daily_stats"]:
            self.stats["daily_stats"][today] = 0
        self.stats["daily_stats"][today] += len(messages)

        # Channel stats
        for msg in messages:
            channel = msg['channel']
            if channel not in self.stats["channels_stats"]:
                self.stats["channels_stats"][channel] = 0
            self.stats["channels_stats"][channel] += 1

            # Keyword stats
            for keyword in msg.get('matched_keywords', []):
                if keyword not in self.stats["keyword_stats"]:
                    self.stats["keyword_stats"][keyword] = 0
                self.stats["keyword_stats"][keyword] += 1

            # Contact info stats
            if msg.get('has_contact'):
                self.stats["jobs_with_contact"] += 1

        if self.save_to_file:
            self.save_stats()

    def save_stats(self):
        """Save stats to file"""
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)

    def get_summary(self):
        """Get a summary of statistics"""
        if not self.stats["total_jobs_found"]:
            return "📊 No jobs found yet. Start filtering to see stats!"

        # Top channels
        top_channels = Counter(self.stats["channels_stats"]).most_common(3)
        # Top keywords
        top_keywords = Counter(self.stats["keyword_stats"]).most_common(3)

        # Recent activity (last 7 days)
        recent_days = list(self.stats["daily_stats"].keys())[-7:]
        recent_total = sum(self.stats["daily_stats"].get(day, 0) for day in recent_days)

        summary = f"""
📊 **Job Search Statistics**

🎯 **Overall:**
• Total jobs found: {self.stats["total_jobs_found"]}
• Jobs with contact info: {self.stats["jobs_with_contact"]} ({self.stats["jobs_with_contact"] / max(self.stats["total_jobs_found"], 1) * 100:.1f}%)
• Last updated: {self.stats.get("last_updated", "Never")[:16]}

📈 **Recent Activity (7 days):**
• Jobs found: {recent_total}

🏆 **Top Performing Channels:**
"""
        for channel, count in top_channels:
            summary += f"• {channel}: {count} jobs\n"

        summary += f"\n🔥 **Most Matched Keywords:**\n"
        for keyword, count in top_keywords:
            summary += f"• {keyword}: {count} matches\n"

        return summary


# Usage in main.py
def update_main_with_stats():
    """Updated main function with statistics"""

    async def main():
        config = load_config()
        client = get_client()
        stats = JobStats()  # Initialize stats tracker

        async with client:
            filtered = await fetch_and_filter_messages(client, config)

            if config.get("save_to_file"):
                # Save both text and HTML reports
                save_to_file(filtered)
                if filtered:  # Only create HTML if we have results
                    save_html_report(filtered)

            await forward_messages(client, filtered, config.get("forward_to"))

            if config.get("log_to_google_sheets"):
                log_to_sheet(filtered)

            # Update statistics
            stats.update_stats(filtered)

            # Print summary
            print(f"\n✅ {len(filtered)} relevant jobs processed.")
            print(stats.get_summary())

        return main