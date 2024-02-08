from dvsportal.dvsportal import DVSPortal, DVSPortalError
import smtplib
from imap_tools.mailbox import MailBoxTls
import yaml
import asyncio
from datetime import datetime, timedelta
import re
import time


async def main():
    while True:
        parking = Parkapp()
        parking_request = await parking.wait_for_mail()
        if parking_request.succes:
            reply = await parking.proces_request(parking_request.license_plate)
            parking.send_reply(reply, parking_request.sender)
        print("Reestablishing connection to mailserver")
        time.sleep(10)


class Parking_request:
    def __init__(self) -> None:
        self.sender: str  # emailadress
        self.time: int  # time in minutes
        self.request_type: str
        self.license_plate: str
        self.succes = False


class Parkapp:
    def __init__(self) -> None:
        with open("config.yaml", "r") as config:
            config = yaml.safe_load(config)
            self._IMAP_server = config["IMAP_SERVER"]
            self._IMAP_port = config["IMAP_PORT"]
            self._SMTP_server = config["SMTP_SERVER"]
            self._SMTP_port = config["SMTP_PORT"]
            self._SMTP_user = config["IMAP_USER"]
            self._SMTP_pass = config["IMAP_PASS"]
            self._IMAP_user = config["IMAP_USER"]
            self._IMAP_pass = config["IMAP_PASS"]
            self._DVS_domain = config["DVS_DOMAIN"]
            self._DVS_user = config["DVS_USER"]
            self._DVS_pass = config["DVS_PASS"]

    async def wait_for_mail(self) -> Parking_request:
        """Opens connectino to IMAP server and waits for new emails"""
        p_request = Parking_request()
        try:
            with MailBoxTls(self._IMAP_server, self._IMAP_port).login(
                self._IMAP_user, self._IMAP_pass
            ) as mailbox:
                print("waiting for requests")
                responses = mailbox.idle.wait(timeout=1000)
                # Timeout must be less than 29 minutes.
                if responses:
                    print("new message recieved")
                    for msg in mailbox.fetch(limit=1, reverse=True):
                        email = re.search(
                            "([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)",
                            str(msg.from_values),
                        )
                        # this is here because Pyright doesn't want me to try to get group() from something that defaults to None
                        if email:
                            p_request.sender = email.group()
                            p_request.request_type = "park1h"
                            p_request.time = 60
                            p_request.license_plate = self.parse_plate(msg.subject)
                            p_request.succes = True
                            return p_request
        except OSError as error:
            print(f"could not establish connection to Imap server: {error}")
            p_request.succes = False
        return p_request

    def parse_plate(self, plate):
        return plate

    async def proces_request(self, license_plate):
        """Tries to fulfill the provided request and returns a reply message to send"""
        # TODO accept and validate license plates in different formats, right not just accepts any str of len 6
        if len(license_plate) == 6:
            try:
                await self.register_car(license_plate, 60)
                reply = f"Thank you for using my Guestparkbymail service. Your registration was succesful. You're registration is valid until {str(datetime.now() + timedelta(hours=1))[:-10]}"
                print("registration succesful, sending confirmation reply")
                return reply
            except DVSPortalError as error:
                print("could not register, will send an error reply")
                # errortext = list(error.args)[1]
                return self.process_error(error)
                # self.DVSerror = errortext["Result"]

    async def register_car(self, license_plate: str, minutes: int) -> None:
        async with DVSPortal(
            api_host=self._DVS_domain,
            identifier=self._DVS_user,
            password=self._DVS_pass,
        ) as dvs:
            await dvs.update()
            reservation = await dvs.create_reservation(
                license_plate_value=license_plate,
                date_from=datetime.now(),
                date_until=(datetime.now() + timedelta(minutes=minutes)),
            )
            return reservation

    def process_error(self, error) -> str:
        errorcode = list(error.args)[1]["Result"]
        match errorcode:
            case 3:
                message = "There are no visitor hours left. Your car has NOT been registered. New visitor hours are available from next Monday"
            case 24:
                message = "This car is already registered!"
            case _:
                message = f"Sorry something has gone wrong and your registration has NOT been processed. But hey, the server has not crashed so that's good. I have not send proper error handling for this error so here is the message of the error: {error}"
        return message

    def send_reply(self, replymessage, to_addr):
        with smtplib.SMTP(self._SMTP_server, self._SMTP_port) as server:
            # server.set_debuglevel(1)
            server.login(self._SMTP_user, self._SMTP_pass)
            msg = "From: %s\r\nTo: %s\r\n\r\n" % (str(self._SMTP_user), str(to_addr))
            msg = msg + str(replymessage)
            server.sendmail(self._SMTP_user, to_addr, msg)
            print("reply send")
            server.quit()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
