import os
from dvsportal import DVSPortal, DVSPortalError
import smtplib
from imap_tools.mailbox import MailBoxTls
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timedelta
from imap_tools.message import MailMessage
import pytz
from email.message import EmailMessage
from logger import getlogger


async def main():
    logger = getlogger("main")
    while True:
        parking = Parkapp()
        parking_request = await parking.wait_for_request_mail()
        if parking_request.succes:
            parking_request = await parking.proces_request(parking_request)
            parking.send_reply(parking_request)
        logger.debug("Reestablishing connection to mailserver")


class Parking_request:
    def __init__(self) -> None:
        self.sender: str  # emailadress
        self.time = 60  # time in minutes
        self.request_type: str
        self.license_plate: str
        self.succes = False
        self.reply: str


class Parkapp:
    def __init__(self) -> None:
        """Takes credentials from the environment or .env file and loads them into variables"""
        load_dotenv()
        self._IMAP_server = str(os.getenv("IMAP_SERVER"))
        self._IMAP_port = int(os.getenv("IMAP_PORT") or 0)
        self._SMTP_server = str(os.getenv("SMTP_SERVER"))
        self._SMTP_port = int(os.getenv("SMTP_PORT") or 0)
        self._SMTP_user = str(os.getenv("IMAP_USER"))
        self._SMTP_pass = str(os.getenv("IMAP_PASS"))
        self._IMAP_user = str(os.getenv("IMAP_USER"))
        self._IMAP_pass = str(os.getenv("IMAP_PASS"))
        self._DVS_domain = str(os.getenv("DVS_DOMAIN"))
        self._DVS_user = str(os.getenv("DVS_USER"))
        self._DVS_pass = str(os.getenv("DVS_PASS"))
        self.logger = getlogger("parkapp")

    async def wait_for_request_mail(self) -> Parking_request:
        """Opens connection to IMAP server and waits for new requests"""
        p_request = Parking_request()
        try:
            with MailBoxTls(self._IMAP_server, self._IMAP_port).login(
                self._IMAP_user, self._IMAP_pass
            ) as mailbox:
                self.logger.debug("waiting for requests")
                responses = mailbox.idle.wait(timeout=1000)
                # Timeout must be less than 29 minutes.
                if responses:
                    self.logger.debug("new message recieved")
                    self.logger.debug("new message recieved")
                    for msg in mailbox.fetch(limit=1, reverse=True):
                        p_request = self.parse_request(msg)
                        return p_request
        except OSError as error:
            self.logger.critical(
                f"could not establish connection to Imap server: {error}"
            )

            p_request = Parking_request()
            p_request.succes = False
        return p_request

    def parse_request(self, msg: MailMessage) -> Parking_request:
        p = Parking_request()
        for word in msg.subject.split():
            # A problem with this is that if there are multiple plates in the subject line it will only register the last one.
            if plate := self.parse_plate(word):
                p.license_plate = plate
                p.sender = msg.to[0]
                p.succes = True
            else:
                p.succes = False
        return p

    def parse_plate(self, plate: str) -> str | None:
        """Takes license in different formats and converts them to allcaps/nodashes, returns None if no valid license_plate could be constructed"""
        filter(str.isalnum, plate)
        plate.upper
        if (
            len(plate) > 5
            and sum(c.isdigit() for c in plate) < 4
            and sum(c.isalpha() for c in plate) < 5
        ):
            return plate
        return None

    async def proces_request(self, request: Parking_request) -> Parking_request:
        """Tries to fulfill the provided request and returns a reply message to send"""
        try:
            await self.register_car(request.license_plate, request.time)
            request.reply = f"Thank you for using my Guestparkbymail service. Your registration was succesful. You're registration is valid until {str(datetime.now() + timedelta(hours=1))[:-10]}"
            self.logger.debug("registration succesful, sending confirmation reply")
        except DVSPortalError as error:
            self.logger.info("could not register, will send an error reply")
            request.reply = self.process_error(error)
        return request

    async def register_car(self, license_plate: str, minutes: int) -> None:
        """Connects to DVSportal and attemps to register 'license_plate' for 'minutes'"""
        async with DVSPortal(
            api_host=self._DVS_domain,
            identifier=self._DVS_user,
            password=self._DVS_pass,
        ) as dvs:
            await dvs.update()
            # if car is already registered, cancel reservation and reregister.
            if license_plate in dvs.active_reservations:
                await dvs.end_reservation(
                    reservation_id=dvs.active_reservations[license_plate][
                        "reservation_id"
                    ],
                )
            # it should be possible to find a way to get a timezone object without importing another thing, right?
            timezone = pytz.timezone("Europe/Amsterdam")
            reservation = await dvs.create_reservation(
                license_plate_value=license_plate,
                date_from=datetime.now(timezone),
                date_until=(datetime.now(timezone) + timedelta(minutes=minutes)),
            )
            return reservation

    def process_error(self, error) -> str:
        """Takes the error that DVSPortal raises and converts them to friendly error messages"""
        errorcode = list(error.args)[1]["Result"]
        match errorcode:
            case 3:
                message = "There are no visitor hours left. Your car has NOT been registered. New visitor hours are available from next Monday"
            case 24:
                message = "This car is already registered!"
            case _:
                message = f"Sorry something has gone wrong and your registration has NOT been processed. But hey, the server has not crashed so that's good. I have not send proper error handling for this error so here is the message of the error: {error}"
        return message

    def send_reply(self, request: Parking_request):
        """Connects to SMTP server and sends 'replymessage' to 'to_addr'"""
        with smtplib.SMTP(self._SMTP_server, self._SMTP_port) as server:
            # server.set_debuglevel(1)
            server.login(self._SMTP_user, self._SMTP_pass)
            msg = EmailMessage()
            msg["Subject"] = "information about your registration"
            msg["From"] = str(self._SMTP_user)
            msg["To"] = str(request.sender)
            msg.set_content(str(request.reply))
            server.send_message(msg)
            self.logger.debug("reply send")
            server.quit()


if __name__ == "__main__":
    asyncio.run(main())
