from json import JSONDecodeError

from flask import Flask, request, Response
from dotenv import load_dotenv
import json
import os
import time

app = Flask(__name__)
load_dotenv()
outfile = os.getenv('OUT_FILE')


@app.route('/', methods=['GET'])
def home():
    return "<h1>Appointments API is online</h1>"


@app.route('/get-earlier-professions', methods=['GET'])
def get_earlier_professions():
    appointments = _read_json_array_file(outfile)
    professions = {a["profession_name"] for a in appointments}
    return output_successful_response(list(professions))


@app.route('/get-earlier-appointments', methods=['GET'])
def get_earlier_appointments():
    args = request.args
    profession = args.get("profession")
    appointments = _read_json_array_file(outfile)
    if profession:
        out_appointments = [a for a in appointments if a["profession_name"] == profession]
    else:
        out_appointments = appointments
    res = {
        "last_updated": _get_modified_time_of_file(outfile),
        "appointments": out_appointments
    }
    return output_successful_response(res)


def output_successful_response(response):
    return Response(status=200, response=json.dumps(response, ensure_ascii=False))


def _get_modified_time_of_file(file_path):
    if os.path.exists(file_path):
        modified_time = round(os.path.getmtime(file_path))
    else:
        modified_time = 0
    return modified_time


def _read_json_array_file(file_path):
    arr = []
    if os.path.exists(file_path):
        with open(file_path, mode="r") as f:
            try:
                arr = json.load(f)
            except JSONDecodeError:
                # Ignore error and return empty array
                pass

    return arr


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 3333))
