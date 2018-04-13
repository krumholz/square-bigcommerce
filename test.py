#!/usr/bin/env python3

import logging
import requests
import pandas
import credentials
import numpy
from datetime import datetime
import messageMyself

# logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(filename='/Applications/MAMP/htdocs/square-bigcommerce/errorLog.txt', level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')
# logging.disable(logging.INFO)
logging.debug('Start of program')


def get_square_items(url='', creds=credentials):
	square_location = credentials.square['store']
	square_bearer_token = credentials.square['bearer_token']
	if url == '':
		url = 'https://connect.squareup.com/v1/' + square_location + '/items'

	r = requests.get(url, headers={'Authorization': 'Bearer ' + square_bearer_token, 'Accept': 'application/json'})
	logging.info('%s', r.headers)
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
	logging.info('%s', r.headers)
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
	url = 'https://api.bigcommerce.com/stores/' + credentials.bigcommerce['store'] + '/v3/catalog/products?page=' + str(paginate) + '&limit=250&include=variants&include_fields=name,inventory_level,inventory_tracking,current_page,total_pages,label'

	r = requests.get(url, headers=headers)
	logging.info('%s', r.headers)
	data = r.json()
	for d in data['data']:
		temp = []
		if d['variants'][0]['option_values']:
			for each in d['variants']:
				temp2 = []
				temp2.append(d['name'] + ' {' + each['option_values'][0]['label'] + '}')
				temp2.append(each['inventory_level'])
				if d['inventory_tracking'] == 'none':
					temp2.append(False)
				else:
					temp2.append(d['inventory_tracking'])
				b.append(temp2)
		else:
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

message = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd"><html lang="en"><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="X-UA-Compatible" content="IE=edge"><title>Inventory Results</title><style type="text/css"></style></head><body style="margin:0; padding:0; background-color:#FFFFFF; padding:20px;"><center><table width="100%" border="0" cellpadding="0" cellspacing="0" bgcolor="#FFFFFF"><tr><td align="center" valign="top">This report is for informational and troubleshooting purposes and should be used as a tool to determine if items listed here require updates. For example, items that are added directly to Square for the sake of variable pricing in-store, will appear in the first section but will not need corrective action.</td></tr>'
message = message + '<tr><td>&nbsp;</td></tr><tr><td><h3>In Square but not in BigCommerce: ' + str(squareUniques.shape[0]) + ' Items</h3></td></tr>'
for index, row in squareUniques.iterrows():
    message = message + '<tr><td>' + row['name'] + '</td></tr>'
message = message + '<tr><td>&nbsp;</td></tr><tr><td><h3>In BigCommerce but not in Square: ' + str(bcUniques.shape[0]) + ' Items</h3></td></tr>'
for index, row in bcUniques.iterrows():
    message = message + '<tr><td>' + row['name'] + '</td></tr>'
message = message + '<tr><td>&nbsp;</td></tr><tr><td><h3>Inventory Tracking settings that do not Match: ' + str(sqTrackingFalse.shape[0] + bcTrackingFalse.shape[0]) + ' Items</h3></td></tr>'
for index, row in sqTrackingFalse.iterrows():
    message = message + '<tr><td>' + row['name'] + '</td></tr>'
for index, row in bcTrackingFalse.iterrows():
    message = message + '<tr><td>' + row['name'] + '</td></tr>'
message = message + '<tr><td>&nbsp;</td></tr><tr><td><h3>Inventory quantities that do not match: ' + str(dfWithoutTrackingMismatches.shape[0]) + ' Items</h3></td></tr>'
messageLoop = ''
for index, row in dfWithoutTrackingMismatches.iterrows():
	messageLoop = messageLoop + '<tr><td>' + row['name'] + ' ' + str(row['squareQuantity']) + ' ' + str(row['bigCommerceQuantity']) + '</td></tr>'
message = message + messageLoop
message = message + '</table></center></body></html>'
# message = message.encode("utf8")
logging.info('%s', message)

today = datetime.now()
today = today.strftime("%B %d, %Y %I:%M%p - %A")
subject = 'Inventory Results (' + today + ')'
messageMyself.emailMyself(subject, message)

logging.debug('End of program')
