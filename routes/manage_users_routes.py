from flask import Blueprint, request, jsonify
from database.connection import get_db_connection

manage_users_bp = Blueprint('manage_users', __name__)

#  unified: Get all users or filter 
@manage_users_bp.route("/users", methods=["GET"])
def get_users():
    role = request.args.get("role")
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if role == "Student":
            cursor.execute("""
                SELECT 
                    users.id, users.name, users.username, users.email, users.user_type AS role,
                    sp.course, sp.section, sp.year, sp.status
                FROM users
                JOIN student_profiles sp ON users.id = sp.user_id
                WHERE users.user_type = %s
            """, (role,))
        elif role:
            cursor.execute("""
                SELECT id, name, username, email, user_type AS role
                FROM users
                WHERE user_type = %s
            """, (role,))
        else:
            cursor.execute("""
                SELECT id, name, username, email, user_type AS role
                FROM users
            """)

        users = cursor.fetchall()
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
            
@manage_users_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Remove related assignments
        cursor.execute("DELETE FROM instructor_assignments WHERE student_id = %s", (user_id,))

        # Optional: remove from student_profiles
        cursor.execute("DELETE FROM student_profiles WHERE user_id = %s", (user_id,))

        # Then delete user
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()

        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()
        
@manage_users_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()
    name = data.get("name")
    username = data.get("username")
    email = data.get("email")

    if not name or not username or not email:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update the users table
        cursor.execute("""
            UPDATE users
            SET name = %s, username = %s, email = %s
            WHERE id = %s
        """, (name, username, email, user_id))
        
        conn.commit()

        return jsonify({"message": "User updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()




