import os
import exifread
import mysql.connector
import decimal
from tkinter import filedialog
from tkinter import *

root = Tk()
root.withdraw()
path = filedialog.askdirectory()
table_name = 'photos'

cnx = mysql.connector.connect(user='root', password='root', database='jpg_geo', host='localhost')
statement = "CREATE TABLE `" + table_name + "` (`datestamp` varchar(255) NOT NULL,`lat` varchar(255) NOT NULL,`lon` varchar(255) NOT NULL,`path` varchar(640) NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=latin1;"
cur = cnx.cursor()
cur.execute(statement)
cnx.commit()

def directory_walk(rootdir):
	result = []
	for subdir, dirs, files in os.walk(rootdir):
		for file in files:
			result.append(os.path.join(subdir, file))
	return result

def divide_up(string):
	if "/" in string:
		divisible = string.split("/")
		result = float(divisible[0]) / float(divisible[1])
	else:
		result = string
	return result

def convert_geo_format(string):
	try:
		final_string = ""
		if len(string) > 0:
			res = string.replace("]","")
			res = res.replace("[","")
			res = res.split(",")
			first_bit = divide_up(res[0])
			second_bit = divide_up(res[1])
			third_bit = divide_up(res[2])
			final_string = str(first_bit) + "-" + str(second_bit) + "-" + str(third_bit) + "N" # Needs work
		return final_string
	except:
		return "0"

def parse_geo(latitude, longitude):
	new_latitude = 0
	new_longitude = 0
	if len(latitude) > 4 and len(longitude) > 4:
		new_latitude = sum(float(x) / 60 ** n for n, x in enumerate(latitude[:-1].split('-')))  * (1 if 'N' in latitude[-1] else -1)
		new_longitude = sum(float(x) / 60 ** n for n, x in enumerate(longitude[:-1].split('-'))) * (1 if 'E' in longitude[-1] else -1)
	return new_latitude, new_longitude

def get_exif_data(path_name, tagname):
	f = open(path_name, 'rb')
	tags = exifread.process_file(f)
	result = ""
	for tag in tags.keys():
		if tag == tagname:
			result = str(tags[tag])
	return result

def collect_geos(all_jpgs):
	for i in all_jpgs:
		descr = ""
		exif_date = 'EXIF DateTimeOriginal'
		exif_lat = 'GPS GPSLatitude'
		exif_lon = 'GPS GPSLongitude'
		date = get_exif_data(i, exif_date)
		latitude = convert_geo_format(get_exif_data(i, exif_lat))
		longitude = convert_geo_format(get_exif_data(i, exif_lon))
		decimal_geo = parse_geo(latitude, longitude)
		if decimal_geo != (0,0):
			deci = str(decimal_geo[0]) + ", " + str(decimal_geo[1])
		else:
			deci = ""
		cur = cnx.cursor()
		if "'" in i:
			i = ""
		try:
			statement = "INSERT INTO " + table_name + " (datestamp, lat, lon, path) VALUES ('" + str(date) + "', '" + str(decimal_geo[0]) + "', '" + str(decimal_geo[1]) + "', '" + str(i) + "')"
			cur.execute(statement)
			cnx.commit()
			print(i)
		except:
			continue

all_files = directory_walk(path)
all_jpgs = [jpg for jpg in all_files if '.JPG' in jpg]

collect_geos(all_jpgs)