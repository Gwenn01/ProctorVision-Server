import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"   # hide TF INFO/WARN
os.environ["GLOG_minloglevel"] = "2"  
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import mysql.connector
from database.connection import get_db_connection

# Initialize Flask app
app = Flask(__name__)
# Allow your frontend to call /api/* (tighten origins in prod)
CORS(
    app,
    resources={r"/api/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]}},
    supports_credentials=True,
)
# JWT Configuration
app.config["JWT_SECRET_KEY"] = "supersecretkey"
jwt = JWTManager(app)

# Test DB connection
@app.route("/test_connection", methods=["GET"])
def test_connection():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE();")
        current_db = cursor.fetchone()
        conn.close()
        return jsonify({"message": f"Connected to database: {current_db[0]}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------
# Register route blueprints
# ---------------------------------------------
from routes.create_account_routes import create_account_bp
from routes.auth_routes import auth_bp

# from routes.video_routes import video_bp

from routes.manage_users_routes import manage_users_bp
from routes.instructor_exam_routes import instructor_exam_bp
from routes.enrollment_routes import enrollment_bp
from routes.exam_routes import exam_bp
from routes.exam_instructions_routes import exam_instructions_bp
from routes.code_runner_routes import code_runner_bp
from routes.parse_instructions_routes import parse_instructions_bp
from routes.parse_question_routes import parse_question_bp
from routes.manage_exam_routes import manage_exam_routes
from routes.file_routes import file_bp
from routes.exam_students_routes import exam_students_bp
from routes.get_exam_routes import get_exam_bp
from routes.exam_submit_routes import exam_submit_bp
from routes.behavior_routes import behavior_bp
from routes.get_behavior_routes import get_behavior_bp
from routes.get_behavior_images import get_behavior_images_bp
from routes.instructor_student_behavior import instructor_behavior_bp
from routes.utils.email_verification import email_verification_bp
from routes.exam_question_routes import exam_questions_bp

# NEW: WebRTC blueprint (streams student camera to server)

app.register_blueprint(create_account_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api')

# app.register_blueprint(video_bp, url_prefix='/api')

app.register_blueprint(manage_users_bp, url_prefix="/api")
app.register_blueprint(instructor_exam_bp, url_prefix='/api')
app.register_blueprint(enrollment_bp, url_prefix="/api")
app.register_blueprint(exam_bp, url_prefix="/api")
app.register_blueprint(parse_instructions_bp, url_prefix="/api")
app.register_blueprint(parse_question_bp, url_prefix="/api")
app.register_blueprint(exam_instructions_bp, url_prefix="/api")
app.register_blueprint(code_runner_bp, url_prefix="/api")
app.register_blueprint(manage_exam_routes, url_prefix='/api')
app.register_blueprint(file_bp)
app.register_blueprint(exam_students_bp, url_prefix='/api')
app.register_blueprint(get_exam_bp, url_prefix='/api')
app.register_blueprint(exam_submit_bp, url_prefix="/api")
app.register_blueprint(behavior_bp, url_prefix='/api')
app.register_blueprint(get_behavior_bp, url_prefix='/api')
app.register_blueprint(get_behavior_images_bp, url_prefix="/api")
app.register_blueprint(instructor_behavior_bp, url_prefix="/api")
app.register_blueprint(email_verification_bp, url_prefix="/api")
app.register_blueprint(exam_questions_bp, url_prefix="/api")

# Register WebRTC endpoints last (organization preference)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


