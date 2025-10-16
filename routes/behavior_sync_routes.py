from flask import Blueprint, request, jsonify
from database.connection import get_db_connection

behavior_sync_bp = Blueprint("behavior_sync", __name__)

# 1️⃣  Fetch behavior logs (for classification)
@behavior_sync_bp.route("/fetch_behavior_logs", methods=["GET"])
def fetch_behavior_logs():
    user_id = request.args.get("user_id")
    exam_id = request.args.get("exam_id")
    if not user_id or not exam_id:
        return jsonify({"error": "Missing user_id or exam_id"}), 400

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, image_base64
        FROM suspicious_behavior_logs
        WHERE user_id=%s AND exam_id=%s AND image_base64 IS NOT NULL
    """, (user_id, exam_id))
    logs = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({"logs": logs})


# 2️⃣  Update classification results (called after Hugging Face predicts)
@behavior_sync_bp.route("/update_classifications", methods=["POST"])
def update_classifications():
    data = request.get_json(silent=True) or {}
    updates = data.get("updates", [])
    if not updates:
        return jsonify({"error": "No updates provided"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    for row in updates:
        try:
            log_id = row["id"]
            label = row["label"]
            cur.execute(
                "UPDATE suspicious_behavior_logs SET classification_label=%s WHERE id=%s",
                (label, log_id),
            )
        except Exception as e:
            print(f"⚠️ Update failed for log {log_id}: {e}")
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": f"{len(updates)} classifications updated."})
