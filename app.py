

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory_store import USERS, seed_volunteers
from disaster_service import (
    create_disaster_report, get_all_disasters_sorted,
    get_disasters_by_reporter, delete_disaster, resolve_disaster,
    add_volunteer_update
)
from volunteer_service import (
    get_all_volunteers, assign_volunteer_to_disaster,
    auto_assign_volunteers, update_volunteer_gps,
    get_volunteer_assignment_details
)
from routing_service  import get_route, get_nearest_volunteer_for_disaster, get_full_map_data
from allocation_service import (
    run_knapsack_for_disaster, run_connectivity_check,
    check_volunteer_reachability, block_road, unblock_road
)


FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

seed_volunteers()


# ── Frontend
@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


# ── Auth 
@app.route("/api/login", methods=["POST"])
def login():
    data     = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required."})

    if USERS.get(username) == password:
        if username == "admin":
            role = "admin"
        elif username.startswith("v"):
            role = "volunteer"
        else:
            role = "user"
        return jsonify({"success": True, "username": username, "role": role})

    return jsonify({"success": False, "message": "Invalid credentials."})


# ── Disasters
@app.route("/api/disasters", methods=["GET"])
@app.route("/api/view",      methods=["GET"])  
def view_disasters():
    reporter_id = request.args.get("reporter_id")
    if reporter_id:
        return jsonify(get_disasters_by_reporter(reporter_id))
    return jsonify(get_all_disasters_sorted())


@app.route("/api/report", methods=["POST"])
def report_disaster():
    data = request.json or {}

    
    location = data.get("location", "").strip()
    if not location:
        return jsonify({"success": False, "error": "Location is required."}), 400

    try:
        severity          = int(data.get("severity", 5))
        volunteers_needed = int(data.get("volunteers_needed", 1))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Severity and volunteers_needed must be integers."}), 400

    raw_emg   = data.get("is_emergency", False)
    is_emergency = (raw_emg == "true" or raw_emg is True)

    did = create_disaster_report(
        dtype             = data.get("type", "Unknown"),
        severity          = severity,
        is_emergency      = is_emergency,
        volunteers_needed = volunteers_needed,
        supplies_needed   = data.get("supplies_needed", ""),
        description       = data.get("description", ""),
        reported_by       = data.get("reported_by", "unknown"),
        location          = location,
        report_photo      = data.get("report_photo", None)
    )
    return jsonify({"success": True,
                    "message": f"Disaster reported with ID {did}",
                    "disaster_id": did})


@app.route("/api/resolve", methods=["POST"])
def resolve():
    data = request.json or {}
    try:
        did = int(data["disaster_id"])
    except (KeyError, ValueError):
        return jsonify({"error": "Valid disaster_id required."}), 400

    if resolve_disaster(did, data.get("resolution_photo")):
        return jsonify({"success": True, "message": f"Disaster {did} resolved."})
    return jsonify({"error": "Not found or already resolved."}), 404


@app.route("/api/delete-disaster", methods=["POST"])
def delete():
    data = request.json or {}
    try:
        did = int(data["disaster_id"])
    except (KeyError, ValueError):
        return jsonify({"success": False, "error": "Valid disaster_id required."}), 400

    ok, msg = delete_disaster(did, data.get("reporter_id"))
    return jsonify({"success": ok, "message" if ok else "error": msg}), (200 if ok else 403)


# ── Volunteers ─────────────────────────────────────────────────────────────────
@app.route("/api/volunteers", methods=["GET"])
def volunteers():
    return jsonify(get_all_volunteers())


@app.route("/api/assign", methods=["POST"])
def assign():
    data = request.json or {}
    try:
        did = int(data["disaster_id"])
    except (KeyError, ValueError):
        return jsonify({"error": "Valid disaster_id required."}), 400

    vid = data.get("volunteer_id")
    if not vid:
        return jsonify({"error": "volunteer_id required."}), 400

    ok, msg = assign_volunteer_to_disaster(
        did, vid,
        data.get("deployment_message", "Deployment initiated.")
    )
    return jsonify({"success": ok, "message" if ok else "error": msg}), (200 if ok else 400)


@app.route("/api/auto-assign", methods=["POST"])
def auto_assign():
    data = request.json or {}
    try:
        did = int(data["disaster_id"])
    except (KeyError, ValueError):
        return jsonify({"error": "Valid disaster_id required."}), 400

    ok, msg = auto_assign_volunteers(
        did, data.get("deployment_message", "Auto-deployment initiated.")
    )
    return jsonify({"success": ok, "message" if ok else "error": msg}), (200 if ok else 400)


@app.route("/api/volunteer-mission", methods=["GET"])
def vol_mission():
    vid = request.args.get("volunteer_id")
    if not vid:
        return jsonify({"error": "volunteer_id required."}), 400
    result = get_volunteer_assignment_details(vid)
    if not result:
        return jsonify({"error": "Volunteer not found."}), 404
    return jsonify(result)


@app.route("/api/volunteer-update", methods=["POST"])
def vol_update():
    data = request.json or {}
    try:
        did = int(data["disaster_id"])
    except (KeyError, ValueError):
        return jsonify({"error": "Valid disaster_id required."}), 400

    desc = data.get("description", "").strip()
    if not desc:
        return jsonify({"error": "Description cannot be empty."}), 400

    ok = add_volunteer_update(did, data.get("volunteer_id"),
                              data.get("priority", "Normal"),
                              desc, data.get("update_photo"))
    return jsonify({"success": ok}) if ok else (jsonify({"error": "Disaster not found."}), 404)


@app.route("/api/location", methods=["POST"])
def location():
    data = request.json or {}
    vid  = data.get("volunteer_id")
    if not vid:
        return jsonify({"error": "volunteer_id required."}), 400
    update_volunteer_gps(vid, data.get("lat"), data.get("lon"), data.get("timestamp"))
    return jsonify({"success": True})


# ── Algorithm endpoints 
@app.route("/api/route", methods=["POST"])
def route():
    data = request.json or {}
    vid  = data.get("volunteer_id")
    try:
        did = int(data["disaster_id"])
    except (KeyError, ValueError):
        return jsonify({"error": "volunteer_id and disaster_id required."}), 400
    return jsonify(get_route(vid, did))


@app.route("/api/nearest-volunteer", methods=["POST"])
def nearest_vol():
    data = request.json or {}
    try:
        did = int(data["disaster_id"])
    except (KeyError, ValueError):
        return jsonify({"error": "Valid disaster_id required."}), 400
    return jsonify(get_nearest_volunteer_for_disaster(did))


@app.route("/api/optimize", methods=["POST"])
def optimize():
    data = request.json or {}
    try:
        did = int(data["disaster_id"])
    except (KeyError, ValueError):
        return jsonify({"error": "Valid disaster_id required."}), 400
    return jsonify(run_knapsack_for_disaster(did))


@app.route("/api/connectivity", methods=["POST"])
def connectivity():
    data = request.json or {}
    return jsonify(run_connectivity_check(data.get("blocked_edges", [])))


@app.route("/api/reachability", methods=["POST"])
def reachability():
    data = request.json or {}
    vid  = data.get("volunteer_id")
    try:
        did = int(data["disaster_id"])
    except (KeyError, ValueError):
        return jsonify({"error": "Valid disaster_id required."}), 400
    return jsonify(check_volunteer_reachability(vid, did))


@app.route("/api/block-road", methods=["POST"])
def api_block():
    data = request.json or {}
    a, b = data.get("from"), data.get("to")
    if not a or not b:
        return jsonify({"error": "Both 'from' and 'to' required."}), 400
    ok, msg = block_road(a, b)
    return jsonify({"success": ok, "message": msg})


@app.route("/api/unblock-road", methods=["POST"])
def api_unblock():
    data = request.json or {}
    a, b = data.get("from"), data.get("to")
    if not a or not b:
        return jsonify({"error": "Both 'from' and 'to' required."}), 400
    ok, msg = unblock_road(a, b)
    return jsonify({"success": ok, "message": msg})


@app.route("/api/map-data", methods=["GET"])
def map_data():
    return jsonify(get_full_map_data())


if __name__ == "__main__":
    print("\n  ResQFlow running →  http://127.0.0.1:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
