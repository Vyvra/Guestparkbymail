# Guestparkbymail

A python script to let guests register for parking by email.
If your municipality uses DVSportal to give access to guest parking you can use this.

## Prerequisites

- An email account with SMTP/IMAP access.
- Login credentials to a parking account.

## Getting started

Supply your credentials in the .env file and run parkapp.py.
When guests send an email to the configured emailadress with their licenseplate in the subject line, this license plate will be registered for one hour.
If the car in question is already registered, it's running registration will be canceled and it will immediately reregister.

The .env file also lets you set a blacklist or whitelist for Emailadresses. If neither of these are set all requests are accepted.

## Features

- Confirmation email when registration is succesful.
- Email reply with error if unsuccesful.
- Whitelist/Blacklist functionality
- Dockerized version available [here](https://hub.docker.com/repository/docker/vyvra/guestparkbymail/general)

### not implemented yet

- Adjustable parking time requests.
- optional automatic cleanup of request mails.

## Issues and requests

For issues, feature requests, and contributions, please use the GitHub Issue Tracker

## Credits

This script was built upon the DVS Portal API implementations by [tcoenraad](https://github.com/tcoenraad), found [here](https://github.com/tcoenraad/python-dvsportal) and [Chessspider](https://github.com/ChessSpider), found [here](https://github.com/ChessSpider/dvsportal)

## Author

This scripts was written by me, [Vyvra](https://github.com/Vyvra).
