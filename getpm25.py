#!/usr/bin/python

# this script will also get 24 hour PSI readings, as this is in the same table table as the PM2.5 concentrations

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

# extract tabular PSI data from HTML and insert into table
# start from just before the day check, so the day check will be
# done separately for each table
# HTML will contain the <h1> heading of the table
def extract_table_data(html):
	table = [['-' for x in xrange(24)] for x in xrange(5)]

	#get current day of 24 hour PM2.5 readings
	end_day = html.find('</h1>')
	# dd MMM yyyy format
	day = re.findall(r'([0-9]+) [A-Za-z]{3} \d{4}', html[:end_day])
	day = int(day[0])
	# quit as reading is not in yet
	if day != dtnow.day:
		exit(0)

	# extract table (1st 12 hours)
	start_table = html.find("<strong>North</strong>")
	end_table = html.find("<tr class=\"even\">", start_table)

	# 12 hours of data from the table
	table12 = html[start_table:end_table]

	#get 24 hour PSI/PM2.5 values, including the blank ones, for 1st 12 hours
	values = re.findall(r'[\s>]([0-9-]{1,3})[\s<(]', table12)
	ctr = 0
	for value in values:
		table[ctr/12][ctr%12] = value
		ctr += 1

	# extract table (2nd 12 hours)
	start_table = html.find("<strong>North</strong>", end_table)

	# the PSI 24 hour table HTML should end here or overall readings will mess up the regex
	end_table = html.find("<strong>Overall Singapore</strong>", start_table)
	# if "Overall Singapore" can't be found, this is the PM2.5 table
	# find the closing '</table>' tag immediately
	if end_table == -1:
		end_table = html.find("</table>", start_table)
	table12 = html[start_table:end_table]

	#get 24 hour PSI or PM2.5, including the blank ones, for 2nd 12 hours
	#PM2.5 values have equivalent PSI values in brackets, ignore them
	# add an open bracket to the right side of the captured number to handle 
	# the case where PM2.5 has equivalent PSI in brackets. e.g. 18(58)
	values = re.findall(r'[\s>]([0-9-]{1,3})[\s<(]', table12)

	ctr = 0
	for value in values:
		table[ctr/12][ctr%12 + 12] = value
		ctr += 1
	return table


#array for regions used in NEA data
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

# check if the latest data already exists
cursor = collection.find().sort( 'timestamp', pymongo.DESCENDING ).limit(1)

# figure out when to check the website again, should be at least 1 hour from the last reading
psi24hr_last = cursor[0][ 'timestamp' ]
dt_psi24hr_last = datetime.fromtimestamp( psi24hr_last, tz=GMT8() )
dt_nxtCheck = dt_psi24hr_last + timedelta( hours=1 )

# not time to check yet
if dtnow < dt_nxtCheck:
	exit(0)

# both 24 hour PSI readings and 24 hour PM2.5 readings must be in before
# this script will insert the entry into the database

# get 24 hour PSI data
f = urllib.urlopen("http://www.haze.gov.sg/haze-updates/psi-readings-over-the-last-24-hours")
psihtml = f.read()

# find start of 24 hour PSI table
start_psi = psihtml.find("24-hr PSI Readings from 1am to 12am on")
psihtml = psihtml[start_psi:]

psi24_table = extract_table_data(psihtml)

# get 24 hour PM2.5 data
# find start of 24 hour PM2.5 table
f = urllib.urlopen("http://www.haze.gov.sg/haze-update/pollutant-concentrations/type/PM25.aspx")
psihtml = f.read()
start_psi = psihtml.find("24-hr PM<sub>2.5</sub> (")
psihtml = psihtml[start_psi:]
pm25_table = extract_table_data(psihtml)


#loop through hours in the day to get all the readings
# use today's date, set hour, min, sec etc to 0
# in each iteration, increase time by an hour
datadt = currdt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=GMT8())
delta = timedelta(hours=1)
for hr in xrange(24):
	datadt += delta

	#only insert data if the timestamp is before the time now, there CAN'T be future data!!!
	if datadt < dtnow:		
		ts = int(time.mktime(datadt.timetuple()))

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
				print datadt, entry
				collection.update( { "timestamp": ts, "region": region }, entry, upsert=True )



