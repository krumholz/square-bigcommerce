#!/usr/bin/env python3

import logging
import requests
import pandas
import credentials
import numpy
from datetime import datetime
import messageMyself

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')
# logging.basicConfig(filename='errorLog.txt', level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')
# logging.disable(logging.INFO)
logging.debug('Start of program')


def get_square_items(url='', creds=credentials):
	square_location = credentials.square['store']
	square_bearer_token = credentials.square['bearer_token']
	if url == '':
		url = 'https://connect.squareup.com/v1/' + square_location + '/items'

	r = requests.get(url, headers={'Authorization': 'Bearer ' + square_bearer_token, 'Accept': 'application/json'})
	data = r.json()
	for d in data:
		temp = []
		if len(d['variations']) > 1:
			for each in d['variations']:
				temp2 = []
				temp2.append(each['id'])
				temp2.append(d['name'] + ' {' + each['name'] + '}')
				temp2.append(each['track_inventory'])
				i.append(temp2)
		else:
			temp.append(d['variations'][0]['id'])
			temp.append(d['name'])
			temp.append(d['variations'][0]['track_inventory'])
			i.append(temp)

	if r.headers.get('Link') is not None:
		next_page = r.headers.get('Link')
		next_page = next_page[1:].split('>')
		next_page = next_page[0]
		get_square_items(url=next_page)
	return i


def get_square_quantity(url='', creds=credentials):
	square_location = credentials.square['store']
	square_bearer_token = credentials.square['bearer_token']
	if url == '':
		url = 'https://connect.squareup.com/v1/' + square_location + '/inventory'

	r = requests.get(url, headers={'Authorization': 'Bearer ' + square_bearer_token, 'Accept': 'application/json'})
	data = r.json()
	for d in data:
		temp = []
		temp.append(d['variation_id'])
		if isinstance(d['quantity_on_hand'], int):
			temp.append(d['quantity_on_hand'])
		else:
			temp.append(0)
		q.append(temp)

	if r.headers.get('Link') is not None:
		next_page = r.headers.get('Link')
		next_page = next_page[1:].split('>')
		next_page = next_page[0]
		get_square_quantity(url=next_page)
	return q


def get_bigcommerce_inventory(next_page='', creds=credentials):
	headers = {
		'X-Auth-Client': credentials.bigcommerce['client_id'],
		'X-Auth-Token': credentials.bigcommerce['access_token'],
		'Accept': 'application/json',
		'Content-Type': 'application/json'
	}
	if next_page == '':
		paginate = 1
	else:
		paginate = next_page
	# url = 'https://api.bigcommerce.com/stores/' + credentials.bigcommerce['store'] + '/v3/catalog/products?include_fields=name,inventory_level&page=' + str(paginate) + '&limit=250'
	url = 'https://api.bigcommerce.com/stores/' + credentials.bigcommerce['store'] + '/v3/catalog/products?page=' + str(paginate) + '&limit=250'

	r = requests.get(url, headers=headers)
	data = r.json()
	for d in data['data']:
		temp = []
		temp.append(d['name'])
		temp.append(d['inventory_level'])
		if d['inventory_tracking'] == 'none':
			temp.append(False)
		else:
			temp.append(d['inventory_tracking'])
		b.append(temp)
	if data['meta']['pagination']['current_page'] != data['meta']['pagination']['total_pages']:
		next_page = data['meta']['pagination']['current_page'] + 1
		get_bigcommerce_inventory(next_page=next_page)
	return b


i = []
q = []
b = []
square_items = get_square_items()
df1 = pandas.DataFrame(square_items, columns=['iD', 'name', 'squareTracking'])
square_quantity = get_square_quantity()
df2 = pandas.DataFrame(square_quantity, columns=['iD', 'squareQuantity'])
df_square_combined = pandas.merge(df1, df2, on='iD', how='outer')
bigcommerce_inventory = get_bigcommerce_inventory()
df3 = pandas.DataFrame(bigcommerce_inventory, columns=['name', 'bigCommerceQuantity', 'bigCommerceTracking'])

df_square_bigcommerce = pandas.merge(df_square_combined, df3, on='name', how='outer')
squareUniques = df_square_combined[(~df_square_combined['name'].isin(df3['name']))]
bcUniques = df3[(~df3['name'].isin(df_square_combined['name']))]
dfWithoutNameMismatches = df_square_bigcommerce[(~df_square_bigcommerce['name'].isin(squareUniques['name']))]
dfWithoutNameMismatches = dfWithoutNameMismatches[(~dfWithoutNameMismatches['name'].isin(bcUniques['name']))]
dfWithoutNameMismatches['trackingOn'] = numpy.where(dfWithoutNameMismatches['squareTracking'] != dfWithoutNameMismatches['bigCommerceTracking'], True, False)
dfTrackingOn = dfWithoutNameMismatches[dfWithoutNameMismatches['trackingOn'] == True]
sqTrackingFalse = dfTrackingOn[dfTrackingOn['squareTracking'] == False]
bcTrackingFalse = dfTrackingOn[dfTrackingOn['bigCommerceTracking'] == False]
dfWithoutTrackingMismatches = dfTrackingOn[dfTrackingOn['squareQuantity'] != dfTrackingOn['bigCommerceQuantity']]

log = {}
square_qty_nan = df_square_combined['squareQuantity'].isna().sum()
log['sqQtyNan'] = square_qty_nan
square_tracking_qty = df_square_combined['squareTracking'].value_counts()
log['sqTrackingQtyFalse'] = square_tracking_qty[False]
bcTracking = df3['bigCommerceTracking'].value_counts()
log['bcTrackingQtyFalse'] = bcTracking[False]
square_qty_not_nan = df_square_combined['squareQuantity'].count()
log['sqQtyNotNan'] = square_qty_not_nan
log['sqTrackingQtyTrue'] = square_tracking_qty[True]
log['bcTrackingQtyProduct'] = bcTracking['product']
logging.info('%s', log)

message = 'In Square but not in BigCommerce: ' + str(squareUniques.shape[0]) + ' items\n'
message = message + '\n'.join(squareUniques['name'])
message = message + '\n\nIn BigCommerce but not in Square: ' + str(bcUniques.shape[0]) + ' items\n'
message = message + '\n'.join(bcUniques['name'])
message = message + '\n\nInventory tracking that does not match in Square or BigCommerce: ' + str(sqTrackingFalse.shape[0] + bcTrackingFalse.shape[0]) + ' items\n'
message = message + '\n'.join(sqTrackingFalse['name']) + '\n' + '\n'.join(bcTrackingFalse['name'])
message = message + '\n\nInventory quantities that do not match: ' + str(dfWithoutTrackingMismatches.shape[0]) + ' items\n'
messageLoop = ''
for index, row in dfWithoutTrackingMismatches.iterrows():
	messageLoop = messageLoop + row['name'] + ' ' + str(row['squareQuantity']) + ' ' + str(row['bigCommerceQuantity']) + '\n'
message = message + messageLoop
logging.info('%s', message)

# np_diff = numpy.where(df_square_bigcommerce['squareQuantity'] != df_square_bigcommerce['bigCommerceQuantity'], df_square_bigcommerce['name'], '')
# df_diff = pandas.DataFrame(np_diff, columns=['name'])
# df_merged = pandas.merge(df_diff, df_square_bigcommerce, on='name', how='inner')
#
# difference = ''
# for index, row in df_merged.iterrows():
# 	difference = str(row[1]) + ', ' + str(row[0]) + ', ' + str(row[2]) + ', ' + str(row[3]) + '\n' + difference
# print(difference)
#
# today = datetime.now()
# today = today.strftime("%B %d, %Y %I:%M%p - %A")
# message = 'Subject: Inventory Results (' + today + ')\nData...\n\n' + difference
# messageMyself.emailMyself(message)

logging.debug('End of program')
