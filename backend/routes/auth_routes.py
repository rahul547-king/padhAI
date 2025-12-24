from flask import Blueprint, jsonify

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    # Firebase auth handled on frontend
    return jsonify({"message": "Login handled by Firebase frontend"})
