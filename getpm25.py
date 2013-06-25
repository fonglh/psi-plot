#!/usr/bin/python

# this script will also get 24 hour PSI readings, as this is in the same table table as the PM2.5 concentrations

import urllib
import re
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

#constant array indices for region
NORTH = 0
SOUTH = 1
EAST = 2
WEST = 3
CENTRAL = 4
REGIONS = [ "North", "South", "East", "West", "Central" ]

psi24_table = [[0 for x in xrange(24)] for x in xrange(5)]
pm25_table = [[0 for x in xrange(24)] for x in xrange(5)]

currdt = datetime.now(tz=GMT8())
dtnow = datetime.now(tz=GMT8())

#get database
client = MongoClient()
db = client.psi_db
try:
	db.authenticate("psiuser", "aNqL6bA5")
except PyMongoError:
	pass
collection = db.psi_24hr_pm25

f = urllib.urlopen("http://app2.nea.gov.sg/anti-pollution-radiation-protection/air-pollution/psi/psi-readings-over-the-last-24-hours")
psihtml = f.read()

# find start of 24 hour PSI table
start_psi = psihtml.find("<h1>24-hr PSI Readings from 12AM to 11.59PM on")
psihtml = psihtml[start_psi:]

#get current day of 24 hour PSI readings
end_day = psihtml.find('</h1>')

# dd MMM yyyy format
day = re.findall(r'([0-9]+) [A-Za-z]{3} \d{4}', psihtml[:end_day])
day = int(day[0])

# quit as reading is not in yet
if day != dtnow.day:
	exit(0)

# extract table of 24 hour PSI readings (1st 12 hours)
start_psi = psihtml.find("<strong>North</strong>")
end_psi = psihtml.find("<strong>Overall Singapore</strong>", start_psi)
psi24hr = psihtml[start_psi:end_psi]


#get 24 hour PSI values, including the blank ones, for 1st 12 hours
psi24_readings = re.findall(r'[\s>]([0-9-]{1,3})[\s<]', psi24hr)

ctr = 0
for reading in psi24_readings:
	psi24_table[ctr/12][ctr%12] = reading
	ctr += 1

# extract table of 24 hour PSI readings (2nd 12 hours)
start_psi = psihtml.find("<strong>North</strong>", end_psi)
end_psi = psihtml.find("<strong>Overall Singapore</strong>", start_psi)
psi24hr = psihtml[start_psi:end_psi]

#get 24 hour PSI values, including the blank ones, for 2nd 12 hours
psi24_readings = re.findall(r'[\s>]([0-9-]{1,3})[\s<]', psi24hr)

ctr = 0
for reading in psi24_readings:
	psi24_table[ctr/12][ctr%12 + 12] = reading
	ctr += 1

# find start of 24 hour PM2.5 table
start_psi = psihtml.find("<h1>24-hr PM2.5 Concentration from 12AM to 11.59PM on")
psihtml = psihtml[start_psi:]

#get current day of 24 hour PSI readings
end_day = psihtml.find('</h1>')

# dd MMM yyyy format
day = re.findall(r'([0-9]+) [A-Za-z]{3} \d{4}', psihtml[:end_day])
day = int(day[0])

# quit as reading is not in yet
if day != dtnow.day:
	exit(0)

# extract table of 24 hour PSI readings (1st 12 hours)
start_psi = psihtml.find("<strong>North</strong>")
end_psi = psihtml.find("<strong>Overall Singapore</strong>", start_psi)
pm25html = psihtml[start_psi:end_psi]


#get 24 hour PSI values, including the blank ones, for 1st 12 hours
pm25_readings = re.findall(r'[\s>]([0-9-]{1,3})[\s<]', pm25html)

ctr = 0
for reading in pm25_readings:
	pm25_table[ctr/12][ctr%12] = reading
	ctr += 1

# extract table of 24 hour PM2.5 readings (2nd 12 hours)
start_psi = psihtml.find("<strong>North</strong>", end_psi)
end_psi = psihtml.find("<strong>Overall Singapore</strong>", start_psi)
pm25html = psihtml[start_psi:end_psi]

#get 24 hour PSI values, including the blank ones, for 2nd 12 hours
pm25_readings = re.findall(r'[\s>]([0-9-]{1,3})[\s<]', pm25html)

ctr = 0
for reading in pm25_readings:
	pm25_table[ctr/12][ctr%12 + 12] = reading
	ctr += 1

#loop through hours in the day to get all the readings
for hr in range(0, 24):
	currdt = currdt.replace(hour=hr, minute=0, second=0, microsecond=0, tzinfo=GMT8())

	#only insert data if the timestamp is before the time now, there CAN'T be future data!!!
	if currdt < dtnow:		
		ts = int(time.mktime(currdt.timetuple()))

		# go through all the regions
		for region_num in range(0, 5):
			psi_24 = psi24_table[region_num][hr]
			pm25 = pm25_table[region_num][hr]

			# make sure both values are numbers, not '-'
			if psi_24.isdigit() and pm25.isdigit():
				psi_24 = int(psi_24)
				pm25 = int(pm25)
				region = REGIONS[region_num]

				entry = { "timestamp": ts, "region": region, "psi_24": psi_24, "pm25": pm25 }
				print entry
				collection.update( { "timestamp": ts, "region": region }, entry, upsert=True )



