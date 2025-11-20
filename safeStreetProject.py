import json
import os
from datetime import datetime
from collections import defaultdict

from flask import Flask, request, jsonify, send_from_directory

# ------------------ File setup ------------------ #

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "hazards.txt")

app = Flask(__name__)

# ------------------ Data collection ------------------ #

def collect_hazard_report(
    location_name,
    hazard_type,
    accessibility,
    user_type,
    temporary=True,
    description="",
    media_url=None,
):
    """
    Collects a hazard report for accessibility-focused mapping.
    """

    if not (1 <= accessibility <= 5):
        raise ValueError("accessibility must be between 1 and 5")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    day_of_week = datetime.now().strftime("%A")

    report = {
        "timestamp": timestamp,
        "day": day_of_week,
        "location_name": location_name,
        "hazard_type": hazard_type.lower(),
        "accessibility": accessibility,
        "user_type": user_type.lower(),
        "temporary": temporary,
        "description": description,
        "media_url": media_url
    }

    return report


def save_report(report, filename=DATA_FILE):
    """Append a single hazard report to a text file as JSON."""
    with open(filename, "a") as f:
        f.write(json.dumps(report) + "\n")


def get_recent_hazards(location_query, filename=DATA_FILE, max_results=5):
    """
    Find recent hazards whose location_name contains the query string.
    """
    matches = []
    try:
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                report = json.loads(line)
                if location_query.lower() in report["location_name"].lower():
                    matches.append(report)
    except FileNotFoundError:
        return []

    matches.sort(key=lambda r: r["timestamp"], reverse=True)
    return matches[:max_results]


def load_reports(filename=DATA_FILE):
    """Load all hazard reports from the file into a list of dicts."""
    reports = []
    try:
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                reports.append(json.loads(line))
    except FileNotFoundError:
        pass
    return reports


def build_risk_model(reports):
    """
    Build a simple risk model:
    key = (location_name_lower, day_of_week)
    value = number of times hazards were reported
    """
    risk_counts = defaultdict(int)

    for r in reports:
        location_key = r["location_name"].lower()
        day = r["day"]
        key = (location_key, day)
        risk_counts[key] += 1

    return risk_counts


def predict_should_avoid(location_name, current_day, model, threshold=3):
    """
    Predict whether people should avoid a location on a given day-of-week.
    """
    key = (location_name.lower(), current_day)
    score = model.get(key, 0)
    should_avoid = score >= threshold
    return should_avoid, score

# ------------------ Flask routes ------------------ #

@app.route("/")
def index():
    # Serve index.html from the same folder
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/script.js")
def serve_js():
    return send_from_directory(BASE_DIR, "script.js")


@app.route("/api/report", methods=["POST"])
def api_report():
    """
    Receive a hazard report from the frontend and save it.
    Expected JSON body:
    {
      "location_name": "...",
      "hazard_type": "...",
      "accessibility": 1-5,
      "user_type": "...",
      "temporary": true/false,
      "description": "..."
    }
    """
    data = request.get_json()

    try:
        location_name = data["location_name"]
        hazard_type = data["hazard_type"]
        accessibility = int(data["accessibility"])
        user_type = data["user_type"]
        temporary = bool(data.get("temporary", True))
        description = data.get("description", "")
        media_url = data.get("media_url")
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Invalid data"}), 400

    try:
        report = collect_hazard_report(
            location_name=location_name,
            hazard_type=hazard_type,
            accessibility=accessibility,
            user_type=user_type,
            temporary=temporary,
            description=description,
            media_url=media_url
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    save_report(report)

    return jsonify({"status": "ok", "report": report})


@app.route("/api/hazards")
def api_hazards():
    """
    Get recent hazards for a given location.
    Query param: ?location=Fashion%20Square
    """
    location_query = request.args.get("location", "")
    if not location_query:
        return jsonify({"error": "location query parameter is required"}), 400

    hazards = get_recent_hazards(location_query)
    return jsonify({"hazards": hazards})


@app.route("/api/predict")
def api_predict():
    """
    Predict if a user should avoid a given location today.
    Query param: ?location=Fashion%20Square
    """
    location_query = request.args.get("location", "")
    if not location_query:
        return jsonify({"error": "location query parameter is required"}), 400

    reports = load_reports()
    model = build_risk_model(reports)

    now = datetime.now()
    current_day = now.strftime("%A")

    should_avoid, score = predict_should_avoid(location_query, current_day, model)

    return jsonify({
        "location": location_query,
        "day": current_day,
        "score": score,
        "should_avoid": should_avoid
    })


if __name__ == "__main__":
    app.run(debug=True)

