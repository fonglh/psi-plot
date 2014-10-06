#!/usr/bin/python

import urllib
import re
import pymongo
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from datetime import datetime, tzinfo, timedelta
from bs4 import BeautifulSoup
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

# Check if it has been an hour since the latest data point
def should_poll_nea(collection):
	cursor = collection.find().sort('timestamp', pymongo.DESCENDING).limit(1)
	psi3hr_last = cursor[0]['timestamp']

	#convert unix timestamp to datetime and add an hour to figure out when the next check should be
	dt_nxt_check = datetime.fromtimestamp(psi3hr_last, tz=GMT8()) + timedelta(hours=1)

	# it is now later than the time NEA's site should be checked
	return datetime.now(tz=GMT8()) > dt_nxt_check

def get_psi_page():
	f = urllib.urlopen("http://www.haze.gov.sg/haze-updates/psi-readings-over-the-last-24-hours")
	return f.read()

# Get the day on the PSI table's heading
# table_heading_str is the string which indicates the start of the table
def parse_day_from_html(psihtml, table_heading_str): 
	table_header = substr_html(psihtml, table_heading_str, '</h1>')

	# dd MMM yyyy format
	day = re.findall(r'([0-9]+) [A-Za-z]{3} \d{4}', psihtml)
	return int(day[0])

# Extract the portion of HTML which starts with start_str and ends with end_str
def substr_html(html, start_str, end_str):
	start_pos = html.find(start_str)
	html = html[start_pos:]
	end_pos = html.find(end_str)

	return html[:end_pos + len(end_str)]


if __name__ == '__main__':
	currdt = datetime.now(tz=GMT8())	# this datetime var will be used for data insertion
	dtnow = datetime.now(tz=GMT8())		# time at which the script is run

	collection = db_init('psi_db', 'psi_readings')

	# not time to check yet
	if not should_poll_nea(collection):
		exit(0)	

	psihtml = get_psi_page()

	# get day on webpage
	day = parse_day_from_html(psihtml, '3-hr PSI Readings from 1am to 12am on')

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
