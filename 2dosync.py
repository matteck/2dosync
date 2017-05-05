#!/usr/bin/env python3

"""
Synchronise from iCloud Reminders to 2Do via 2Do email integration
TO-DO: set dates when 2Do supports it.
"""

import caldav
import requests
import smtplib
import configparser
import datetime

config = configparser.ConfigParser()
config.read("2dosync.ini")
USERNAME = config['icloud']['username']
PASSWORD = config['icloud']['password']
URL = config['icloud']['url']

SMTP_USERNAME = config['smtp']['username']
SMTP_PASSWORD = config['smtp']['password']
SMTP_SERVER = config['smtp']['server']

client = caldav.DAVClient(url=URL,
                          username=USERNAME,
                          password=PASSWORD)
principal = client.principal()

urls = None
for calendar in principal.calendars():
    if calendar.name == '2DoInbox':
        found = True
        urls = [x[0] for x in calendar.children()]
        break
assert found

for u in urls:
    r = requests.get(u, auth=(USERNAME, PASSWORD))
    lines = [x.strip() for x in r.text.strip().split('\n')]
    vals = [x.split(':', 1) for x in lines]
    d = {key: value for (key, value) in vals}
    # Don't import completed
    if ('STATUS' in d and d['STATUS'] == 'COMPLETED'):
        client.delete(u)
        continue
    # Can't continue without a summary, shouldn't happen so throw an exception
    assert 'SUMMARY' in d
    # Due date
    if "DUE;TZID=Australia/Sydney" in d:
        raw = d["DUE;TZID=Australia/Sydney"]
        due = "due(%s-%s-%s %s:%s)" % (raw[0:5], raw[])

    else:
        due = "due(%s)" % datetime.datetime.now().isoformat()[0:10]
    print(due)
    # Priority
    if "PRIORITY" in d:
        p = int(d["PRIORITY"])
        if p <= 1:
            priority = "priority(!!!)"
        elif p <= 5:
            priority = "priority(!!)"
        else:
            priority = "priority(!)"
    else:
        priority = ""
    # Tags - might customise later
    tags = "tag(siri)"
    # Description, remove Apple default for empty description
    if 'DESCRIPTION' in d and d['DESCRIPTION'] != "Reminder":
        body = d['DESCRIPTION']
    else:
        body = ''
    subject = "%s %s %s %s" % (d['SUMMARY'], tags, priority, due)
    msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s" % (SMTP_USERNAME,
                                                            SMTP_USERNAME,
                                                            subject,
                                                            body)
    server = smtplib.SMTP_SSL(SMTP_SERVER)
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    server.sendmail(SMTP_USERNAME, SMTP_USERNAME, msg)
    server.quit()
    # client.delete(u)
