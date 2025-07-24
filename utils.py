import yaml

def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_to_file(messages, filename="filtered_jobs.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        for msg in messages:
            f.write(f"[{msg['channel']}] {msg['date']}\n{msg['text']}\n\n")
    print(f"📄 Saved {len(messages)} messages to {filename}")
