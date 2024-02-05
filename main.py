import smtplib
import time
import re
from datetime import datetime, timedelta
from imap_tools.mailbox import MailBoxTls
import asyncio
from dvsportal.dvsportal.dvsportal import DVSPortal
import yaml

config = []
with open("config.yaml", "r") as config:
    config = yaml.safe_load(config)

IMAP_SERVER = config["IMAP_SERVER"]
IMAP_PORT = config["IMAP_PORT"]
SMTP_SERVER = config["SMTP_SERVER"]
SMTP_PORT = config["SMTP_PORT"]
IMAP_USER = config["IMAP_USER"]
IMAP_PASS = config["IMAP_PASS"]
DVS_DOMAIN = config["DVS_DOMAIN"]
DVS_USER = config["DVS_USER"]
DVS_PASS = config["DVS_PASS"]


async def main(loop):
    for i in range(1000):
        print("waiting for email")
        mail = check_mail(IMAP_SERVER, IMAP_PORT, IMAP_USER, IMAP_PASS)
        license_plate = mail[0]
        requester = str(mail[1])
        if len(license_plate) == 6:
            requester = re.search(
                "([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)", requester
            ).group()
            reply = reply_request(requester)
            print(reply)
            test = await park_car(license_plate, DVS_USER, DVS_PASS, DVS_DOMAIN)
            print(test)
        time.sleep(10)


def check_mail(IMAP_SERVER, IMAP_PORT, IMAP_USER, IMAP_PASS) -> str:
    with MailBoxTls(IMAP_SERVER, IMAP_PORT).login(IMAP_USER, IMAP_PASS) as mailbox:
        for msg in mailbox.fetch(limit=1, reverse=True):
            print(msg.date_str, msg.subject)
            answer = [msg.subject, msg.from_values].copy()
            if len(msg.subject) == 6:
                mailbox.delete([msg.uid])
            return answer


async def park_car(license_plate, DVS_USER, DVS_PASS, DVS_DOMAIN):
    async with DVSPortal(
        api_host=DVS_DOMAIN, identifier=DVS_USER, password=DVS_PASS
    ) as dvs:
        await dvs.update()
        reservation = await dvs.create_reservation(
            license_plate_value=license_plate,
            date_from=datetime.now(),
            date_until=(datetime.now() + timedelta(hours=1)),
        )
        return reservation


def reply_request(requester):
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        # server.set_debuglevel(1)
        server.login(IMAP_USER, IMAP_PASS)
        msg = "From: %s\r\nTo: %s\r\n\r\n" % (IMAP_USER, requester)
        msg = msg + (
            f"Thank you for using my parkbymail service. Your registration was succesful. You're registration is valid until {(datetime.now() + timedelta(hours=1))}"
        )
        server.sendmail(IMAP_USER, requester, msg)
        server.quit()
    return "Succes"


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
