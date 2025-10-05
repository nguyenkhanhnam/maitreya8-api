from flask import Flask, request, jsonify, Response
import subprocess
import json
import csv
import io
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import sys

app = Flask(__name__)

# --- NEW HELPER FUNCTION TO CLEAN THE OUTPUT ---
def extract_csv_from_output(raw_output: str) -> str | None:
    """
    Finds and extracts only the 'Vedic Planets' CSV data from the tool's raw output.
    """
    lines = raw_output.strip().split('\n')
    csv_data_lines = []
    found_header = False
    header_start = 'Planet;'

    for line in lines:
        if line.strip().startswith(header_start):
            found_header = True
        
        if found_header:
            # The table ends with a blank line
            if not line.strip():
                break
            csv_data_lines.append(line)

    if not csv_data_lines:
        return None
    
    return "\n".join(csv_data_lines)
# ---------------------------------------------

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
        try:
            naive_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            tz_info = ZoneInfo(timezone)
            offset = naive_dt.astimezone(tz_info).utcoffset()
            offset_hours = int(offset.total_seconds() // 3600)
            offset_minutes = int((offset.total_seconds() % 3600) // 60)
            offset_string = f"{offset_hours:+03d}:{abs(offset_minutes):02d}"
        except ZoneInfoNotFoundError:
            return jsonify({"error": f"Invalid IANA timezone specified: '{timezone}'"}), 400

        local_date_time = f"{date} {time}:00"
        location_string = f"API_Location {longitude} {latitude} {offset_string}"

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

        result = subprocess.run(command, capture_output=True, text=True)

        # --- REFACTORED LOGIC ---
        # For JSON and CSV, we need the clean data.
        if output_format in ['json', 'csv']:
            clean_csv = extract_csv_from_output(result.stdout)
            
            if not clean_csv:
                return jsonify({
                    "error": "Could not find parseable CSV data in the Maitreya output.",
                    "raw_output": result.stdout
                }), 500

            if output_format == 'json':
                csv_file = io.StringIO(clean_csv)
                reader = csv.DictReader(csv_file, delimiter=';')
                planets_list = [row for row in reader]
                return jsonify(planets_list)
            
            elif output_format == 'csv':
                return Response(clean_csv, mimetype='text/csv')

        # For other formats, return the full, raw output as it's more descriptive.
        else:
            content_type_map = {
                'html': 'text/html',
                'plain-html': 'text/html',
                'text': 'text/plain'
            }
            mimetype = content_type_map.get(output_format, 'text/plain')
            return Response(result.stdout, mimetype=mimetype)

    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.stderr.flush()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
