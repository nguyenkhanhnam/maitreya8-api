from flask import Flask, request, jsonify, Response
import subprocess
import json
import csv
import io
from datetime import datetime  # <--- IMPORT datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError # <--- IMPORT zoneinfo

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
    output_format = request.args.get('format', 'json').lower()

    valid_formats = ['json', 'csv', 'html', 'plain-html', 'text']
    if output_format not in valid_formats:
        return jsonify({"error": f"Invalid format specified. Valid formats are: {', '.join(valid_formats)}"}), 400

    if not all([date, time, latitude, longitude, timezone]):
        return jsonify({"error": "Missing required parameters: date, time, lat, lon, tz"}), 400

    try:
        # --- NEW: Calculate UTC offset from timezone ---
        try:
            # Create a datetime object and localize it to the user's timezone
            naive_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            tz_info = ZoneInfo(timezone)
            # This correctly handles Daylight Saving Time for the given date/time
            offset = naive_dt.astimezone(tz_info).utcoffset()
            # Format the offset into the required +/-HH:MM string
            offset_hours = int(offset.total_seconds() // 3600)
            offset_minutes = int((offset.total_seconds() % 3600) // 60)
            offset_string = f"{offset_hours:+03d}:{abs(offset_minutes):02d}"
        except ZoneInfoNotFoundError:
            return jsonify({"error": f"Invalid IANA timezone specified: '{timezone}'"}), 400
        # -----------------------------------------------

        local_date_time = f"{date} {time}:00"
        # --- CHANGE: Use the new offset_string for the location ---
        location_string = f"API_Location {latitude} {longitude} {offset_string}"

        command = [
            "maitreya8t",
            "--ldate", local_date_time,
            "--location", location_string,
            "--vedicplanets",
        ]

        if output_format in ['json', 'csv']:
            command.append('--csv')
        elif output_format == 'html':
            command.append('--html')
        elif output_format == 'plain-html':
            command.append('--plain-html')

        result = subprocess.run(
            command, capture_output=True, text=True, check=True
        )

        if output_format == 'json':
            csv_file = io.StringIO(result.stdout)
            reader = csv.DictReader(csv_file)
            planets_list = [row for row in reader]
            return jsonify(planets_list)
        else:
            content_type_map = {
                'csv': 'text/csv',
                'html': 'text/html',
                'plain-html': 'text/html',
                'text': 'text/plain'
            }
            mimetype = content_type_map.get(output_format, 'text/plain')
            return Response(result.stdout, mimetype=mimetype)

    except subprocess.CalledProcessError as e:
        # Now we return the specific error for debugging
        return jsonify({"error": "Maitreya CLI command failed.", "stderr": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
