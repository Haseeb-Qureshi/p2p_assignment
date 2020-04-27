from flask import Flask, request, Response
from flask_cors import CORS
from waitress import serve
import requests
import logging
import sys

if len(sys.argv) < 2: raise Exception("Must pass in port number")
MY_PORT = int(sys.argv[1])

app = Flask(__name__, static_url_path="", static_folder="../frontend")
CORS(app)

EXCLUDED_HEADERS = ["content-encoding", "content-length", "transfer-encoding", "connection"]

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/<int:node>/<method>",methods=["GET", "POST", "DELETE"])
def proxy(node, method):
    try:
        if request.method == "GET":
            r = requests.get(f"http://localhost:{node}/{method}")
            return Response(r.content, r.status_code, stripped_headers(r))
        elif request.method == "POST":
            r = requests.post(f"http://localhost:{node}/{method}", json=request.get_json())
            return Response(r.content, r.status_code, stripped_headers(r))
        else:
            raise Exception("Invalid request: " + request.method)
    except requests.exceptions.ConnectionError:
        return "ConnectionError", 500 

def stripped_headers(r):
    return [(name, value) for (name, value) in r.raw.headers.items() if name.lower() not in EXCLUDED_HEADERS]

if __name__ == "__main__":
    logging.getLogger('waitress').setLevel(logging.ERROR)
    serve(app, host="0.0.0.0", port=MY_PORT)
