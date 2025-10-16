from flask import Blueprint, request, jsonify
from services.behavior_service import save_behavior_log
from services.instructor_services import increment_suspicious_for_student

ai_bridge_bp = Blueprint("ai_bridge", __name__)

@ai_bridge_bp.route("/save_behavior_log", methods=["POST"])
def save_behavior_log_api():
    data = request.get_json()
    user_id = data.get("user_id")
    exam_id = data.get("exam_id")
    image_base64 = data.get("image_base64")
    warning_type = data.get("warning_type")

    if not all([user_id, exam_id, image_base64, warning_type]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        save_behavior_log(user_id, exam_id, image_base64, warning_type)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ai_bridge_bp.route("/increment_suspicious", methods=["POST"])
def increment_suspicious_api():
    data = request.get_json()
    student_id = data.get("student_id")
    if not student_id:
        return jsonify({"error": "Missing student_id"}), 400

    try:
        increment_suspicious_for_student(student_id)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
