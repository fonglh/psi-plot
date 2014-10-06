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

# return a collection
def db_init(db_name, collection_name):
	#get database
	client = MongoClient()
	db = client[db_name]
	try:
		db.authenticate("psiuser", "aNqL6bA5")
	except PyMongoError:
		return None
	return db[collection_name]

def dt_to_unixtime(dt):
	return int(time.mktime(dt.timetuple()))

def should_poll_nea(collection):
	cursor = collection.find().sort('timestamp', pymongo.DESCENDING).limit(1)
	psi3hr_last = cursor[0]['timestamp']

	#convert unix timestamp to datetime and add an hour to figure out when the next check should be
	dt_nxt_check = datetime.fromtimestamp(psi3hr_last, tz=GMT8()) + timedelta(hours=1)

	# it is now later than the time NEA's site should be checked
	return datetime.now(tz=GMT8()) > dt_nxt_check


if __name__ == '__main__':
	currdt = datetime.now(tz=GMT8())	# this datetime var will be used for data insertion
	dtnow = datetime.now(tz=GMT8())		# time at which the script is run

	collection = db_init('psi_db', 'psi_readings')

	# check if the latest data already exists
	cursor = collection.find().sort( 'timestamp', pymongo.DESCENDING ).limit(1)

	# figure out when to check the website again, should be at least 1 hour from the last reading
	psi3hr_last = cursor[0][ 'timestamp' ]
	dt_psi3hr_last = datetime.fromtimestamp( psi3hr_last, tz=GMT8() )
	dt_nxtCheck = dt_psi3hr_last + timedelta( hours=1 )

	# not time to check yet
	if dtnow < dt_nxtCheck:
		exit(0)


	f = urllib.urlopen("http://www.haze.gov.sg/haze-updates/psi-readings-over-the-last-24-hours")
	psihtml = f.read()

	#find start of PSI reading table
	start_psi = psihtml.find("<h1>3-hr PSI Readings from 1am to 12am on")

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
	# each number is an hourly psi reading, starting from 1am
	# unavailable readings are repsesented by a '-'
	# iterate through this array insert hourly data into the database

	# use today's date, set hour, min, sec etc to 0
	# in each iteration, increase time by an hour
	datadt = currdt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=GMT8())
	delta = timedelta(hours=1)
	for reading in psi_readings:
		if reading.isdigit():
			datadt += delta
			#only insert data if the timestamp is before the time now, there CAN'T be future data!!!
			if datadt < dtnow:		
				ts = int(time.mktime(datadt.timetuple()))
				entry = { "timestamp": ts, "psi": reading }
				collection.update( { "timestamp": ts}, entry, upsert=True )
				print datadt, ts, int(reading)
