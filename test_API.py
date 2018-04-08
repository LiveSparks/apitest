import unittest
import requests

addDataURL = 'http://127.0.0.1:5000/post_location'
baseURL ='http://127.0.0.1:5000/'

class testFlask(unittest.TestCase):

	def setUp(self):
		pass

	def test_existing_pincode(self):
		data = {
			'pincode':'IN/110001',
			'place_name':'Connaught Place',
			'admin_name1':'New Delhi',
			'longitude':77.2167,
			'latitude':28.6333,
			'accuracy':4
		}
		result = requests.post(addDataURL, data=data)
		string = result.text
		self.assertIn('This Pincode Already Exists!',string)

	def test_proximity_points(self):
		data={
			'pincode':'IN/99999',
			'place_name':'test_place',
			'admin_name1':'test_location',
			'longitude':77.2160,
			'latitude':28.6330,
			'accuracy':99
		}
		result = requests.post(addDataURL, data=data)
		string = result.text
		self.assertIn('A location already exists within',string)

	def test_key_null(self):
		data={
			'pincode':'IN/99999',
			'place_name':'test_place',
			'admin_name1':'test_location',
			'longitude':77.2160,
			'latitude':28.6330,
			'accuracy':99
		}
		data['pincode']='NULL'
		result = requests.post(addDataURL,data=data)
		string = result.text
		self.assertIn('You must supply a pincode',string)

	def test_place_name_null(self):
		data={
			'pincode':'IN/99999',
			'place_name':'test_place',
			'admin_name1':'test_location',
			'longitude':77.2160,
			'latitude':28.6330,
			'accuracy':99
		}
		data['place_name']='NULL'
		result = requests.post(addDataURL,data=data)
		string = result.text
		self.assertIn('You must supply a place name',string)

	def test_get_using_self(self):
		result = requests.get(baseURL+'get_using_self?longitude=77.216&latitude=28.633')
		string = result.text
		self.assertIn('Pincodes within 5Kms of given cordinates:',string)

	def test_get_using_postgres(self):
		result = requests.get(baseURL+'get_using_postgres?longitude=77.216&latitude=28.633')
		string = result.text
		self.assertIn('Pincodes within 5Kms of given cordinates:',string)

	def test_compare_get(self):
		result = requests.get(baseURL+'get_using_self?longitude=77.216&latitude=28.633')
		string = result.text
		get_self = string.split(':')
		result = requests.get(baseURL+'get_using_postgres?longitude=77.216&latitude=28.633')
		string = result.text
		get_postgres = string.split(':')
		self.assertTrue(set(get_self[1])==set(get_postgres[1]))

	def test_get_incomplete(self):
		result = requests.get(baseURL+'get_using_self')
		string = result.text
		self.assertIn('You must supply valid arguments!',string)

	def test_get_place(self):
		result = requests.get(baseURL+'get_place?longitude=77.216&latitude=28.633')
		string = result.text
		self.assertIn('The Point falls under:',string)

	def test_get_place_incomplete(self):
		result = requests.get(baseURL+'get_place')
		string = result.text
		self.assertIn('You must supply valid arguments!',string)

	def test_get_place_out_of_bound(self):
		result = requests.get(baseURL+'get_place?longitude=0&latitude=0')
		string = result.text
		self.assertIn("Given point doesn't fall under any known location!",string)

if __name__=='__main__':
	unittest.main()