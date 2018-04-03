#!/usr/bin/env python3

import requests
import pandas
import credentials
import numpy
import smtplib
from datetime import datetime


def get_square_items(url='', creds=credentials):
	square_location = credentials.square['store']
	square_bearer_token = credentials.square['bearer_token']

	if url == '':
		url = 'https://connect.squareup.com/v1/' + square_location + '/items'

	r = requests.get(url, headers={'Authorization': 'Bearer ' + square_bearer_token, 'Accept': 'application/json'})

	data = r.json()
	for d in data:
		temp = []
		temp.append(d['variations'][0]['id'])
		temp.append(d['name'])
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

	url = 'https://api.bigcommerce.com/stores/' + credentials.bigcommerce['store'] + '/v3/catalog/products?include_fields=name,inventory_level&page=' + str(paginate) + '&limit=250'

	r = requests.get(url, headers=headers)
	data = r.json()
	for d in data['data']:
		temp = []
		temp.append(d['name'])
		temp.append(d['inventory_level'])
		b.append(temp)

	# pprint.pprint(data)

	if data['meta']['pagination']['current_page'] != data['meta']['pagination']['total_pages']:
		next_page = data['meta']['pagination']['current_page'] + 1
		get_bigcommerce_inventory(next_page=next_page)

	return b


i = []
q = []
b = []
square_items = get_square_items()
square_quantity = get_square_quantity()
bigcommerce_inventory = get_bigcommerce_inventory()
df1 = pandas.DataFrame(square_items, columns=['iD', 'name'])
df2 = pandas.DataFrame(square_quantity, columns=['iD', 'squareQuantity'])
df3 = pandas.DataFrame(bigcommerce_inventory, columns=['name', 'bigCommerceQuantity'])
df_square_combine = pandas.merge(df1, df2, on='iD', how='outer')
df_square_bigcommerce = pandas.merge(df_square_combine, df3, on='name', how='outer')
np_diff = numpy.where(df_square_bigcommerce['squareQuantity'] != df_square_bigcommerce['bigCommerceQuantity'], df_square_bigcommerce['name'], '')
df_diff = pandas.DataFrame(np_diff, columns=['name'])
df_merged = pandas.merge(df_diff, df_square_bigcommerce, on='name', how='inner')

difference = ''
for index, row in df_merged.iterrows():
	difference = row[1] + ', ' + row[0] + ', ' + str(row[2]) + ', ' + str(row[3]) + '\n' + difference
print(difference)

today = datetime.now()
today = today.strftime("%B %d, %Y %I:%M%p - %A")
message = 'Subject: Inventory Results (' + today + ')\nData...\n' + difference
message = message.encode("utf8")
email_from = credentials.email['email']
email_to = 'nick.krumholz@gmail.com'
email_pass = credentials.email['password']

smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
smtpObj.ehlo()
smtpObj.starttls()
smtpObj.login(email_from, email_pass)
smtpObj.sendmail(email_from, email_to, message)
smtpObj.quit()
