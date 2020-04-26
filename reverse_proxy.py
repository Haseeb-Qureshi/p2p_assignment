from flask import Flask, request, Response
from flask_cors import CORS
from waitress import serve
import requests
import logging
import sys

if len(sys.argv) < 2: raise Exception("Must pass in port number")
MY_PORT = int(sys.argv[1])

app = Flask(__name__, static_url_path="", static_folder="frontend")
CORS(app)

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/<int:node>/<method>",methods=["GET", "POST", "DELETE"])
def proxy(node, method):
    if request.method == "GET":
        resp = requests.get(f"http://localhost:{node}/{method}")
        excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        headers = [(name, value) for (name, value) in  resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response
    elif request.method == "POST":
        resp = requests.post(f"http://localhost:{node}{method}", json=request.get_json())
        excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response

if __name__ == "__main__":
    logging.getLogger('waitress').setLevel(logging.ERROR)
    serve(app, host="0.0.0.0", port=MY_PORT)
