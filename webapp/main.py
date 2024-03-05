from flask import Blueprint, render_template, request
from flask_login import login_required, current_user, user_logged_in
from . import db
import asyncio
import sys

sys.path.append("../")
from parkapp import Parking_request, Parkapp

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/register", methods=["POST"])
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


@main.route("/profile")
@login_required
def profile():
    return render_template("profile.html", name=current_user.name)
