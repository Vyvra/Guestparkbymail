from dvsportal.dvsportal import DVSPortal, DVSPortalError
import smtplib
from imap_tools.mailbox import MailBoxTls
import yaml
import asyncio
from datetime import datetime, timedelta
import re
import time


async def main():
    parking = Parkapp()
    while True:
        await parking.wait_for_mail()
        await parking.proces_request()
        print("Reestablishing connection to mailserver")
        time.sleep(10)


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
            self.requester: str

    async def wait_for_mail(self) -> None:
        with MailBoxTls(self._IMAP_server, self._IMAP_port).login(
            self._IMAP_user, self._IMAP_pass
        ) as mailbox:
            print("waiting for requests")
            responses = mailbox.idle.wait(timeout=1000)
            # Timeout must be less than 29 minutes.
            print("new message recieved")
            if responses:
                for msg in mailbox.fetch(limit=1, reverse=True):
                    self.request = msg
                    requester = re.search(
                        "([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)",
                        str(self.request.from_values),
                    )
                    # this is here because Pyright doesn't want me to try to get group() from something that defaults to None
                    if requester:
                        self.requester = requester.group()

    async def proces_request(self) -> None:
        # TODO accept and validate license plates in different formats, right not just accepts any str of len 6
        if len(self.request.subject) == 6:
            try:
                license_plate = self.request.subject
                await self.register_car(license_plate, 60)
                reply = f"Thank you for using my parkbymail service. Your registration was succesful. You're registration is valid until {(datetime.now() + timedelta(hours=1))}"
                print("registration succesful, sending confirmation reply")
                self.send_reply(reply, self.requester)
            except DVSPortalError as error:
                print("could not register, will send an error reply")
                self.process_error(error)

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

    def process_error(self, error) -> None:
        message = f"Sorry something has gone wrong and your registration has NOT been processed. But hey, the server has not crashed so that's good. I have not send proper error handling up yet so here is the message of the error: {error}"
        self.send_reply(message, self.requester)

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
