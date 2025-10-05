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
        # --- THE ROOT CAUSE FIX ---
        try:
            # Calculate the timezone offset as a decimal number
            naive_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            tz_info = ZoneInfo(timezone)
            offset = naive_dt.astimezone(tz_info).utcoffset()
            
            # Convert offset to a decimal number (e.g., -7.0 or 5.5)
            offset_decimal = offset.total_seconds() / 3600.0
        except ZoneInfoNotFoundError:
            return jsonify({"error": f"Invalid IANA timezone specified: '{timezone}'"}), 400
        # -------------------------

        local_date_time = f"{date} {time}:00"
        # Use the correct decimal offset in the location string
        location_string = f"API_Location {longitude} {latitude} {offset_decimal}"

        command = ["maitreya8t", "--ldate", local_date_time, "--location", location_string, "--vedicplanets"]

        if output_format in ['json', 'csv']: command.append('--csv')
        elif output_format == 'html': command.append('--html')
        elif output_format == 'plain-html': command.append('--plain-html')

        # We can now use check=True again because we expect the command to succeed
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        # Since the output is now clean, we no longer need the complex parsing functions
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

    except subprocess.CalledProcessError as e:
        # This error handler is now for true failures, not the timezone bug
        return jsonify({
            "error": "Maitreya CLI command failed unexpectedly.",
            "return_code": e.returncode,
            "stdout": e.stdout,
            "stderr": e.stderr
        }), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
