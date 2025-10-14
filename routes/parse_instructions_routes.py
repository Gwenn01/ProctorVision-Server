# routes/parse_instructions_routes.py
from flask import Blueprint, request, jsonify
from flask_cors import CORS
from pypdf import PdfReader
from docx import Document
import io, os

# ---------------------------------------------------------------------
# Setup Blueprint
# ---------------------------------------------------------------------
parse_instructions_bp = Blueprint("parse_instructions", __name__)
CORS(parse_instructions_bp, resources={r"/*": {"origins": "*"}})

# Allowed file types (no external dependencies)
ALLOWED = {".pdf", ".docx", ".txt"}

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _normalize(text: str) -> str:
    """Normalize line breaks and strip whitespace."""
    return "\n".join((text or "").splitlines()).strip()


def _extract_from_docx(raw_bytes: bytes) -> str:
    """Extract text from DOCX bytes."""
    try:
        doc = Document(io.BytesIO(raw_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        raise ValueError(f"Failed to read DOCX: {e}")


def _extract_from_pdf(raw_bytes: bytes) -> str:
    """Extract text from PDF bytes."""
    try:
        reader = PdfReader(io.BytesIO(raw_bytes))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {e}")


def _extract_from_txt(raw_bytes: bytes) -> str:
    """Extract text from TXT bytes."""
    try:
        return raw_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        raise ValueError(f"Failed to read TXT: {e}")


# ---------------------------------------------------------------------
# Main route: /parse-instructions
# ---------------------------------------------------------------------
@parse_instructions_bp.route("/parse-instructions", methods=["POST"])
def parse_instructions():
    try:
        file = request.files.get("file")
        if not file or not file.filename:
            return jsonify({"error": "No file uploaded."}), 400

        _, ext = os.path.splitext(file.filename)
        ext = ext.lower()

        if ext not in ALLOWED:
            return jsonify({
                "error": f"Unsupported file type '{ext}'. Please upload PDF, DOCX, or TXT."
            }), 415

        raw = file.read()
        text = ""

        # 🧠 Parse based on extension
        if ext == ".docx":
            text = _extract_from_docx(raw)
        elif ext == ".pdf":
            text = _extract_from_pdf(raw)
        elif ext == ".txt":
            text = _extract_from_txt(raw)

        # 🧹 Clean and normalize
        clean_text = _normalize(text)
        if not clean_text.strip():
            return jsonify({"error": "No readable text found in the uploaded file."}), 422

        return jsonify({"instructions": clean_text}), 200

    except ValueError as e:
        print("⚠️ Parse error:", str(e))
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        print("❌ Error in parse-instructions:", str(e))
        return jsonify({"error": "Server error: " + str(e)}), 500
