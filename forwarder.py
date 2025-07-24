from io import BytesIO
from datetime import datetime

async def forward_messages(client, messages, destination):
    if not messages:
        return

    resolved = "me" if destination in ["saved_messages", "me"] else destination

    # Combine all messages into one text string
    content = ""
    for msg in messages:
        content += f"[{msg['channel']}] {msg['date']}\n{msg['text']}\n\n{'-'*40}\n\n"

    file_data = BytesIO(content.encode("utf-8"))
    filename = f"filtered_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    try:
        await client.send_file(resolved, file_data, caption=f"📄 Filtered job posts ({len(messages)})", file_name=filename)
        print(f"✅ Sent {len(messages)} messages as one file: {filename}")
    except Exception as e:
        print(f"❌ Failed to send file to {resolved}: {e}")
