from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route('/healthz')
def healthz():
    """A simple health check endpoint."""
    return jsonify({"status": "ok"}), 200

@app.route('/api/vedicplanets', methods=['GET'])
def get_vedic_planets():
    date = request.args.get('date')
    time = request.args.get('time')
    latitude = request.args.get('lat')
    longitude = request.args.get('lon')
    timezone = request.args.get('tz')

    if not all([date, time, latitude, longitude, timezone]):
        return jsonify({"error": "Missing required parameters: date, time, lat, lon, tz"}), 400

    try:
        # --- CHANGE 1: Combine date and time into a single string ---
        # We add ":00" for the seconds to match the required format.
        local_date_time = f"{date} {time}:00"

        # --- CHANGE 2: Combine location info into a single string ---
        # The name "API_Location" is just a placeholder.
        location_string = f"API_Location {latitude} {longitude} {timezone}"

        # --- CHANGE 3: Build the command with the correct flags ---
        command = [
            "maitreya8t",
            "--ldate", local_date_time,
            "--location", location_string,
            "--vedicplanets",
            "--output=json"
        ]
        
        result = subprocess.run(
            command, capture_output=True, text=True, check=True
        )
        json_output = [json.loads(line) for line in result.stdout.strip().split('\n')]
        
        if len(json_output) == 1:
            return jsonify(json_output[0])
        else:
            return jsonify(json_output)

    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Maitreya CLI command failed.", "stderr": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Using port 3000 as configured
    app.run(host='0.0.0.0', port=3000)
