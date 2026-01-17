from flask import Blueprint, jsonify, request, g
from firebase_admin import auth

# Local (this repo) firebase initializer
from firebase_init import init_firebase

auth_bp = Blueprint("auth", __name__)

# init once
init_firebase()


def require_auth(fn):
    """Decorator: requires Authorization: Bearer <firebase_id_token>"""
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Missing Bearer token"}), 401

        token = header.replace("Bearer ", "").strip()
        try:
            decoded = auth.verify_id_token(token)
            g.uid = decoded["uid"]
        except Exception:
            return jsonify({"error": "Invalid/expired token"}), 401

        return fn(*args, **kwargs)

    wrapper.__name__ = fn.__name__
    return wrapper


@auth_bp.route("/login", methods=["POST"])
def login():
    # Login handled in frontend (Firebase Auth)
    return jsonify({"message": "Login handled by Firebase frontend"})
