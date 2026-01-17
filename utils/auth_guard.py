from functools import wraps
from flask import request, jsonify, g
from firebase_admin import auth as fb_auth

from firebase_init import ensure_firebase


def require_firebase_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # 🔐 Always ensure Firebase Admin is initialized
        ensure_firebase()

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing Bearer token"}), 401

        token = auth_header.replace("Bearer ", "").strip()
        try:
            decoded = fb_auth.verify_id_token(token)
        except Exception:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Attach user to request context
        g.user = {
            "uid": decoded.get("uid"),
            "email": decoded.get("email"),
            "name": decoded.get("name"),
        }

        return fn(*args, **kwargs)

    return wrapper
