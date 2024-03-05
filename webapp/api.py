from flask import Flask, render_template, request

import sys

sys.path.append("../")
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
    reply = {"reply": (prequest.reply.get_content)}
    return prequest.reply.get_content()


@app.route("/", methods=["GET"])
def welcome():
    return render_template("index.html", site="guestparkbymail")
