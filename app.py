from flask import Flask, request, jsonify, Response # <--- IMPORT Response
import subprocess
import json
import csv
import io

app = Flask(__name__)

@app.route('/healthz')
def healthz():
    """A simple health check endpoint."""
    return jsonify({"status": "ok"}), 200

@app.route('/api/vedicplanets', methods=['GET'])
def get_vedic_planets():
    # --- Step 1: Get all parameters, including the new 'format' parameter ---
    date = request.args.get('date')
    time = request.args.get('time')
    latitude = request.args.get('lat')
    longitude = request.args.get('lon')
    timezone = request.args.get('tz')
    
    # Default to 'json' if the format parameter is not provided
    output_format = request.args.get('format', 'json').lower()

    # --- Step 2: Validate the requested format ---
    valid_formats = ['json', 'csv', 'html', 'plain-html', 'text']
    if output_format not in valid_formats:
        return jsonify({"error": f"Invalid format specified. Valid formats are: {', '.join(valid_formats)}"}), 400

    if not all([date, time, latitude, longitude, timezone]):
        return jsonify({"error": "Missing required parameters: date, time, lat, lon, tz"}), 400

    try:
        local_date_time = f"{date} {time}:00"
        location_string = f"API_Location {latitude} {longitude} {timezone}"

        # --- Step 3: Build the command, adding the correct format flag ---
        command = [
            "maitreya8t",
            "--ldate", local_date_time,
            "--location", location_string,
            "--vedicplanets",
        ]

        # Determine the flag needed for the subprocess based on the desired output
        # For JSON output, we need to request CSV from the tool to parse it.
        if output_format in ['json', 'csv']:
            command.append('--csv')
        elif output_format == 'html':
            command.append('--html')
        elif output_format == 'plain-html':
            command.append('--plain-html')
        # If 'text', we add no flag, as it's the default.

        result = subprocess.run(
            command, capture_output=True, text=True, check=True
        )

        # --- Step 4: Process and return the data in the requested format ---
        
        # If the user wants JSON, we parse the CSV and convert it.
        if output_format == 'json':
            csv_file = io.StringIO(result.stdout)
            reader = csv.DictReader(csv_file)
            planets_list = [row for row in reader]
            return jsonify(planets_list)
        
        # For all other formats, we return the raw text with the correct Content-Type.
        else:
            content_type_map = {
                'csv': 'text/csv',
                'html': 'text/html',
                'plain-html': 'text/html',
                'text': 'text/plain'
            }
            mimetype = content_type_map[output_format]
            return Response(result.stdout, mimetype=mimetype)

    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Maitreya CLI command failed.", "stderr": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
