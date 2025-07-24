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
                    matched_keywords = [kw for kw in keywords if kw in text]

                    if matched_keywords:  # Only if keywords match
                        # Check for contact information
                        has_contact = bool(re.search(r'@\w+|https?://|t\.me/|\+\d+|\b\d{10,}\b|email|gmail|website|\bon\b', msg.message.lower()))

                        results.append({
                            "channel": channel,
                            "text": msg.message,
                            "date": str(msg.date),
                            "id": msg.id,
                            "url": f"https://t.me/{channel.replace('@', '')}/{msg.id}",
                            "matched_keywords": matched_keywords,
                            "word_count": len(msg.message.split()),
                            "has_contact": has_contact
                        })
        except Exception as e:
            print(f"❌ Error with {channel}: {e}")

    return results