import json
from flask import Flask, jsonify, request
from parkapp import Parking_request, Parkapp
import asyncio

app = Flask(__name__)


@app.route("/register", methods=["POST"])
def register_car():
    print(request.json)
    print(request.data)
    license_plate = request.json["license_plate"]
    email = request.json["email"]
    prequest = Parking_request()
    prequest.license_plate = license_plate
    prequest.sender = email
    parkapp = Parkapp()
    prequest = asyncio.run(parkapp.proces_request(prequest))
    return str(prequest.reply)
