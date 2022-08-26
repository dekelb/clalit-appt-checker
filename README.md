# clalit-appt-checker
Python scraper to check for earlier appointments in Clalit Health Services

## Some background
If you ever needed to schedule a doctor's appointment at Clalit you probably noticed that most available slots are a few months ah
ead, and it's not that easy to find a slot for "next week" (sometimes not even two weeks from now). There is a "waiting list", but
 it's based on someone from Clalit calling you to re-schedule your appointment (and it usually doesn't really work).
Sometimes people cancel their appointments, but in order to catch a better slot - you need to sign in to the website and look for
a newer slot. Over and over again.

So basically this is what this script does for me.

It will not change your appointment, but will let you know (by mail) that there is a newer slot available.

## How to run
1. Make sure you have pipenv installed
2. Run `pipenv install` to install all python dependencies
3. Copy the sample env file and set the relevant values inside `cp .env.example .env`
4. Run `pipenv run checker` to execute the checker script

## Set as cronjob
`*/15 * * * * cd /PATH/TO/clalit-appt-checker && /usr/local/bin/pipenv run checker >/tmp/cronstdout.log 2>/tmp/cronstderr.log`  
This will run the script on every 15th minute of the hour (00:00, 00:15, 00:30, 00:45, 01:00 ...)

## Send mails using gmail
In order to send emails using SMTP with gmail you will need to configure your gmail account to allow less secure apps and setup an App password

## Output to a local file
In order to export the results to a local json file you need to configure the file name. The file will be created and overwriten every execution of the crawler