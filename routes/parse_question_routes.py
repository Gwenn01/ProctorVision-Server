# routes/parse_question_routes.py
from flask import Blueprint, request, jsonify
from flask_cors import CORS
import os, re
from io import BytesIO
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from docx import Document

# ---------------------------------------------------------------------
# Blueprint setup
# ---------------------------------------------------------------------
parse_question_bp = Blueprint("parse_question", __name__)
CORS(parse_question_bp, resources={r"/*": {"origins": "*"}})

# ---------------------------------------------------------------------
# Regex patterns for parsing questions
# ---------------------------------------------------------------------
Q_RE = re.compile(r"^\s*(?:q(?:uestion)?\s*\d*[\.\):-]?\s*)(.*)$", re.I)
OPT_RE = re.compile(r"^\s*([A-D])[\.\)]\s*(.+)$", re.I)

# Keywords to detect essay questions
ESSAY_KEYWORDS = [
    "explain",
    "describe",
    "discuss",
    "essay",
    "in detail",
    "why",
    "how",
]


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------
def _flush(q, out):
    """Finalize a question and detect its type before appending."""
    if not q:
        return

    text = (q.get("questionText") or "").lower()
    opts = q.get("options", [])

    if len(opts) >= 2:
        # Multiple choice
        q["type"] = "mcq"
        q["correctAnswer"] = None
    elif any(word in text for word in ESSAY_KEYWORDS):
        # Essay
        q["type"] = "essay"
        q["options"] = []
        q["correctAnswer"] = None
    else:
        # Identification (short answer)
        q["type"] = "identification"
        q["options"] = []
        q["correctAnswer"] = ""

    out.append(q)


def _new_q(text):
    """Start a new question object."""
    m = Q_RE.match(text)
    return {
        "questionText": (m.group(1) if m else text).strip(),
        "options": [],
        "correctAnswer": None,
        "type": None,  # will be set in _flush
    }


def _try_option(line):
    """Check if a line is an option like A. Something"""
    m = OPT_RE.match(line)
    if not m:
        return None
    letter = m.group(1).upper()
    body = m.group(2).strip()
    index = ord(letter) - ord("A")  # A->0, B->1, ...
    return index, body


def _parse_lines(lines):
    """Convert lines of text into structured questions."""
    questions = []
    q = None
    for raw in lines:
        text = (raw or "").strip()
        if not text:
            continue

        # New question?
        if Q_RE.match(text):
            _flush(q, questions)
            q = _new_q(text)
            continue

        # Option?
        opt = _try_option(text)
        if opt:
            idx, body = opt
            if q is None:
                # If options appear before a question line, start a generic question
                q = _new_q("Untitled question")
            q["options"].append(body)
            continue

        # Continuation of the question text
        if q is None:
            q = _new_q(text)
        else:
            q["questionText"] = (q["questionText"] + " " + text).strip()

    _flush(q, questions)
    return questions


# ---------------------------------------------------------------------
# Main route: /parse-questions
# ---------------------------------------------------------------------
@parse_question_bp.route("/parse-questions", methods=["POST"])
def parse_questions():
    try:
        file = request.files.get("file")
        if not file or not file.filename:
            return jsonify({"error": "No file uploaded"}), 400

        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        lines = []

        # Use in-memory file stream for cloud hosting safety
        file_stream = BytesIO(file.read())

        if ext == ".docx":
            try:
                doc = Document(file_stream)
                lines = [p.text for p in doc.paragraphs]
            except Exception as e:
                return jsonify({"error": f"Failed to read DOCX file: {str(e)}"}), 500

        elif ext == ".pdf":
            try:
                reader = PdfReader(file_stream)
                for page in reader.pages:
                    text = page.extract_text() or ""
                    if text:
                        lines.extend(text.splitlines())
            except Exception as e:
                return jsonify({"error": f"Failed to read PDF file: {str(e)}"}), 500

        else:
            return jsonify({"error": "Unsupported file type. Please upload a .PDF or .DOCX file."}), 415

        # Parse the extracted lines
        questions = _parse_lines(lines)
        return jsonify({"questions": questions}), 200

    except Exception as e:
        print("❌ Error in parse-questions:", str(e))
        return jsonify({"error": str(e)}), 500
