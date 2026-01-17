from __future__ import annotations

import json
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, g

from auth_routes import require_auth
from gemini_client import generate_answer
from firebase_init import get_db

planner_bp = Blueprint("planner", __name__, url_prefix="/planner")


@planner_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Planner route ready"})


def _extract_first_json_object(text: str):
    t = (text or "").strip()
    if t.startswith("{") and t.endswith("}"):
        return t
    first = t.find("{")
    last = t.rfind("}")
    if first != -1 and last != -1 and last > first:
        return t[first:last + 1]
    return None


@planner_bp.route("/generate", methods=["POST"])
@require_auth
def generate_plan():
    data = request.get_json(force=True)

    syllabus_text = (data.get("syllabus_text") or "").strip()
    if not syllabus_text:
        return jsonify({"error": "syllabus_text is required"}), 400

    hours_per_day = float(data.get("hours_per_day") or 2)
    days_per_week = int(data.get("days_per_week") or 6)
    weeks = int(data.get("weeks") or 4)
    goal = (data.get("goal") or "Exam preparation").strip()

    uid = g.uid

    prompt = f"""
You are a university study planner.

Create an adaptive study plan from the syllabus.

STRICT RULES:
- Output MUST be valid JSON only (no markdown, no extra text).
- Keep it realistic.

Inputs:
- Goal: {goal}
- Weeks: {weeks}
- Days per week: {days_per_week}
- Hours per day: {hours_per_day}

Return JSON schema:
{{
  "title": "string",
  "weeks": [
    {{
      "week": 1,
      "focus": "string",
      "days": [
        {{"day": "Mon", "topics": ["..."], "tasks": ["..."], "hours": number}}
      ]
    }}
  ],
  "tips": ["...", "..."],
  "revision_strategy": ["...", "..."]
}}

Syllabus:
{syllabus_text}
""".strip()

    try:
        model_text = generate_answer(prompt)
        json_blob = _extract_first_json_object(model_text)
        if not json_blob:
            return jsonify({"error": "Planner generation failed. Try again."}), 400
        plan = json.loads(json_blob)
    except Exception as e:
        return jsonify({"error": f"Planner generation failed: {e}"}), 500

    # Save plan in Firestore
    try:
        db = get_db()
        ref = db.collection("users").document(uid).collection("plans").document()
        ref.set({
            "title": plan.get("title") or "Study Plan",
            "plan": plan,
            "createdAt": datetime.now(timezone.utc),
        })
        plan_id = ref.id
    except Exception:
        plan_id = None

    return jsonify({"plan_id": plan_id, "plan": plan})
