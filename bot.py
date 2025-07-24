from telethon import TelegramClient, events, Button
from telethon.tl.custom import Message
import asyncio
import os
from dotenv import load_dotenv
from job_filter import fetch_and_filter_messages
from utils import load_config
import json
from datetime import datetime

load_dotenv()


class JobFilterBot:
    def __init__(self):
        api_id = int(os.getenv("API_ID"))
        api_hash = os.getenv("API_HASH")
        self.client = TelegramClient("bot_session", api_id, api_hash)
        self.user_configs = {}  # Store user configurations

    async def start_bot(self):
        """Start the bot and add event handlers"""
        await self.client.start()
        print("🤖 Bot started! Send /start to begin")

        # Event handlers
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            await self.handle_start(event)

        @self.client.on(events.NewMessage(pattern='/search'))
        async def search_handler(event):
            await self.handle_search(event)

        @self.client.on(events.NewMessage(pattern='/config'))
        async def config_handler(event):
            await self.handle_config(event)

        @self.client.on(events.NewMessage(pattern='/stats'))
        async def stats_handler(event):
            await self.handle_stats(event)

        @self.client.on(events.CallbackQuery)
        async def callback_handler(event):
            await self.handle_callback(event)

        # Keep bot running
        await self.client.run_until_disconnected()

    async def handle_start(self, event):
        """Handle /start command"""
        user_id = event.sender_id

        welcome_msg = """
🤖 **Welcome to Job Filter Bot!**

I help you find relevant job posts from Telegram channels.

**Commands:**
• `/search` - Search for jobs now
• `/config` - Setup your channels and keywords  
• `/stats` - View your search statistics
• `/help` - Show this help message

**Quick Setup:**
1. Use `/config` to set your channels and keywords
2. Use `/search` to find jobs
3. Get results as a nice formatted file!

Ready to start? Use the buttons below:
        """

        buttons = [
            [Button.inline("⚙️ Setup Config", b"setup_config")],
            [Button.inline("🔍 Search Jobs", b"search_jobs")],
            [Button.inline("📊 View Stats", b"view_stats")]
        ]

        await event.respond(welcome_msg, buttons=buttons)

    async def handle_config(self, event):
        """Handle configuration setup"""
        user_id = event.sender_id

        config_msg = """
⚙️ **Configuration Setup**

Send me your configuration in this format:

```
CHANNELS:
@channel1
@channel2
@channel3

KEYWORDS:
python
javascript
remote work
```

Or use buttons for quick setup:
        """

        buttons = [
            [Button.inline("📝 Use Default Config", b"default_config")],
            [Button.inline("📋 Show Current Config", b"show_config")],
            [Button.inline("🔙 Back to Menu", b"main_menu")]
        ]

        await event.respond(config_msg, buttons=buttons)

    async def handle_search(self, event):
        """Handle job search"""
        user_id = event.sender_id

        if user_id not in self.user_configs:
            await event.respond(
                "❌ No configuration found! Please setup your config first using `/config`",
                buttons=[[Button.inline("⚙️ Setup Config", b"setup_config")]]
            )
            return

        # Show searching message
        search_msg = await event.respond("🔍 Searching for jobs... Please wait")

        try:
            config = self.user_configs[user_id]
            filtered = await fetch_and_filter_messages(self.client, config)

            if not filtered:
                await search_msg.edit("❌ No jobs found matching your criteria")
                return

            # Generate report
            from report_generator import generate_html_report
            html_content = generate_html_report(filtered)

            # Send as file
            from io import BytesIO
            file_data = BytesIO(html_content.encode("utf-8"))
            filename = f"jobs_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

            await self.client.send_file(
                event.chat_id,
                file_data,
                caption=f"📄 Found {len(filtered)} jobs! Open the HTML file in your browser.",
                file_name=filename
            )

            await search_msg.delete()

        except Exception as e:
            await search_msg.edit(f"❌ Error during search: {str(e)}")

    async def handle_stats(self, event):
        """Handle statistics display"""
        user_id = event.sender_id

        # Load user stats (you'd implement this)
        stats_msg = """
📊 **Your Job Search Stats**

🎯 **This Week:**
• Jobs found: 25
• Channels searched: 5
• Top keyword: "python" (12 matches)

🏆 **All Time:**
• Total jobs: 150
• Success rate: 75%
• Best day: Monday (avg 8 jobs)

📈 **Trending:**
• Remote work ↗️ +15%
• Python jobs ↗️ +10%
        """

        buttons = [
            [Button.inline("🔍 Search Again", b"search_jobs")],
            [Button.inline("🔙 Back to Menu", b"main_menu")]
        ]

        await event.respond(stats_msg, buttons=buttons)

    async def handle_callback(self, event):
        """Handle inline button callbacks"""
        data = event.data.decode('utf-8')

        if data == "setup_config":
            await self.handle_config(event)
        elif data == "search_jobs":
            await self.handle_search(event)
        elif data == "view_stats":
            await self.handle_stats(event)
        elif data == "default_config":
            # Set a default configuration
            user_id = event.sender_id
            self.user_configs[user_id] = {
                "channels": ["@jobsearch", "@remotework"],
                "keywords": ["python", "javascript", "remote"],
                "message_limit": 50
            }
            await event.respond("✅ Default configuration set! You can now search for jobs.")
        elif data == "main_menu":
            await self.handle_start(event)


# Bot runner
async def run_bot():
    bot = JobFilterBot()
    await bot.start_bot()


if __name__ == "__main__":
    asyncio.run(run_bot())