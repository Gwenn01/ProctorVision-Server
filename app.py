from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "✅ Flask running successfully on Railway!"})

@app.route("/api/test")
def test():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    # Local dev only
    if os.environ.get("RAILWAY_ENVIRONMENT") is None:
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
