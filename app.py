from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def hello():
    return jsonify({"message": "Hello, CI/CD!"})


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/api/time")
def get_time():
    from datetime import UTC, datetime

    current_time = datetime.now(UTC).isoformat()
    return jsonify({"current_time": current_time})


@app.route("/greet/<name>")
def greet(name):
    return jsonify({"message": f"Hello, {name}!"})


@app.route("/version")
def version():
    return jsonify({"version": "1.0.2"})


if __name__ == "__main__":
    app.run(debug=True)
