import unittest
import mongomock
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

	def test_get_psi_page(self):
		psihtml = getpsi.get_psi_page()
		self.assertIn('3-hr PSI Readings from 1am to 12am on', psihtml)
		self.assertIn('24-hr PSI Readings from 1am to 12am on', psihtml)

	def test_parse_day_from_html_1(self):
		# test single digit day
		psihtml = """abcde<h1>3-hr PSI Readings from 1am to 12am on
                        06 Oct 2014</h1>"""
		result = getpsi.parse_day_from_html(psihtml, '3-hr PSI Readings from 1am to 12am on')

		self.assertEqual(result, 6)

	def test_parse_day_from_html_2(self):
		# test double digit day
		psihtml = """abc<h1>3-hr PSI Readings from 1am to 12am on
                        23 Oct 2014</h1>"""
		result = getpsi.parse_day_from_html(psihtml, '3-hr PSI Readings from 1am to 12am on')

		self.assertEqual(result, 23)

	def test_parse_day_from_html_3(self):
		# test double digit day, with 24-hr table
		psihtml = """abc<h1 style="display:inline-block">24-hr PSI Readings from 1am to 12am on
                        23 Oct 2014</h1>"""
		result = getpsi.parse_day_from_html(psihtml, '24-hr PSI Readings from 1am to 12am on')

		self.assertEqual(result, 23)

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
		expected = [139, 134, 122, 105, 90, 89, 93, 91, 83, 73, 68, 66,
					67, 70, 75, 80, 83, 80, 75, 68, 64, 63]

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
		
		
		
		
		
