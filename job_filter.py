import re


def normalize_keywords(keywords):
    return [kw.strip().lower() for kw in keywords]

async def fetch_and_filter_messages(client, config):
    results = []
    channels = config["channels"]
    keywords = normalize_keywords(config["keywords"])
    limit = config.get("message_limit", 50)

    for channel in channels:
        try:
            async for msg in client.iter_messages(channel, limit=limit):
                if msg.message:
                    text = msg.message.lower()
                    if any(kw in text for kw in keywords):
                        # In job_filter.py - collect more useful data
                        results.append({
                            "channel": channel,
                            "text": msg.message,
                            "date": str(msg.date),
                            "id": msg.id,
                            "url": f"https://t.me/{channel.replace('@', '')}/{msg.id}",  # Direct link
                            "matched_keywords": [kw for kw in keywords if kw in text],  # Which keywords matched
                            "word_count": len(msg.message.split()),
                            "has_contact": bool(
                                re.search(r'@\w+|https?://|t\.me/|[\w.-]+@[\w.-]+|\bwww\.\w+\.\w+\b', msg.message))
                            # Has contact info (Telegram, email, website)
                        })
        except Exception as e:
            print(f"❌ Error with {channel}: {e}")
    return results
