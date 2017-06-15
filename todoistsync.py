#!/usr/bin/env python3

"""
Synchronise from iCloud Reminders to 2Do via 2Do email integration
TO-DO: escape quotes in description and notes
TO-DO: add notes
"""

import caldav
import requests
import configparser
import datetime
import sys
import uuid
import json
import calendar

config = configparser.ConfigParser()
config.read("2dosync.ini")
USERNAME = config['icloud']['username']
PASSWORD = config['icloud']['password']
URL = config['icloud']['url']

SMTP_USERNAME = config['smtp']['username']
SMTP_PASSWORD = config['smtp']['password']
SMTP_SERVER = config['smtp']['server']

TODOIST_API_KEY="76122e73916a913bd5998eebb6a82dec0efdc49b"
TODOIST_API_URL="https://todoist.com/API/v7/sync"

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
    if "DUE;TZID=Australia/Sydney" in d:
        raw = d["DUE;TZID=Australia/Sydney"]
        due = "%s-%s-%sT%s:%s" % (raw[0:4], raw[4:6], raw[6:8], raw[9:11], raw[11:13])
        datestring = "%s %s %s:%s" % (raw[6:8], calendar.month_name[int(raw[4:6])], raw[9:11], raw[11:13])
    else:
        due = str(datetime.date.today().strftime('%Y-%m-%dT%H:%M'))
        datestring = "today"
    # Priority
    if "PRIORITY" in d:
        p = int(d["PRIORITY"])
        if p <= 1:
            priority = "4"
        elif p <= 5:
            priority = "3"
        else:
            priority = "2"
    else:
        priority = "1"
    # Tags - might customise later
    tags = "tag(siri)"
    # Description, remove Apple default for empty description
    if 'DESCRIPTION' in d and d['DESCRIPTION'] != "Reminder":
        body = d['DESCRIPTION']
    else:
        body = ''

    data = {"token": TODOIST_API_KEY, "commands": '[{"type": "item_add", "uuid": "%s", "temp_id": "%s", "args": {"content": "%s",  "priority": "%s", "date_string": "%s", "labels": [2147964283]}}]' % (uuid.uuid4(), uuid.uuid4(), d['SUMMARY'], priority, datestring)}

    print(json.dumps(data, sort_keys=True, indent=4))

    s = requests.post(TODOIST_API_URL, data=data)
    print(s.status_code)
    print(json.dumps(s.json(), sort_keys=True, indent=4))

    # subject = "%s %s %s %s" % (d['SUMMARY'], tags, priority, due)
    # msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s" % (SMTP_USERNAME,
    #                                                         SMTP_USERNAME,
    #                                                         subject,
    #                                                         body)
    # server = smtplib.SMTP_SSL(SMTP_SERVER)
    # server.login(SMTP_USERNAME, SMTP_PASSWORD)
    # server.sendmail(SMTP_USERNAME, SMTP_USERNAME, msg)
    # server.quit()
    # client.delete(u)
