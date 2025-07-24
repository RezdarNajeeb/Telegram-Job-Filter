async def forward_messages(client, messages, destination):
    if not messages:
        return

    for msg in messages:
        try:
            await client.send_message(destination, f"[{msg['channel']}] {msg['date']}\n\n{msg['text']}")
        except Exception as e:
            print(f"❌ Failed to send to {destination}: {e}")
