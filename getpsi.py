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
	last_timestamp = cursor[0]['timestamp']

	#convert unix timestamp to datetime and add an hour to figure out when the next check should be
	dt_nxt_check = datetime.fromtimestamp(last_timestamp, tz=GMT8()) + timedelta(hours=1)

	# it is now later than the time NEA's site should be checked
	return datetime.now(tz=GMT8()) > dt_nxt_check

def get_psi_page():
	f = urllib.urlopen("http://www.haze.gov.sg/haze-updates/psi-readings-over-the-last-24-hours")
	return f.read()

# Get the day on the PSI table's heading
# table_heading_str is the string which indicates the start of the table
def datetime_from_html(psihtml, table_heading_str): 
	table_header = substr_html(psihtml, table_heading_str, '</h1>')

	# dd MMM yyyy format
	date = re.findall(r'([0-9]+) ([A-Za-z]{3}) (\d{4})', psihtml)
	# convert result from regex match to a string
	date_str = date[0][0] + ' ' + date[0][1] + ' ' + date[0][2]
	# create a naive datetime object (no timezone) from the string
	parsed_date = datetime.strptime(date_str, '%d %b %Y')
	# create an aware datetime object (with timezone)
	result_date = datetime.now(tz=GMT8())
	# replace the values of the aware datetime object
	result_date = result_date.replace(parsed_date.year, parsed_date.month, parsed_date.day, 0, 0, 0, 0)
	return result_date

# Extract the portion of HTML which starts with start_str and ends with end_str
def substr_html(html, start_str, end_str):
	start_pos = html.find(start_str)
	html = html[start_pos:]
	end_pos = html.find(end_str)

	return html[:end_pos + len(end_str)]

# Given HTML from <table> to </table>, extract PSI values from the <td> data
def get_td(table_html):
	soup = BeautifulSoup(table_html)
	# the time headers all have a width 0f 7%
	td_list = soup.findAll('td', attrs={'width': lambda x: x != '7%'}) 	
	td_list = [extract_psi_number(str(block)) for block in td_list]
	# after PSI number extraction, some td blocks returned None
	td_list = [elem for elem in td_list if elem is not None]
	return td_list

# Extract the number from a <td>..</td> HTML block
# return '-' or invalid block as None
def extract_psi_number(input_str):
	extracted_data = re.findall(r'[\s>]([0-9-]{1,3})[\s<]', input_str)
	if not extracted_data or not extracted_data[0].isdigit():
		return None
	else:
		return int(extracted_data[0])

# If there are no labels, return the input_arr
# Else assume the data is evenly distributed among the labels.
# Also, there are a maximum of 12 contiuous values per label
# For an example, see the 24 hour PSI reading table on NEA's website with region information
def structure_table(input_arr, labels=[]):
	if len(labels) == 0:
		return input_arr

	output = {}

	# init output dictionary with empty lists
	for label in labels:
		output[label] = []

	# 12 hours for each half of the data
	first_half = input_arr[:12*len(labels)]
	second_half = input_arr[12*len(labels):]

	subarray1_len = len(first_half)/len(labels)
	subarray2_len = len(second_half)/len(labels)

	# no need return value as dictionaries are changed in the function (like pass by ref in C++)
	structure_table_helper(output, first_half, subarray1_len, labels)
	structure_table_helper(output, second_half, subarray2_len, labels)

	return output

def structure_table_helper(output_dict, subarray, subarray_len, labels):
	label_num = 0
	for label in labels:
		for i in xrange(subarray_len):
			output_dict[label].append(subarray[label_num*subarray_len + i])
		label_num += 1

def insert_data(collection, input_data, dtnow, datadt):
	delta = timedelta(hours=1)

	# assume input_data is a dictionary, if not, try a list
	# find the length of each subarray and get the labels
	try:
		labels = input_data.keys()
		data_len = len(input_data[labels[0]])
	except AttributeError:
		labels = []
		data_len = len(input_data)

	for i in xrange(data_len):
		datadt += delta
		# sanity check. there CAN't be future data
		if datadt > dtnow:
			break

		ts = int(time.mktime(datadt.timetuple()))

		# this is the dictionary
		if labels:
			for label in labels:
				entry = {"timestamp": ts, "region": label, "psi_24": input_data[label][i]}
				print datadt, entry
				collection.update( { "timestamp": ts, "region": label }, entry, upsert=True )
		else:		#this is the simple array
			entry = {"timestamp": ts, "psi": input_data[i]}
			print datadt, entry
			collection.update( { "timestamp": ts}, entry, upsert=True )


if __name__ == '__main__':
	dtnow = datetime.now(tz=GMT8())		# time at which the script is run

	psi3hr_collection = db_init('psi_db', 'psi_readings')
	psi24hr_collection = db_init('psi_db', 'psi_24hr_pm25')

	# not time to check yet
	if not should_poll_nea(psi3hr_collection) and not should_poll_nea(psi24hr_collection):
		exit(0)	

	psihtml = get_psi_page()
	psihtml_3hr = substr_html(psihtml, '3-hr PSI Readings', '</table>')

	#get 3 hour PSI values
	psi_readings = get_td(psihtml_3hr)

	# 24 hour PSI values
	psihtml_24hr = substr_html(psihtml, '24-hr PSI Readings', '</table>')
	psi24hr_readings = get_td(psihtml_24hr)
	psi24hr_structured = structure_table(psi24hr_readings, ['North', 'South', 'East', 'West', 'Central'])

	# psi_readings is in the format [ 180, 230, 123, ... ]
	# each number is an hourly psi reading, starting from 1am
	# iterate through this array insert hourly data into the database

	# get today's date from the page
	datadt = datetime_from_html(psihtml, '3-hr PSI Readings from 1am to 12am on')
	insert_data(psi3hr_collection, psi_readings, dtnow, datadt)

	datadt = datetime_from_html(psihtml, '24-hr PSI Readings from 1am to 12am on')
	insert_data(psi24hr_collection, psi24hr_structured, dtnow, datadt)
