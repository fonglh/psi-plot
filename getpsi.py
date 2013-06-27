#!/usr/bin/python

import urllib
import re
import pymongo
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from datetime import datetime, tzinfo, timedelta
import time

class GMT8(tzinfo):
	def utcoffset(self, dt):
		return timedelta(hours=8) + self.dst(dt)
	def dst(self, dt):
		return timedelta(0)
	def tzname(self,dt):
		return "GMT +8"

currdt = datetime.now(tz=GMT8())	# this datetime var will be used for data insertion
dtnow = datetime.now(tz=GMT8())		# time at which the script is run

#get database
client = MongoClient()
db = client.psi_db
try:
	db.authenticate("psiuser", "aNqL6bA5")
except PyMongoError:
	pass
collection = db.psi_readings

# check if the latest data already exists
cursor = collection.find().sort( 'timestamp', pymongo.DESCENDING ).limit(1)

# figure out when to check the website again, should be at least 1 hour from the last reading
psi3hr_last = cursor[0][ 'timestamp' ]
dt_psi3hr_last = datetime.fromtimestamp( psi3hr_last, tz=GMT8() )
dt_nxtCheck = dt_psi3hr_last + timedelta( hours=1 )

# not time to check yet
if dtnow < dt_nxtCheck:
	exit(0)


f = urllib.urlopen("http://app2.nea.gov.sg/anti-pollution-radiation-protection/air-pollution/psi/psi-readings-over-the-last-24-hours")
psihtml = f.read()

#find start of PSI reading table
start_psi = psihtml.find("<h1>3-hr PSI Readings from 12AM to 11.59PM on")
psihtml = psihtml[start_psi:]

#get current day from website to see if data has been updated just past midnight
end_day = psihtml.find('</h1>')
# dd MMM yyyy format
day = re.findall(r'([0-9]+) [A-Za-z]{3} \d{4}', psihtml[:end_day])
day = int(day[0])

# quit as reading is not in yet
if day != dtnow.day:
	exit(0)


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
		#only insert data if the timestamp is before the time now, there CAN'T be future data!!!
		if currdt < dtnow:		
			ts = int(time.mktime(currdt.timetuple()))
			entry = { "timestamp": ts, "psi": reading }
			collection.update( { "timestamp": ts}, entry, upsert=True )
			print currdt, ts, int(reading)
	hr += 1
