# Guestparkbymail  
Let guests register for parking by email!

If your municipality uses DVSportal to give acces to guest parking you can use this. 

## Prerequisites

- An email account with SMTP/IMAP access.

## Getting started
Supply your credentials in the config.yaml file and run main.py. When guests send an email to the configured emailadress with their licenseplate in the subjectline, this licenseplate will be registered for one hour. 

## Features
- Confirmation email when succesfully 

### Yet to be developed:
- Adjustable parking time requests.
- Graceful denial of requests when balance has run out
- Requests of time extension


## Credits
This script was built upon the DVS Portal API implementation by [tcoenraad](https://github.com/tcoenraad). The original API can be found [here](https://github.com/tcoenraad/python-dvsportal). 

## Author
This scripts was written by me, [Vyvra](https://github.com/Vyvra).

## Issues and Contributions

For issues, feature requests, and contributions, please use the [GitHub Issue Tracker](https://github.com/Vyvra/Guestparkbymail/issues)
