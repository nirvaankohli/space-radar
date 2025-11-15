import flask
from flask import Flask, jsonify, request
import data_pipeline
import os

app = Flask(__name__)


@app.route("/run_pipeline", methods=["POST"])
def run_pipeline():
    result = data_pipeline.run_pipeline()
    return jsonify({"status": "completed", "result": result})
