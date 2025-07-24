import re
from typing import List, Dict, Any


def normalize_keywords(keywords):
    """Normalize and precompile regex patterns for smart matching"""
    normalized = []
    for kw in keywords:
        kw = kw.strip()
        if not kw:
            continue

        is_acronym = kw.isupper() and len(kw) <= 5
        is_short = len(kw) <= 3
        has_special_chars = bool(re.search(r'[./\-+#]', kw))

        # Build regex pattern based on keyword type
        if is_acronym:
            pattern = re.compile(rf'(?<!\w){re.escape(kw)}(?!\w)')
        elif is_short:
            pattern = re.compile(rf'(?i)(?<!\w){re.escape(kw.lower())}(?!\w)')
        elif has_special_chars:
            # Escape all parts and allow optional whitespace around symbols
            flexible = re.sub(r'([./+\-#])', r'\\s*\1\\s*', re.escape(kw))
            pattern = re.compile(rf'(?i)(?<!\w){flexible}(?!\w)')
        else:
            pattern = re.compile(re.escape(kw), re.IGNORECASE)

        normalized.append({
            'original': kw,
            'regex': pattern
        })

    return normalized

def is_keyword_match(text: str, keyword_info: Dict) -> bool:
    return bool(keyword_info['regex'].search(text))

def find_matched_keywords(text: str, normalized_keywords: List[Dict]) -> List[str]:
    """Find all keywords that match in the text"""
    matched = []
    for kw_info in normalized_keywords:
        if is_keyword_match(text, kw_info):
            matched.append(kw_info['original'])  # Return original case
    return matched


async def fetch_and_filter_messages(client, config):
    results = []
    channels = config["channels"]
    keywords = normalize_keywords(config["keywords"])
    limit = config.get("message_limit", 50)

    print(f"🔍 Searching with keywords: {[kw['original'] for kw in keywords]}")

    for channel in channels:
        try:
            print(f"📡 Searching in {channel}...")
            message_count = 0

            async for msg in client.iter_messages(channel, limit=limit):
                message_count += 1
                if msg.message:
                    matched_keywords = find_matched_keywords(msg.message, keywords)

                    if matched_keywords:  # Only if keywords match
                        # Check for contact information
                        has_contact = bool(re.search(
                            r'@\w+|https?://|t\.me/|\+\d+|\b\d{10,}\b|contact|apply|email',
                            msg.message,
                            re.IGNORECASE
                        ))

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

            print(
                f"✅ {channel}: Found {len([r for r in results if r['channel'] == channel])} matches from {message_count} messages")

        except Exception as e:
            print(f"❌ Error with {channel}: {e}")

    return results


# Test function to verify keyword matching
def test_keyword_matching():
    """Test the keyword matching logic"""
    test_keywords = ["IT", "Python", "javascript", "C++", ".NET", "UI/UX", "AI", "remote work"]
    normalized = normalize_keywords(test_keywords)

    test_texts = [
        "Looking for IT specialist",
        "Need Python developer",
        "JavaScript and Python skills required",
        "C++ programmer wanted",
        ".NET developer position",
        "UI/UX designer needed",
        "AI engineer remote position",
        "Remote work available",
        "This is a great opportunity",  # Should not match "IT" in "opportunity"
        "Digital marketing position",  # Should not match "IT" in "Digital"
        "C ++ developer needed",  # Should match C++
        "DotNet and .NET experience",  # Should match .NET
    ]

    print("🧪 Testing keyword matching:")
    for text in test_texts:
        matches = find_matched_keywords(text, normalized)
        print(f"Text: '{text}' → Matches: {matches}")


if __name__ == "__main__":
    # Run tests
    test_keyword_matching()