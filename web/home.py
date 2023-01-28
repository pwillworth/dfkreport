#!/usr/bin/env python3
"""

 Copyright 2021 Paul Willworth <ioscode@gmail.com>

"""

import os
import sys
import cgi
import logging
from http import cookies
from web3 import Web3
from jinja2 import Environment, FileSystemLoader
sys.path.append("../")
import db
import balances

logging.basicConfig(filename='../home.log', level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
# Get current url
try:
	url = os.environ['SCRIPT_NAME']
except KeyError:
	url = ''

form = cgi.FieldStorage()
# Get Cookies
useCookies = 1
C = cookies.SimpleCookie()
try:
	C.load(os.environ['HTTP_COOKIE'])
except KeyError:
	useCookies = 0

if useCookies:
	try:
		account = C['selectedAccount'].value
	except KeyError:
		account = form.getfirst('account', '')
	try:
		sid = C['sid-{0}'.format(account)].value
	except KeyError:
		sid = form.getfirst('sid', '')
else:
	sid = form.getfirst('sid', '')
	account = form.getfirst('account', '')

sid = db.dbInsertSafe(sid)

loginState = 0
memberState = 0
if sid != '' and Web3.isAddress(account):
	account = Web3.toChecksumAddress(account)
	sess = db.getSession(sid)
	if sess == account:
		loginState = 1

bankState = 'ragmanEmpty'
bankMessage = '<span style="color:red;">Warning!</span> <span style="color:white;">Monthly hosting fund goal not reached, please help fill the ragmans crates!</span>'
balance = balances.readCurrent()
bankProgress = '${0:.2f}'.format(balance)
if balance >= 30:
	bankState = 'ragman'
	bankMessage = 'Thank You!  The ragmans crates are full and the hosting bill can be paid this month!'

# get subscription status
if loginState > 0:
	memberState = db.getMemberStatus(account)[0]
else:
	memberState = 0

print('Content-type: text/html\n')
env = Environment(loader=FileSystemLoader('templates'))

template = env.get_template('home.html')
print(template.render(url=url, memberState=memberState, bankState=bankState, bankProgress=bankProgress, bankMessage=bankMessage))
