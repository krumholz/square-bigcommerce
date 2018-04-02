#!/usr/bin/env python3

import requests
import pandas
import credentials


def get_items(url='', creds=credentials):
	square_location = credentials.square['location']
	square_bearer_token = credentials.square['bearer_token']

	if url == '':
		url = 'https://connect.squareup.com/v1/' + square_location + '/items'

	r = requests.get(url, headers={'Authorization': 'Bearer ' + square_bearer_token, 'Accept': 'application/json'})

	data = r.json()
	for d in data:
		temp = []
		temp.append(d['id'])
		temp.append(d['name'])
		s.append(temp)

	if r.headers.get('Link') is not None:
		next_page = r.headers.get('Link')
		next_page = next_page[1:].split('>')
		next_page = next_page[0]
		get_items(url=next_page)

	return s


s = []
square_items = get_items()
df = pandas.DataFrame(square_items, columns=['ID', 'Name'])
print(df)
