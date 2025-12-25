from flask import Blueprint, jsonify

planner_bp = Blueprint("planner", __name__)

@planner_bp.route("/")
def planner():
    return jsonify({"message": "Study planner coming soon"})
