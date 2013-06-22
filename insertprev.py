#!/usr/bin/python

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

#specify required date
currdt = datetime(2013, 6, 21, 0, 0, 0, 0, tzinfo=GMT8())

#specify readings
psi_readings = ['210', '173', '143', '119', '104', '96', '94', '111', '158', '256', '367', '400', '401', '360', '245', '168', '145', '143', '139', '135', '137', '142', '153', '168']


#get database
client = MongoClient()
db = client.psi_db
collection = db.psi_readings

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
