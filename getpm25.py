#!/usr/bin/python

# this script will also get 24 hour PSI readings, as this is in the same table table as the PM2.5 concentrations

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
dtnow = datetime.now(tz=GMT8())

#get database
client = MongoClient()
db = client.psi_db
db.authenticate("psiuser", "aNqL6bA5")
collection = db.psi_24hr_pm25

f = urllib.urlopen("http://app2.nea.gov.sg/anti-pollution-radiation-protection/air-pollution/psi/past-24-hour-psi-readings/")
psihtml = f.read()

# find times available by checking the dropdown box
start_time_pos = psihtml.find('<h1 id="psi24">')
end_time_pos = psihtml.find('</select>', start_time_pos)
psihtml = psihtml[ start_time_pos:end_time_pos ]

# get all the available times
times = re.findall(r'<option.*value="([0-9]{4})">', psihtml)

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



