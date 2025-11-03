from flask import Blueprint, request, jsonify, redirect
from database.connection import get_db_connection
import os

email_verification_bp = Blueprint("email_verification", __name__)

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://proctorvision-client.vercel.app")

@email_verification_bp.route("/verify", methods=["GET"])
def verify_account():
    # Fetch the user identifier (either user_id or email)
    user_id = request.args.get("user_id")

    try:
        # Validate that user_id is provided
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the user exists in the database
        cursor.execute("SELECT id, is_verified FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 400  # User doesn't exist

        if user[1]:  # already verified
            return redirect(f"{FRONTEND_URL}/verify-already")

        # Update the user to mark them as verified
        cursor.execute(
            """
            UPDATE users
            SET is_verified = TRUE
            WHERE id = %s
        """,
            (user_id,),
        )
        conn.commit()

        # Redirect to frontend success page
        return redirect(f"{FRONTEND_URL}/verify-success")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()
