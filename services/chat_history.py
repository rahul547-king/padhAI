import json
import os
import uuid

CHAT_FILE = "chat_history.json"


def load_history():
    if not os.path.exists(CHAT_FILE):
        return []
    with open(CHAT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history):
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def generate_title(question: str) -> str:
    question = question.strip().rstrip("?")
    words = question.split()
    return " ".join(words[:6]).capitalize()


def create_new_chat(first_question):
    history = load_history()

    chat = {
        "id": str(uuid.uuid4()),
        "title": generate_title(first_question),
        "messages": [
            {"role": "user", "content": first_question}
        ]
    }

    history.append(chat)
    save_history(history)
    return chat


def add_message(chat_id, role, content):
    history = load_history()

    for chat in history:
        if chat["id"] == chat_id:
            chat["messages"].append({
                "role": role,
                "content": content
            })
            save_history(history)
            return


def get_chat(chat_id):
    history = load_history()
    for chat in history:
        if chat["id"] == chat_id:
            return chat
    return None
