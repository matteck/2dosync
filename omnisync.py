#!/usr/bin/env python3

"""
Synchronise from iCloud Reminders to Omnifocus via Omni Mail Drop integration
"""

import caldav
import requests
import configparser
import datetime
import sys
import uuid
import json
import calendar
import smtplib

config = configparser.ConfigParser()
config.read("2dosync.ini")
USERNAME = config['icloud']['username']
PASSWORD = config['icloud']['password']
URL = config['icloud']['url']

SMTP_USERNAME = config['smtp']['username']
SMTP_PASSWORD = config['smtp']['password']
SMTP_SERVER = config['smtp']['server']
OMNI_EMAIL_ADDRESS = 'matt_eck.5xs9t@sync.omnigroup.com'

client = caldav.DAVClient(url=URL,
                          username=USERNAME,
                          password=PASSWORD)
principal = client.principal()

urls = None
for cal in principal.calendars():
    if cal.name == '2DoInbox':
        found = True
        urls = [x[0] for x in cal.children()]
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
    # if "DUE;TZID=Australia/Sydney" in d:
    #     raw = d["DUE;TZID=Australia/Sydney"]
    #     due = "%s-%s-%sT%s:%s" % (raw[0:4], raw[4:6], raw[6:8], raw[9:11], raw[11:13])
    #     datestring = "%s %s %s:%s" % (raw[6:8], calendar.month_name[int(raw[4:6])], raw[9:11], raw[11:13])
    # else:
    #     due = str(datetime.date.today().strftime('%Y-%m-%dT%H:%M'))
    #     datestring = "today"
    # Priority
    # if "PRIORITY" in d:
    #     p = int(d["PRIORITY"])
    #     if p <= 1:
    #         priority = "4"
    #     elif p <= 5:
    #         priority = "3"
    #     else:
    #         priority = "2"
    # else:
    #     priority = "1"
    # Tags - might customise later
    # tags = "tag(siri)"
    # Description, remove Apple default for empty description
    if 'DESCRIPTION' in d and d['DESCRIPTION'] != "Reminder":
        body = d['DESCRIPTION']
    else:
        body = ''
    
    subject = d['SUMMARY']
    msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s" % (SMTP_USERNAME,
                                                            OMNI_EMAIL_ADDRESS,
                                                            subject,
                                                            body)
    
    server = smtplib.SMTP_SSL(SMTP_SERVER)
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    server.sendmail(SMTP_USERNAME, OMNI_EMAIL_ADDRESS, msg)
    server.quit()
    client.delete(u)
    

    client.delete(u)
