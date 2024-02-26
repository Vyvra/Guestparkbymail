from datetime import datetime, timedelta
from dotenv import load_dotenv
from dvsportal import DVSPortal, DVSPortalError
from email.message import EmailMessage
from imap_tools.mailbox import MailBoxTls
from imap_tools.message import MailMessage
from logger import getlogger
import asyncio
import os
import pytz
import smtplib

LOGGER = getlogger("parkapp")


async def main():
    # logger = getlogger("main")
    while True:
        parking = Parkapp()
        request = Parking_request()
        request = await parking.wait_for_request_mail(request)
        if request.succes:
            request = await parking.proces_request(request)
            request = parking.send_reply(request)
        # logger.debug("Reestablishing connection to mailserver")


class Parking_request:
    def __init__(self) -> None:
        self.sender: str  # emailadress
        self.time = 60  # time in minutes
        self.request_type: str
        self.license_plate: str
        self.succes = False
        self.reply = EmailMessage()


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
        self.logger = LOGGER

    async def wait_for_request_mail(self, request) -> Parking_request:
        """Opens connection to IMAP server and waits for new requests"""
        try:
            with MailBoxTls(self._IMAP_server, self._IMAP_port).login(
                self._IMAP_user, self._IMAP_pass
            ) as mailbox:
                self.logger.debug("waiting for requests")
                responses = mailbox.idle.wait(timeout=1500)
                # Timeout must be less than 29 minutes.
                if responses:
                    self.logger.debug("new message recieved")
                    for msg in mailbox.fetch(limit=1, reverse=True):
                        request = self.parse_request(msg, request)
                        return request
        except OSError as error:
            self.logger.critical(
                f"could not establish connection to Imap server: {error}"
            )

            request.succes = False
        return request

    def parse_request(
        self, msg: MailMessage, request: Parking_request
    ) -> Parking_request:
        """Takes a Mailmessage and converts it a Parking_request"""
        for word in msg.subject.split():
            # A problem with this is that if there are multiple plates in the subject line it will only register the last one.
            if plate := self.parse_plate(word):
                request.license_plate = plate
                request.sender = msg.from_
                request.succes = True
            else:
                request.succes = False
        return request

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
        # Reject unauthorized requests
        if self.authorized_sender(request) is False:
            request.reply["Subject"] = "Unauthorized parking request"
            request.reply.set_content(
                "Sorry requests for parking from this email adress are not allowed. Please use an emailadress that is authorized for use by this service."
            )
            self.logger.warning(
                f"recieved unauthorized request from email {request.sender}"
            )
            return request

        try:
            await self.register_car(request.license_plate, request.time)
            request.reply.set_content(
                f"Thank you for using my Guestparkbymail service. Your registration was succesful. Your registration is valid until {str(datetime.now(pytz.timezone('Europe/Amsterdam')) + timedelta(hours=1))[:-10]}"
            )
            request.reply[
                "Subject"
            ] = f"Succesful registeration for {request.license_plate}"
            self.logger.debug("registration succesful, sending confirmation reply")
        except DVSPortalError as error:
            self.logger.info("could not register, will send an error reply")
            request.reply.set_content(self.process_error(error))
            request.reply[
                "Subject"
            ] = f"WARNING, registration for {request.license_plate} unsuccesful"
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
        """Connects to SMTP server and sends the reply from the request.reply variable"""
        with smtplib.SMTP(self._SMTP_server, self._SMTP_port) as server:
            # server.set_debuglevel(1)
            server.login(self._SMTP_user, self._SMTP_pass)
            request.reply["From"] = str(self._SMTP_user)
            request.reply["To"] = str(request.sender)
            server.send_message(request.reply)
            self.logger.debug("reply send")
            server.quit()

    def authorized_sender(self, request: Parking_request) -> bool:
        """Checks if requests from request.sender are allowed based on whitelist/blacklist settings"""
        whitelist = os.getenv("WHITELIST")
        blacklist = os.getenv("BLACKLIST")
        if whitelist:
            if request.sender in whitelist:
                return True
            else:
                return False
        if blacklist:
            if request.sender in blacklist:
                return False
        return True


if __name__ == "__main__":
    asyncio.run(main())
