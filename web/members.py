#!/usr/bin/env python3
"""

 Copyright 2023 Paul Willworth <ioscode@gmail.com>

"""

import os
import sys
import cgi
from datetime import timezone, datetime
import math
from web3 import Web3
from jinja2 import Environment, FileSystemLoader
from http import cookies
sys.path.append("../")
import db

def timeDescription(seconds):
	appendStr = ''
	if seconds != 0:
		if seconds < 0:
			appendStr = ' ago'
		tmpDays = math.floor(seconds / 86400)
		tmpStr = ''
		if (tmpDays > 0):
			if (tmpDays > 365):
				tmpStr = str(math.floor(tmpDays / 365)) + " years, "
				tmpDays = tmpDays % 365
			tmpStr = tmpStr + str(tmpDays)+" days"
		elif (seconds % 3600 >= 1):
			tmpStr = str(math.floor(seconds/3600))+" hours"
		elif (seconds % 60 >= 1):
			tmpStr = str(math.floor(seconds/60))+" minutes"
		else:
			tmpStr = "less than a minute"
		return tmpStr + appendStr
	else:
	#except:
		return "no time"

# Get current url
try:
	url = os.environ['SCRIPT_NAME']
except KeyError:
	url = ''
# Extract query parameters
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
secondsLeft = 0
if sid != '' and Web3.isAddress(account):
    account = Web3.toChecksumAddress(account)
    sess = db.getSession(sid)
    if sess == account:
        loginState = 1

walletGroup = ''
requestTime = datetime.now(timezone.utc).timestamp()
# get subscription status
if loginState > 0:
	con = db.aConn()
	with con.cursor() as cur:
		cur.execute('SELECT expiresTimestamp FROM members WHERE account=%s', (account,))
		row = cur.fetchone()
		if row[0] != None:
			secondsLeft = row[0] - requestTime
		if row[0] != None and requestTime < row[0]:
			if secondsLeft > 0:
				memberState = 2
			else:
				memberState = 1
		else:
			memberState = 1

	con.close()
else:
    memberState = 0

print('Content-type: text/html\n')
env = Environment(loader=FileSystemLoader('templates'))

template = env.get_template('member.html')
print(template.render(url=url, memberState=memberState, secondsLeft=secondsLeft, expiryDescription=timeDescription(secondsLeft)))
