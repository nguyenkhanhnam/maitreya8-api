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

    if not all([date, time, latitude, longitude, timezone]):
        return jsonify({"error": "Missing required parameters: date, time, lat, lon, tz"}), 400

    try:
        try:
            naive_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            tz_info = ZoneInfo(timezone)
            offset = naive_dt.astimezone(tz_info).utcoffset()
            offset_decimal = offset.total_seconds() / 3600.0
        except ZoneInfoNotFoundError:
            return jsonify({"error": f"Invalid IANA timezone specified: '{timezone}'"}), 400

        local_date_time = f"{date} {time}:00"
        location_string = f"API_Location {longitude} {latitude} {offset_decimal}"

        command = ["maitreya8t", "--ldate", local_date_time, "--location", location_string, "--vedicplanets"]

        if output_format in ['json', 'csv']: command.append('--csv')
        elif output_format == 'html': command.append('--html')
        elif output_format == 'plain-html': command.append('--plain-html')

        # We do not use check=True, so we can inspect the result ourselves.
        result = subprocess.run(command, capture_output=True, text=True)

        # --- THE BEST PRACTICE: INTELLIGENT ERROR HANDLING ---
        # We expect return code 0 (true success) or 255 (known bug on success).
        # Any other return code is a REAL, UNEXPECTED error.
        if result.returncode not in [0, 255]:
            # Log the unexpected error for debugging.
            print(f"Maitreya command failed with UNEXPECTED exit code: {result.returncode}", file=sys.stderr)
            print(f"Command executed: {' '.join(command)}", file=sys.stderr)
            print(f"Stdout: {result.stdout}", file=sys.stderr)
            print(f"Stderr: {result.stderr}", file=sys.stderr)
            sys.stderr.flush()
            
            # Return a detailed error to the API user.
            return jsonify({
                "error": "Maitreya CLI command failed with an unexpected error.",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }), 500
        # --------------------------------------------------------

        # If we reach here, it's a success (either code 0 or 255).
        # The output from the tool is clean because our inputs are correct.
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
        # This catches Python errors, not subprocess errors.
        print(f"An unexpected Python error occurred: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
