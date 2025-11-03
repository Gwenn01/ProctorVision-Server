from flask import Blueprint, request, jsonify
from database.connection import get_db_connection  
import bcrypt  
from routes.utils.email_utils import send_verification_email
import uuid
import os

create_account_bp = Blueprint('create_account', __name__)

# Environment-based URLs (fall back to localhost for dev)
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://proctorvision-client.vercel.app")
BACKEND_URL = os.getenv("BACKEND_URL", "https://proctorvision-server-production.up.railway.app")

@create_account_bp.route("/create_account", methods=["POST"])
def create_account():
    data = request.get_json()

    required_fields = ["name", "username", "email", "password", "userType"]
    if data["userType"].lower() == "student":
        required_fields += ["course", "section", "year", "status"]

    # Validate required fields
    if not all(field in data and data[field] for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check for duplicates
        cursor.execute(
            "SELECT * FROM users WHERE username = %s OR email = %s",
            (data["username"], data["email"]),
        )
        if cursor.fetchone():
            return jsonify({"error": "Username or email already exists"}), 409

        raw_password = data["password"]
        hashed_pw = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt())

        # Insert into users (removed verify_token)
        cursor.execute(
            """
            INSERT INTO users (name, username, email, password, user_type, is_verified)
            VALUES (%s, %s, %s, %s, %s, %s)
        """,
            (
                data["name"],
                data["username"],
                data["email"],
                hashed_pw,
                data["userType"],
                False,  # is_verified = False by default
            ),
        )

        new_user_id = cursor.lastrowid  # Get the new user ID

        # If student, insert profile
        if data["userType"].lower() == "student":
            cursor.execute(
                """
                INSERT INTO student_profiles (user_id, course, section, year, status)
                VALUES (%s, %s, %s, %s, %s)
            """,
                (
                    new_user_id,
                    data["course"],
                    data["section"],
                    data["year"],
                    data["status"],
                ),
            )

        conn.commit()
        conn.close()

        # ✅ Send verification email with user_id in verification URL (removed token)
        verification_url = f"{BACKEND_URL}/api/verify?user_id={new_user_id}"

        send_verification_email(
            to_email=data["email"],
            name=data["name"],
            username=data["username"],
            password="Hidden for security",  # safer
            verification_url=verification_url,  # Use user_id instead of token
        )

        return jsonify(
            {
                "message": "Account created successfully. Please check your email for verification.",
                "user": {
                    "id": new_user_id,  # Include the user ID in the response
                    "name": data["name"],
                    "username": data["username"],
                    "email": data["email"],
                    "userType": data["userType"],
                },
            }
        ), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@create_account_bp.route("/bulk_create_students", methods=["POST"])
def bulk_create_students():
    data = request.get_json()
    students = data.get("students", [])
    meta = data.get("meta", {})

    required_meta = ["course", "section", "year", "status"]
    if not all(k in meta and meta[k] for k in required_meta):
        return jsonify({"error": "Missing course/section/year/status metadata"}), 400

    if not students:
        return jsonify({"error": "No student data provided"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        created_students = []

        for student in students:
            name = student.get("name")
            username = student.get("username")
            email = student.get("email")
            raw_password = student.get("password")

            # Skip if any essential field is missing
            if not all([name, username, email, raw_password]):
                continue

            # Skip if username or email already exists
            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
            if cursor.fetchone():
                continue

            hashed_pw = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt())

            # Insert into users table (no verify_token)
            cursor.execute(""" 
                INSERT INTO users (name, username, email, password, user_type, is_verified)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                name,
                username,
                email,
                hashed_pw,
                "Student",
                False  # is_verified = False by default
            ))

            user_id = cursor.lastrowid

            # Insert into student_profiles table
            cursor.execute("""
                INSERT INTO student_profiles (user_id, course, section, year, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user_id,
                meta["course"],
                meta["section"],
                meta["year"],
                meta["status"]
            ))

            # Append student info to return for frontend email sending
            created_students.append({
                "name": name,
                "email": email,
                "username": username,
                "password": raw_password,
                "user_id": user_id  # Include user_id here
            })

        conn.commit()
        conn.close()

        # Send verification email per created student (if backend returns them)
        if created_students:
            for student in created_students:
                verification_url = f"{BACKEND_URL}/api/verify?user_id={student['user_id']}"

                send_verification_email(
                    to_email=student["email"],
                    name=student["name"],
                    username=student["username"],
                    password="Hidden for security",  # safer
                    verification_url=verification_url,
                )

        return jsonify({
            "message": f"{len(created_students)} students added.",
            "created_students": created_students
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
