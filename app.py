from flask import Flask, request, jsonify, Response
import subprocess
import json
import csv
import io
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import sys

app = Flask(__name__)

@app.route('/healthz')
def healthz():
    return jsonify({"status": "ok"}), 200

@app.route('/api/vedicplanets', methods=['GET'])
def get_vedic_planets():
    # Get all possible location parameters
    city = request.args.get('city')
    date = request.args.get('date')
    time = request.args.get('time')
    latitude = request.args.get('lat')
    longitude = request.args.get('lon')
    timezone = request.args.get('tz') # Only used for manual lat/lon
    output_format = request.args.get('format', 'json').lower()

    if not date or not time:
        return jsonify({"error": "Missing required parameters: date, time"}), 400

    location_string = ""
    try:
        # --- NEW, SIMPLIFIED LOGIC ---
        if city:
            # If a city is provided, we pass it directly to the tool.
            location_string = city
        elif all([latitude, longitude, timezone]):
            # If manual coordinates are provided, we build the complex string.
            naive_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            tz_info = ZoneInfo(timezone)
            offset = naive_dt.astimezone(tz_info).utcoffset()
            offset_decimal = offset.total_seconds() / 3600.0
            location_string = f"API_Location {longitude} {latitude} {offset_decimal}"
        else:
            return jsonify({"error": "Missing location parameters. Provide either 'city' or all of 'lat', 'lon', and 'tz'."}), 400
        # --------------------------------

        local_date_time = f"{date} {time}:00"
        
        # Build the command using the determined location string
        command = ["maitreya8t", "--ldate", local_date_time, "--location", location_string, "--vedicplanets"]

        if output_format in ['json', 'csv']: command.append('--csv')
        elif output_format == 'html': command.append('--html')
        elif output_format == 'plain-html': command.append('--plain-html')

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode not in [0, 255]:
            return jsonify({
                "error": "Maitreya CLI command failed with an unexpected error.",
                "return_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr
            }), 500

        if output_format == 'json':
            csv_file = io.StringIO(result.stdout)
            reader = csv.DictReader(csv_file, delimiter=';')
            return jsonify([row for row in reader])
        else:
            content_type_map = {
                'csv': 'text/csv', 'html': 'text/html',
                'plain-html': 'text/html', 'text': 'text/plain'
            }
            mimetype = content_type_map.get(output_format, 'text/plain')
            return Response(result.stdout, mimetype=mimetype)

    except Exception as e:
        print(f"An unexpected Python error occurred: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
