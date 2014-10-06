import unittest
import mongomock
from datetime import datetime, tzinfo, timedelta
import pymongo
import getpsi

class GMT8(tzinfo):
	def utcoffset(self, dt):
		return timedelta(hours=8) + self.dst(dt)
	def dst(self, dt):
		return timedelta(0)
	def tzname(self,dt):
		return "GMT +8"

class DatabaseTests(unittest.TestCase):
	def test_db_init_psi_readings(self):
		collection = getpsi.db_init('psi_db', 'psi_readings')
		assert isinstance(collection, pymongo.collection.Collection)

	def test_db_init_fail(self):
		collection = getpsi.db_init('non_existent', 'non_existent')
		self.assertIsNone(collection)

class Psi3Hour(unittest.TestCase):
	def test_should_poll_nea_yes(self):
		collection = mongomock.Connection().db.collection
		# latest timestamp more than 1 hour ago
		data_time = datetime.now(tz=GMT8()) - timedelta(hours=2)
		data_time = getpsi.dt_to_unixtime(data_time)
		collection.insert(dict(timestamp=data_time))

		result = getpsi.should_poll_nea(collection)
		self.assertIs(result, True)

	def test_should_poll_nea_no(self):
		collection = mongomock.Connection().db.collection
		# latest timestamp more than 1 hour ago
		data_time = datetime.now(tz=GMT8()) - timedelta(minutes=2)
		data_time = getpsi.dt_to_unixtime(data_time)
		collection.insert(dict(timestamp=data_time))

		result = getpsi.should_poll_nea(collection)
		self.assertIs(result, False)
