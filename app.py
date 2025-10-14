from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "✅ Flask running successfully on Railway!"})

@app.route("/api/test")
def test():
    return jsonify({"status": "ok"})
