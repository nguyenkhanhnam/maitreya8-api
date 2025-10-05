from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

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
        command = [
            "maitreya8t", "--date", date, "--time", time,
            "--latitude", latitude, "--longitude", longitude,
            "--timezone", timezone, "--vedicplanets", "--output=json"
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
    # Flask runs on port 5000 by default inside the container
    app.run(host='0.0.0.0', port=5000)
