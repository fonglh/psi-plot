#!/usr/bin/python

import urllib
import re
from pymongo import MongoClient
from datetime import datetime, tzinfo, timedelta
import time

class GMT8(tzinfo):
	def utcoffset(self, dt):
		return timedelta(hours=8) + self.dst(dt)
	def dst(self, dt):
		return timedelta(0)
	def tzname(self,dt):
		return "GMT +8"

currdt = datetime.now(tz=GMT8())

#get database
client = MongoClient()
db = client.psi_db
db.authenticate("psiuser", "aNqL6bA5")
collection = db.psi_readings

f = urllib.urlopen("http://app2.nea.gov.sg/anti-pollution-radiation-protection/air-pollution/psi/past-24-psi-readings")
psihtml = f.read()

# get current day to check if the site has been updated just past midnight
start_day = psihtml.find('<h1 id="psi24">')
psihtml = psihtml[ start_day: ]
end_day = psihtml.find('</h1>')
day = re.findall(r'24-hr PSI Readings on ([0-9]+) [A-Za-z]{3} \d{4}', psihtml[:end_day])
day = int(day[0])

# quit as reading is not in yet
if day != currdt.day:
	exit(0)

#find start of PSI reading table
start_psi = psihtml.find("<h1>3-hr PSI Readings from 12AM to 11.59PM on")
psihtml = psihtml[start_psi:]

# extract table of PSI readings
start_psi = psihtml.find("<strong>3-hr PSI</strong>")
end_psi = psihtml.find("</table>", start_psi)
psihtml = psihtml[start_psi:end_psi]

#get PSI values, including the blank ones
psi_readings = re.findall(r'[\s>]([0-9-]{1,3})[\s<]', psihtml)


# psi_readings is in the format [ 180, 230, 123, '-', '-' ]
# each number is an hourly psi reading, starting from midnight
# unavailable readings are repsesented by a '-'

# iterate through this array insert hourly data into the database
hr = 0
for reading in psi_readings:
	if reading.isdigit():
		currdt = currdt.replace(hour=hr, minute=0, second=0, microsecond=0, tzinfo=GMT8())
		ts = int(time.mktime(currdt.timetuple()))
		entry = { "timestamp": ts, "psi": reading }
		collection.update( { "timestamp": ts}, entry, upsert=True )
		print currdt, ts, int(reading)
	hr += 1
