from telethon import TelegramClient
import os
from dotenv import load_dotenv

load_dotenv()

def get_client():
    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    return TelegramClient("session", api_id, api_hash)
