from datetime import datetime, timezone

# Local (this repo)
from firebase_init import get_db

def _now():
    return datetime.now(timezone.utc)

def create_chat(uid: str, title: str, active_doc_id: str | None = None) -> str:
    db = get_db()
    chat_ref = db.collection("users").document(uid).collection("chats").document()
    chat_ref.set({
        "title": title,
        "activeDocId": active_doc_id,
        "createdAt": _now(),
        "updatedAt": _now(),
    })
    return chat_ref.id

def add_message(uid: str, chat_id: str, role: str, content: str, citations=None):
    db = get_db()
    citations = citations or []
    msg_ref = (
        db.collection("users").document(uid)
        .collection("chats").document(chat_id)
        .collection("messages").document()
    )
    msg_ref.set({
        "role": role,
        "content": content,
        "citations": citations,
        "createdAt": _now(),
    })

    # bump updatedAt
    db.collection("users").document(uid).collection("chats").document(chat_id).update({
        "updatedAt": _now()
    })

def list_chats(uid: str, limit: int = 30):
    db = get_db()
    chats = (
        db.collection("users").document(uid)
        .collection("chats")
        .order_by("updatedAt", direction="DESCENDING")
        .limit(limit)
        .stream()
    )
    out = []
    for c in chats:
        d = c.to_dict()
        d["id"] = c.id
        out.append(d)
    return out

def get_chat(uid: str, chat_id: str, message_limit: int = 50):
    db = get_db()
    chat_ref = db.collection("users").document(uid).collection("chats").document(chat_id)
    chat_doc = chat_ref.get()
    if not chat_doc.exists:
        return None

    chat = chat_doc.to_dict()
    chat["id"] = chat_id

    msgs = (
        chat_ref.collection("messages")
        .order_by("createdAt")
        .limit(message_limit)
        .stream()
    )
    chat["messages"] = [m.to_dict() for m in msgs]
    return chat
