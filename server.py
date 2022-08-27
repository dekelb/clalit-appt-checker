from json import JSONDecodeError

from flask import Flask, request, Response
from dotenv import load_dotenv
import json
import os

app = Flask(__name__)
load_dotenv()
outfile = os.getenv('OUT_FILE')


@app.route('/', methods=['GET'])
def home():
    return "<h1>Appointments API is online</h1>"


@app.route('/get-earlier-professions', methods=['GET'])
def get_earlier_professions():
    appointments = _read_earlier_appointments_file()
    professions = {a["profession_name"] for a in appointments}
    return output_successful_response(list(professions))


@app.route('/get-earlier-appointments', methods=['GET'])
def get_earlier_appointments():
    args = request.args
    profession = args.get("profession")
    appointments = _read_earlier_appointments_file()
    if profession:
        out_appointments = [a for a in appointments if a["profession_name"] == profession]
    else:
        out_appointments = appointments
    return output_successful_response(out_appointments)


def output_successful_response(response):
    return Response(status=200, response=json.dumps(response, ensure_ascii=False))


def _read_earlier_appointments_file():
    appointments = []
    if os.path.exists(outfile):
        with open(outfile, mode="r") as f:
            try:
                appointments = json.load(f)
            except JSONDecodeError:
                # Ignore error and return empty array
                pass

    return appointments


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 3333))
