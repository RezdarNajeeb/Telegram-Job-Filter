import asyncio
import os
import re
from datetime import datetime
from io import BytesIO
from typing import Dict, List

from dotenv import load_dotenv
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError

# Import your existing modules here (implement or adjust as needed)
from job_filter import fetch_and_filter_messages
from report_generator import generate_html_report
from stats_tracker import JobStats

load_dotenv()

class JobFilterBot:
    def __init__(self):
        self.api_id = int(os.getenv("API_ID"))
        self.api_hash = os.getenv("API_HASH")
        self.bot_token = os.getenv("BOT_TOKEN")

        # User client session for fetching messages (phone login)
        # The session string can be saved/loaded from a file
        self.user_session_file = "user_client.session"
        self.user_client = TelegramClient(
            self.user_session_file, self.api_id, self.api_hash
        )

        # Bot client to interact with users
        self.bot_client = TelegramClient("bot_session", self.api_id, self.api_hash)

        # Per user configs and stats
        self.user_configs: Dict[int, Dict] = {}
        self.user_stats: Dict[int, JobStats] = {}

    async def start(self):
        # Start user client first (login if needed)
        await self.user_client.start()
        if not await self.user_client.is_user_authorized():
            print("User client not authorized. Please complete login.")
            await self.user_client.send_code_request(input("Enter phone number: "))
            try:
                await self.user_client.sign_in(
                    phone=input("Enter phone number: "),
                    code=input("Enter code you received: "),
                )
            except SessionPasswordNeededError:
                await self.user_client.sign_in(password=input("Two-step password: "))

        print("✅ User client authorized and started.")

        # Start bot client
        await self.bot_client.start(bot_token=self.bot_token)
        me = await self.bot_client.get_me()
        print(f"🤖 Bot started as @{me.username}")

        # Register event handlers on bot client
        self.register_handlers()

        print("🚀 Bot is running! Users can start chatting with it.")
        await self.bot_client.run_until_disconnected()

    def register_handlers(self):
        @self.bot_client.on(events.NewMessage(pattern="/start"))
        async def start_handler(event):
            await self.handle_start(event)

        @self.bot_client.on(events.NewMessage(pattern="/help"))
        async def help_handler(event):
            await self.handle_start(event)

        @self.bot_client.on(events.NewMessage(pattern="/config"))
        async def config_handler(event):
            await self.handle_config_setup(event)

        @self.bot_client.on(events.NewMessage(pattern="/search"))
        async def search_handler(event):
            await self.handle_search(event)

        @self.bot_client.on(events.NewMessage(pattern="/stats"))
        async def stats_handler(event):
            await self.handle_stats(event)

        @self.bot_client.on(events.NewMessage(pattern="/status"))
        async def status_handler(event):
            await self.handle_status(event)

        @self.bot_client.on(events.NewMessage())
        async def config_message_handler(event):
            if re.search(r"^(CHANNELS|channels):", event.message.message, re.MULTILINE):
                await self.parse_config_message(event)

        @self.bot_client.on(events.CallbackQuery)
        async def callback_handler(event):
            await self.handle_callback(event)

    async def handle_start(self, event):
        user = await event.get_sender()
        user_id = user.id

        welcome_msg = f"""
👋 **Welcome to Job Filter Bot, {user.first_name}!**

🎯 I help you find relevant job posts from Telegram channels automatically.

**🚀 Quick Start:**
1. Set up your channels and keywords with `/config`
2. Search for jobs with `/search`
3. Get beautiful HTML reports directly here!

**📋 Commands:**
• `/config` - Set up channels and keywords
• `/search` - Find jobs matching your criteria
• `/stats` - View your search statistics
• `/status` - Check your current settings
• `/help` - Show this help message

**💡 Features:**
✅ Smart keyword matching (IT, C++, .NET)
✅ Beautiful HTML reports
✅ Statistics tracking
✅ Contact info detection
✅ Direct links to original posts

Ready to find your dream job? 🚀
        """

        buttons = [
            [Button.inline("⚙️ Setup Config", b"setup_config")],
            [Button.inline("🔍 Search Jobs", b"search_jobs")],
            [Button.inline("📊 View Stats", b"view_stats")],
        ]

        await event.respond(welcome_msg, buttons=buttons)

    async def handle_config_setup(self, event):
        config_msg = """
⚙️ **Configuration Setup**

Send me your configuration in this format:

CHANNELS:
@jobsearch
@remotework
@python_jobs

KEYWORDS:
Python
JavaScript
remote work
IT
C++
.NET

**📝 Tips:**
• Use @ for channel usernames
• One item per line
• Keywords are smart-matched (IT won't match "opportunity")
• Technical terms like C++, .NET work perfectly

Or use quick setup buttons below:
        """

        buttons = [
            [Button.inline("🛠️ Tech Jobs Config", b"tech_config")],
            [Button.inline("🌍 Remote Work Config", b"remote_config")],
            [Button.inline("📋 Show Current Config", b"show_config")],
        ]

        await event.respond(config_msg, buttons=buttons)

    async def parse_config_message(self, event):
        user_id = event.sender_id
        text = event.message.message

        try:
            config = self.parse_user_config(text)
            self.user_configs[user_id] = config

            # Save config (optional)
            await self.save_user_config(user_id, config)

            summary = f"""
✅ **Configuration Saved!**

📡 **Channels ({len(config['channels'])}):**
{chr(10).join(f'• {ch}' for ch in config['channels'][:5])}
{'• ... and more' if len(config['channels']) > 5 else ''}

🎯 **Keywords ({len(config['keywords'])}):**
{chr(10).join(f'• {kw}' for kw in config['keywords'][:8])}
{'• ... and more' if len(config['keywords']) > 8 else ''}

⚙️ **Settings:**
• Message limit: {config.get('message_limit', 50)} per channel

Ready to search? Use `/search` or the button below!
            """

            buttons = [[Button.inline("🔍 Search Now", b"search_jobs")]]
            await event.respond(summary, buttons=buttons)

        except Exception as e:
            await event.respond(
                f"❌ **Config Error:** {str(e)}\n\nPlease check the format and try again."
            )

    def parse_user_config(self, text: str) -> Dict:
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        config = {"channels": [], "keywords": [], "message_limit": 50}
        current_section = None

        for line in lines:
            line_lower = line.lower()
            if line_lower.startswith("channels:") or line_lower.startswith("channel:"):
                current_section = "channels"
                continue
            elif line_lower.startswith("keywords:") or line_lower.startswith("keyword:"):
                current_section = "keywords"
                continue
            elif line_lower.startswith("limit:"):
                try:
                    config["message_limit"] = int(line.split(":", 1)[1].strip())
                except:
                    pass
                continue

            if current_section and line:
                if current_section == "channels":
                    channel = line.strip()
                    if not channel.startswith("@"):
                        channel = "@" + channel
                    config["channels"].append(channel)
                elif current_section == "keywords":
                    config["keywords"].append(line.strip())

        if not config["channels"]:
            raise ValueError("No channels specified")
        if not config["keywords"]:
            raise ValueError("No keywords specified")

        return config

    async def handle_search(self, event):
        user_id = event.sender_id

        if user_id not in self.user_configs:
            await event.respond(
                "❌ **No configuration found!**\n\nPlease set up your channels and keywords first.",
                buttons=[[Button.inline("⚙️ Setup Config", b"setup_config")]],
            )
            return

        search_msg = await event.respond(
            "🔍 **Searching for jobs...**\n\nPlease wait, this may take a moment..."
        )

        try:
            config = self.user_configs[user_id]

            # Use user client to fetch and filter messages (hybrid approach)
            filtered = await fetch_and_filter_messages(self.user_client, config)

            if not filtered:
                await search_msg.edit(
                    "❌ **No jobs found** matching your criteria.\n\nTry adjusting your keywords or checking different channels.",
                    buttons=[[Button.inline("⚙️ Update Config", b"setup_config")]],
                )
                return

            # Update stats
            if user_id not in self.user_stats:
                self.user_stats[user_id] = JobStats(f"user_{user_id}_stats.json")
            self.user_stats[user_id].update_stats(filtered)

            # Generate HTML report
            html_content = generate_html_report(filtered)
            html_file = BytesIO(html_content.encode("utf-8"))
            filename = f"jobs_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

            await self.bot_client.send_file(
                event.chat_id,
                html_file,
                caption=f"📄 **Job Report Generated!**\n\n🎯 Found **{len(filtered)}** matching jobs\n💡 Open the HTML file in your browser for best experience",
                file_name=filename,
                force_document=True,
            )

            # Send summary
            summary = self.generate_search_summary(filtered)
            await self.bot_client.send_message(event.chat_id, summary)

            await search_msg.delete()

        except Exception as e:
            await search_msg.edit(
                f"❌ **Search Error:** {str(e)}\n\nPlease try again or contact support."
            )

    def generate_search_summary(self, messages: List[Dict]) -> str:
        if not messages:
            return "❌ No jobs found"

        channels = {}
        total_with_contact = 0
        all_keywords = []

        for msg in messages:
            channel = msg["channel"]
            channels[channel] = channels.get(channel, 0) + 1
            if msg.get("has_contact"):
                total_with_contact += 1
            all_keywords.extend(msg.get("matched_keywords", []))

        from collections import Counter

        top_keywords = Counter(all_keywords).most_common(3)

        summary = f"""🎯 **Search Results Summary**

📊 **Overview:**
• **{len(messages)}** jobs found
• **{total_with_contact}** with contact info ({total_with_contact / len(messages) * 100:.1f}%)
• **{len(channels)}** channels searched

📈 **Top Channels:**
"""

        for channel, count in list(channels.items())[:3]:
            summary += f"• {channel}: {count} jobs\n"

        if top_keywords:
            summary += f"\n🔥 **Most Matched:**\n"
            for keyword, count in top_keywords:
                summary += f"• {keyword}: {count}×\n"

        summary += f"\n💡 **Next Steps:**\n• Open the HTML file above\n• Click links to view original posts\n• Apply to jobs with contact info!"

        return summary

    async def handle_callback(self, event):
        data = event.data.decode("utf-8")
        user_id = event.sender_id

        if data == "setup_config":
            await self.handle_config_setup(event)
        elif data == "search_jobs":
            await self.handle_search(event)
        elif data == "view_stats":
            await self.handle_stats(event)
        elif data == "tech_config":
            tech_config = {
                "channels": ["@python_jobs", "@javascript_jobs", "@remote_work"],
                "keywords": ["Python", "JavaScript", "React", "Node.js", "IT", "backend", "frontend"],
                "message_limit": 50,
            }
            self.user_configs[user_id] = tech_config
            await event.respond(
                "✅ **Tech Jobs Config Applied!**\n\nYou can now search or customize further with `/config`"
            )
        elif data == "remote_config":
            remote_config = {
                "channels": ["@remote_work", "@remotejobs", "@freelance_jobs"],
                "keywords": ["remote", "work from home", "freelance", "online", "digital nomad"],
                "message_limit": 50,
            }
            self.user_configs[user_id] = remote_config
            await event.respond(
                "✅ **Remote Work Config Applied!**\n\nYou can now search or customize further with `/config`"
            )
        elif data == "show_config":
            await self.show_current_config(event)

    async def handle_stats(self, event):
        user_id = event.sender_id

        if user_id not in self.user_stats:
            await event.respond(
                "📊 **No statistics yet!**\n\nStart searching for jobs to see your stats.",
                buttons=[[Button.inline("🔍 Search Jobs", b"search_jobs")]],
            )
            return

        stats = self.user_stats[user_id]
        summary = stats.get_summary()

        buttons = [
            [Button.inline("🔍 Search Again", b"search_jobs")],
            [Button.inline("⚙️ Update Config", b"setup_config")],
        ]

        await event.respond(f"📊 **Your Statistics**\n\n{summary}", buttons=buttons)

    async def handle_status(self, event):
        user_id = event.sender_id
        await self.show_current_config(event)

    async def show_current_config(self, event):
        user_id = event.sender_id

        if user_id not in self.user_configs:
            await event.respond(
                "❌ **No configuration set!**\n\nUse `/config` to set up your channels and keywords.",
                buttons=[[Button.inline("⚙️ Setup Config", b"setup_config")]],
            )
            return

        config = self.user_configs[user_id]

        config_text = f"""
⚙️ **Current Configuration**

📡 **Channels ({len(config['channels'])}):**
{chr(10).join(f'• {ch}' for ch in config['channels'])}

🎯 **Keywords ({len(config['keywords'])}):**
{chr(10).join(f'• {kw}' for kw in config['keywords'])}

⚙️ **Settings:**
• Message limit: {config.get('message_limit', 50)} per channel
        """

        buttons = [
            [Button.inline("🔍 Search Jobs", b"search_jobs")],
            [Button.inline("✏️ Edit Config", b"setup_config")],
        ]

        await event.respond(config_text, buttons=buttons)

    async def save_user_config(self, user_id: int, config: Dict):
        # Optional: save user config to file or DB
        pass


async def main():
    bot = JobFilterBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")


if __name__ == "__main__":
    print("🚀 Starting Job Filter Bot...")
    asyncio.run(main())
