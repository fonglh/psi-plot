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

print psi24_table
print pm25_table

exit(0)


for value in times:
	hr = int(value)/100
	currdt = currdt.replace(hour=hr, minute=0, second=0, microsecond=0, tzinfo=GMT8())
	# quit when the script tries to insert future data
	if currdt > dtnow:
		exit(0)
	ts = int(time.mktime(currdt.timetuple()))

	url = "http://app2.nea.gov.sg/anti-pollution-radiation-protection/air-pollution/psi/past-24-hour-psi-readings/time/" + value + "#psi24"

	f = urllib.urlopen(url)
	psihtml = f.read()
	#find start and end of PSI and PM2.5 table
	start_psi = psihtml.find("<strong>24-hr PM2.5 Concentration")
	start_psi = psihtml.find("<tr>", start_psi)		#skip the superscript 3 which screws up the regex later
	end_psi = psihtml.find("</table>", start_psi)
	psihtml = psihtml[start_psi:end_psi]

	#get PSI values, including the blank ones
	table_data = re.findall(r'<td align="center">\s*([^-\s]*)\s*</td>', psihtml, re.M)

	#data is in the format region, 24 hour PSI, 24 hr PM2.5. with each item on 1 row
	#3 iterations are needed for each record
	i = 0
	for row in table_data:
		if i % 3 == 0:
			region = row;
		elif i % 3 == 1:
			psi_24 = int(row)
		else:
			pm25 = int(row)
			entry = { "timestamp": ts, "region": region, "psi_24": psi_24, "pm25": pm25 }
			print entry
			collection.update( { "timestamp": ts, "region": region }, entry, upsert=True )
		i += 1



