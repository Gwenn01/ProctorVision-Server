# routes/file_routes.py
from flask import Blueprint, send_from_directory, abort, jsonify, request
from flask_cors import CORS
import fitz  # PyMuPDF
import os

# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------
file_bp = Blueprint("file_bp", __name__)
CORS(file_bp, resources={r"/*": {"origins": "*"}})

# Base uploads directory (relative-safe)
BASE_UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "exams")
os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------------------
# Serve PDF File (Safe)
# ---------------------------------------------------------------------
@file_bp.route("/uploads/exams/<path:filename>", methods=["GET"])
def serve_exam_file(filename):
    """Serve a PDF exam file from the uploads directory safely."""
    try:
        # Only allow PDF files
        if not filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are allowed."}), 400

        safe_path = os.path.join(BASE_UPLOAD_DIR, filename)

        if not os.path.isfile(safe_path):
            return jsonify({"error": "File not found."}), 404

        return send_from_directory(BASE_UPLOAD_DIR, filename, as_attachment=False)

    except Exception as e:
        print("❌ Error serving file:", str(e))
        return jsonify({"error": "Error serving file: " + str(e)}), 500


# ---------------------------------------------------------------------
# 2️Extract Text from Exam PDF
# ---------------------------------------------------------------------
@file_bp.route("/api/exam_text/<path:filename>", methods=["GET"])
def get_exam_text(filename):
    """Extract and return plain text from a PDF file."""
    try:
        if not filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are supported."}), 400

        pdf_path = os.path.join(BASE_UPLOAD_DIR, filename)
        if not os.path.isfile(pdf_path):
            return jsonify({"error": "PDF file not found."}), 404

        # Extract text safely
        text = []
        with fitz.open(pdf_path) as doc:
            for page in doc:
                page_text = page.get_text("text").strip()
                if page_text:
                    text.append(page_text)

        content = "\n\n".join(text)
        if not content.strip():
            return jsonify({"error": "No readable text found in this PDF."}), 422

        return jsonify({"filename": filename, "content": content}), 200

    except Exception as e:
        print("❌ Error reading PDF:", str(e))
        return jsonify({"error": "Failed to read PDF: " + str(e)}), 500
