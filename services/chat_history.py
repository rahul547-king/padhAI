import json
import os

CHAT_FILE = "chat_history.json"

def load_history():
    if not os.path.exists(CHAT_FILE):
        return []
    with open(CHAT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_message(question, answer):
    history = load_history()
    history.append({
        "question": question,
        "answer": answer
    })
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
