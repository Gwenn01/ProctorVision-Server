from flask import Blueprint, request, jsonify
from database.connection import get_db_connection

# New blueprint name to avoid conflict
get_behavior_bp = Blueprint('get_behavior', __name__)

#  GET /api/get_behavior_logs - fetch suspicious behavior logs for a user
@get_behavior_bp.route('/get_behavior_logs', methods=['GET'])
def get_behavior_logs():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                sbl.exam_id,
                sbl.timestamp,
                sbl.warning_type,
                sbl.image_base64,
                 sbl.classification_label,
                e.title
            FROM suspicious_behavior_logs sbl
            JOIN exams e ON sbl.exam_id = e.id
            WHERE sbl.user_id = %s
            ORDER BY sbl.timestamp ASC
        """, (user_id,))
        
        logs = cursor.fetchall()
        conn.close()

        return jsonify(logs), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@get_behavior_bp.route('/get_exam_behavior_summary', methods=['GET'])
def get_exam_behavior_summary():
    exam_id = request.args.get('exam_id')

    if not exam_id:
        return jsonify({"error": "Missing exam_id"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # ✅ Fetch all behavior logs for this exam
        cursor.execute("""
            SELECT 
                sbl.user_id,
                sbl.exam_id,
                sbl.warning_type,
                sbl.classification_label,
                sbl.timestamp,
                e.title
            FROM suspicious_behavior_logs sbl
            JOIN exams e ON sbl.exam_id = e.id
            WHERE sbl.exam_id = %s
        """, (exam_id,))
        logs = cursor.fetchall()

        # ============================================
        # 📊 Aggregate Summary
        # ============================================
        total_students = len(set(log["user_id"] for log in logs))
        suspicious = len([log for log in logs if log["classification_label"] == "Suspicious"])
        clean = len([log for log in logs if log["classification_label"] == "Clean"])

        # 🧩 Count behavior types (No Face, Hand Detected, etc.)
        behavior_counts = {}
        for log in logs:
            w = log.get("warning_type", "Unknown")
            behavior_counts[w] = behavior_counts.get(w, 0) + 1

        # 🧠 Top suspicious students by count
        suspicious_by_student = {}
        for log in logs:
            uid = log["user_id"]
            if log["classification_label"] == "Suspicious":
                suspicious_by_student[uid] = suspicious_by_student.get(uid, 0) + 1

        top_students = sorted(
            [{"user_id": k, "count": v} for k, v in suspicious_by_student.items()],
            key=lambda x: x["count"],
            reverse=True
        )

        # ✅ Combine into response
        summary = {
            "exam_id": exam_id,
            "title": logs[0]["title"] if logs else "Unknown Exam",
            "total_students": total_students,
            "suspicious_count": suspicious,
            "clean_count": clean,
            "behavior_counts": behavior_counts,
            "top_students": top_students,
        }

        conn.close()
        return jsonify(summary), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
