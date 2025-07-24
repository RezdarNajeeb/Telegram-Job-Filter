from telethon import TelegramClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
keywords = [kw.strip().lower() for kw in os.getenv("KEYWORDS", "").split(",")]

client = TelegramClient("session", api_id, api_hash)

channels = [
    "kanyaw_organization",
    "IraqJobz",
    "allkurdistanjobs",
    "Bestwnjobs",
    "fjkurdistan10",
]

async def main():
    matched = []

    for channel in channels:
        try:
            async for msg in client.iter_messages(channel, limit=50):
                if msg.message:
                    text = msg.message.lower()
                    if any(keyword in text for keyword in keywords):
                        matched.append(f"[{channel}] {msg.date}:\n{msg.message}\n\n")
        except Exception as e:
            print(f"Error reading {channel}: {e}")

    with open("filtered_jobs.txt", "w", encoding="utf-8") as f:
        f.writelines(matched)

    print(f"✅ Done! {len(matched)} matching job posts saved to filtered_jobs.txt")

with client:
    client.loop.run_until_complete(main())
