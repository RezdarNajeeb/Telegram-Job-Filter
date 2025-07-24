from io import BytesIO
from datetime import datetime
from report_generator import generate_html_report
from telethon.tl.types import DocumentAttributeFilename

async def forward_messages(client, messages, destination):
    if not messages:
        return

    resolved = "me" if destination in ["saved_messages", "me"] else destination

    try:
        # ✅ Generate HTML report
        html_content = generate_html_report(messages)
        html_file = BytesIO(html_content.encode("utf-8"))
        html_filename = f"job_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        # ✅ Send HTML report
        await client.send_file(
            resolved,
            html_file,
            caption=f"📄 Job Report - {len(messages)} jobs found! Open in browser for best view.",
            file_name=html_filename,
            force_document=True,
            attributes=[
                DocumentAttributeFilename(file_name=html_filename)
            ]
        )

        # ✅ Send summary message
        summary = generate_summary_message(messages)
        await client.send_message(resolved, summary)

        print(f"✅ Sent HTML report with {len(messages)} jobs to {resolved}")

    except Exception as e:
        print(f"❌ Failed to send HTML report to {resolved}: {e}")
        # 🔁 Only send fallback if HTML failed
        await send_text_fallback(client, messages, resolved)


async def send_text_fallback(client, messages, destination):
    """Fallback to text format if HTML fails"""
    try:
        content = ""
        for msg in messages:
            content += f"[{msg['channel']}] {msg['date']}\n{msg['text']}\n\n{'-' * 40}\n\n"

        file_data = BytesIO(content.encode("utf-8"))
        filename = f"filtered_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        await client.send_file(destination, file_data, caption=f"📄 Job Posts ({len(messages)})", file_name=filename)
        print(f"✅ Sent text fallback with {len(messages)} messages")
    except Exception as e:
        print(f"❌ Text fallback also failed: {e}")


def generate_summary_message(messages):
    """Generate a quick summary message"""
    if not messages:
        return "❌ No jobs found"

    # Group by channel
    channels = {}
    total_with_contact = 0
    all_keywords = []

    for msg in messages:
        channel = msg['channel']
        channels[channel] = channels.get(channel, 0) + 1
        if msg.get('has_contact'):
            total_with_contact += 1
        all_keywords.extend(msg.get('matched_keywords', []))

    # Most common keywords
    from collections import Counter
    top_keywords = Counter(all_keywords).most_common(3)

    summary = f"""```🎯 **Job Search Results**

📊 **Summary:**
• Total jobs found: {len(messages)}
• Jobs with contact info: {total_with_contact} ({total_with_contact / len(messages) * 100:.1f}%)
• Channels searched: {len(channels)}

📈 **Top Channels:**
"""

    for channel, count in list(channels.items())[:3]:
        summary += f"• {channel}: {count} jobs\n"

    if top_keywords:
        summary += f"\n🔥 **Most Matched Keywords:**\n"
        for keyword, count in top_keywords:
            summary += f"• {keyword}: {count} times\n"

    summary += f"\n💡 Open the HTML file above for detailed view with clickable links!```"

    return summary