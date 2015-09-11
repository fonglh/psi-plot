import unittest
import mongomock
from nose.tools import nottest
from datetime import datetime, tzinfo, timedelta
import pymongo
import getpsi
from bs4 import BeautifulSoup

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
	def setUp(self):
		f = open('test_data.html')
		self.psi_html = f.read()

	@unittest.skip("mongomock fails with no attribute 'Connection'")
	def test_should_poll_nea_yes(self):
		collection = mongomock.Connection().db.collection
		# latest timestamp more than 1 hour ago
		data_time = datetime.now(tz=GMT8()) - timedelta(hours=2)
		data_time = getpsi.dt_to_unixtime(data_time)
		collection.insert(dict(timestamp=data_time))

		result = getpsi.should_poll_nea(collection)
		self.assertIs(result, True)

	@unittest.skip("mongomock fails with no attribute 'Connection'")
	def test_should_poll_nea_no(self):
		collection = mongomock.Connection().db.collection
		# latest timestamp more than 1 hour ago
		data_time = datetime.now(tz=GMT8()) - timedelta(minutes=2)
		data_time = getpsi.dt_to_unixtime(data_time)
		collection.insert(dict(timestamp=data_time))

		result = getpsi.should_poll_nea(collection)
		self.assertIs(result, False)

	@nottest
	def test_get_psi_page(self):
		psihtml = getpsi.get_psi_page()
		self.assertIn('3-hr PSI Readings from 1am to 12am on', psihtml)
		self.assertIn('24-hr PSI Readings from 1am to 12am on', psihtml)

	def test_datetime_from_html_1(self):
		# test single digit day
		psihtml = """abcde<h1>3-hr PSI Readings from 1am to 12am on
                        06 Oct 2014</h1>"""
		result = getpsi.datetime_from_html(psihtml, '3-hr PSI Readings from 1am to 12am on')

		self.assertEqual(result, datetime(2014, 10, 6, tzinfo=GMT8()))

	def test_datetime_from_html_2(self):
		# test double digit day
		psihtml = """abc<h1>3-hr PSI Readings from 1am to 12am on
                        23 Oct 2014</h1>"""
		result = getpsi.datetime_from_html(psihtml, '3-hr PSI Readings from 1am to 12am on')

		self.assertEqual(result, datetime(2014, 10, 23, tzinfo=GMT8()))

	def test_datetime_from_html_3(self):
		# test double digit day, with 24-hr table
		psihtml = """abc<h1 style="display:inline-block">24-hr PSI Readings from 1am to 12am on
                        31 Aug 2014</h1>"""
		result = getpsi.datetime_from_html(psihtml, '24-hr PSI Readings from 1am to 12am on')

		self.assertEqual(result, datetime(2014, 8, 31, tzinfo=GMT8()))

	def test_substr_html(self):
		html = """abc<h1 style="display:inline-block">24-hr PSI Readings from 1am to 12am on
                        23 Oct 2014</h1>dafds"""
		expected = """24-hr PSI Readings from 1am to 12am on
                        23 Oct 2014</h1>"""
		result = getpsi.substr_html(html, '24-hr PSI Readings', '</h1>')

		self.assertEqual(expected, result)

	def test_get_td_3hour_table(self):
		html = getpsi.substr_html(self.psi_html, '3-hr PSI Readings', '</table>')
		result = getpsi.get_td(html)
		expected = [68, 70, 73, 76, 78, 78, 78, 77, 76, 72, 71, 71,
					74, 77, 82, 87, 94, 102, 105, 107, 107, 104, 93, 82]

		self.assertEqual(result, expected)

	def test_extract_psi_number_bold(self):
		input_str = """<td align="center">
<strong style="font-size:14px;">63</strong>
</td>"""
		result = getpsi.extract_psi_number(input_str)

		self.assertEqual(result, 63)
		
	def test_extract_psi_number_normal(self):
		input_str = """<td align="center">
                    80
                </td>"""
		result = getpsi.extract_psi_number(input_str)

		self.assertEqual(result, 80)
		
	def test_extract_psi_number_dash(self):
		input_str = """<td align="center">
                    -
                </td>"""
		result = getpsi.extract_psi_number(input_str)

		self.assertIsNone(result)
		
	def test_extract_psi_number_rubbish(self):
		input_str = """<td align="center">
                   abcdefg 
                </td>"""
		result = getpsi.extract_psi_number(input_str)

		self.assertIsNone(result)

	def test_structure_table_3hr(self):
		input_arr = [68, 70, 73, 76, 78, 78, 78, 77, 76, 72, 71, 71,
					74, 77, 82, 87, 94, 102, 105, 107, 107, 104, 93, 82]	
		labels = []
		expected = [68, 70, 73, 76, 78, 78, 78, 77, 76, 72, 71, 71,
					74, 77, 82, 87, 94, 102, 105, 107, 107, 104, 93, 82]

		result = getpsi.structure_table(input_arr, labels)
		self.assertEqual(result, expected)

class Psi24Hour(unittest.TestCase):
	def setUp(self):
		f = open('test_data.html')
		self.psi_html = f.read()

	def test_get_td_24hour_table(self):
		html = getpsi.substr_html(self.psi_html, '24-hr PSI Readings', '</table>')
		result = getpsi.get_td(html)
		expected = [74, 72, 71, 71, 71, 71, 70, 71, 71, 72, 72, 73, 78, 75, 75, 75, 75, 74, 73, 73, 73, 73, 73, 73, 76, 75, 75, 75, 74, 73, 72, 72, 72, 72, 71, 72, 86, 82, 79, 78, 77, 77, 76, 76, 75, 75, 76, 76, 75, 72, 72, 72, 72, 71, 70, 70, 71, 70, 70, 71, 73, 74, 74, 74, 75, 75, 76, 78, 80, 81, 81, 80, 73, 74, 74, 74, 75, 76, 78, 80, 82, 83, 85, 85, 72, 73, 73, 73, 73, 74, 75, 77, 79, 80, 81, 81, 76, 76, 75, 77, 79, 82, 85, 87, 90, 91, 91, 92, 71, 72, 72, 72, 73, 74, 75, 77, 79, 79, 80, 80]

		self.assertEqual(result, expected)
		# sanity check, a full day of readings (24 hours) for 5 regions
		self.assertEqual(len(result), 120)

	def test_structure_table_24hr(self):
		input_arr = [74, 72, 71, 71, 71, 71, 70, 71, 71, 72, 72, 73, 78, 75, 75, 75, 75, 74, 73, 73, 73, 73, 73, 73, 76, 75, 75, 75, 74, 73, 72, 72, 72, 72, 71, 72, 86, 82, 79, 78, 77, 77, 76, 76, 75, 75, 76, 76, 75, 72, 72, 72, 72, 71, 70, 70, 71, 70, 70, 71, 73, 74, 74, 74, 75, 75, 76, 78, 80, 81, 81, 80, 73, 74, 74, 74, 75, 76, 78, 80, 82, 83, 85, 85, 72, 73, 73, 73, 73, 74, 75, 77, 79, 80, 81, 81, 76, 76, 75, 77, 79, 82, 85, 87, 90, 91, 91, 92, 71, 72, 72, 72, 73, 74, 75, 77, 79, 79, 80, 80]
		labels = ['North', 'South', 'East', 'West', 'Central']
		expected = {'North': [74, 72, 71, 71, 71, 71, 70, 71, 71, 72, 72, 73, 73, 74, 74, 74, 75, 75, 76, 78, 80, 81, 81, 80],
					'South': [78, 75, 75, 75, 75, 74, 73, 73, 73, 73, 73, 73, 73, 74, 74, 74, 75, 76, 78, 80, 82, 83, 85, 85],
					'East': [76, 75, 75, 75, 74, 73, 72, 72, 72, 72, 71, 72, 72, 73, 73, 73, 73, 74, 75, 77, 79, 80, 81, 81],
					'West': [86, 82, 79, 78, 77, 77, 76, 76, 75, 75, 76, 76, 76, 76, 75, 77, 79, 82, 85, 87, 90, 91, 91, 92],
					'Central': [75, 72, 72, 72, 72, 71, 70, 70, 71, 70, 70, 71, 71, 72, 72, 72, 73, 74, 75, 77, 79, 79, 80, 80]
		}

		result = getpsi.structure_table(input_arr, labels)
		self.assertEqual(result, expected)

