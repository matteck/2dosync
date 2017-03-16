#!/usr/bin/env python3

"""
Synchronise from iCloud Reminders to 2Do via 2Do email integration
TO-DO: set dates when 2Do supports it. Property is like 'DUE;TZID=Australia/Sydney': '20170309T220000'
"""

import caldav
import requests
import smtplib
import configparser

c = configparser.ConfigParser()


USERNAME="matt@eckha.us"
PASSWORD="rtyt-pbpq-ltce-gegy"

SMTP_USERNAME="matte2do@gmail.com"
SMTP_PASSWORD="djbzzyrhtpyglfvi"
SMTP_SERVER="smtp.gmail.com"

client = caldav.DAVClient("https://p48-caldav.icloud.com/110849164/calendars/", username=USERNAME, password=PASSWORD)
principal = client.principal()

urls = None
for calendar in principal.calendars():
    if calendar.name == '2DoInbox':
        found = True
        urls = [ x[0] for x in calendar.children()]
        break

assert(found)

for u in urls:
    r = requests.get(u, auth=(USERNAME, PASSWORD))
    lines = [ x.strip() for x in r.text.strip().split('\n')]
    vals = [ x.split(':', 1) for x in lines]
    d = {key: value for (key, value) in vals}
    # Don't import completed
    if not ('STATUS' in d and d['STATUS'] == 'COMPLETED'):
        assert('SUMMARY' in d)
        subject = d['SUMMARY'] + ' tags:import'
        msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (SMTP_USERNAME, SMTP_USERNAME, d['SUMMARY'])
        server = smtplib.SMTP_SSL(SMTP_SERVER)
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, SMTP_USERNAME, msg)
        server.quit()
    client.delete(u)
