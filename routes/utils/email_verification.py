from flask import Blueprint, request, jsonify, redirect
from database.connection import get_db_connection
import os
from datetime import datetime, timedelta

email_verification_bp = Blueprint("email_verification", __name__)

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://proctorvision-client.vercel.app")

@email_verification_bp.route("/verify", methods=["GET"])
def verify_account():
    token = request.args.get("token")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, is_verified FROM users WHERE verify_token = %s", (token,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "Invalid or expired token"}), 400
        
        # Check if token has expired (for example, 1 hour expiration)
        token_expiration_time = user[2] + timedelta(hours=1)  # Assuming created_at is stored as a datetime
        if datetime.now() > token_expiration_time:
            return jsonify({"error": "Expired token"}), 400

        if user[1]:  # already verified
            return redirect(f"{FRONTEND_URL}/verify-already")

        cursor.execute(
            """
            UPDATE users
            SET is_verified = TRUE, verify_token = NULL
            WHERE verify_token = %s
        """,
            (token,),
        )
        conn.commit()

        # Redirect to frontend success page
        return redirect(f"{FRONTEND_URL}/verify-success")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()
