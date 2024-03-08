from flask import Flask, render_template, request, Blueprint

import sys

sys.path.append("../")
from parkapp import Parking_request, Parkapp
import asyncio


api = Blueprint("api", __name__)


@api.route("/register", methods=["POST"])
def register_car():
    print(request.json)
    print(request.data)
    license_plate = request.json["license_plate"]
    email = request.json["email"]
    confirmation_requested = request.json["confirmation"]
    print(confirmation_requested)
    prequest = Parking_request()
    prequest.license_plate = license_plate
    prequest.sender = email
    parkapp = Parkapp()
    prequest = asyncio.run(parkapp.proces_request(prequest))
    if confirmation_requested:
        parkapp.send_reply(prequest)
    return prequest.reply.get_content()


@api.route("/addblacklist", methods=["POST"])
def addblacklist():
    return "blacklist functionality not implimented yet"


@api.route("/removeblacklist", methods=["POST"])
def removeblacklist():
    return ""


@api.route("/changetime", methods=["POST"])
def changetime():
    return ""


@api.route("/", methods=["GET"])
def welcome():
    return render_template("index.html", site="guestparkbymail")
