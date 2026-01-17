from flask import Blueprint, render_template

pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@pages_bp.route("/quiz", methods=["GET"])
def quiz_dashboard():
    return render_template("quiz_dashboard.html")
