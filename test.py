#!/usr/bin/env python3

import requests
import pandas
import credentials
import numpy


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
		temp.append(d['quantity_on_hand'])
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
df1 = pandas.DataFrame(square_items, columns=['ID', 'Name'])
df2 = pandas.DataFrame(square_quantity, columns=['ID', 'Square Quantity'])
df3 = pandas.DataFrame(bigcommerce_inventory, columns=['Name', 'BigCommerce Quantity'])
df_square_combine = pandas.merge(df1, df2, on='ID', how='outer')
df_square_bigcommerce = pandas.merge(df_square_combine, df3, on='Name', how='outer')
df_diff = numpy.where(df_square_bigcommerce['Square Quantity'] != df_square_bigcommerce['BigCommerce Quantity'], df_square_bigcommerce['Name'], '')

for dif in df_diff:
	if dif != '':
		print(dif)
