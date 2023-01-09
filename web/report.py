#!/usr/bin/env python3
"""

 Copyright 2023 Paul Willworth <ioscode@gmail.com>

"""

import os
import sys
import cgi
import jsonpickle
from jinja2 import Environment, FileSystemLoader
sys.path.append("../")
import db

# Get current url
try:
	url = os.environ['SCRIPT_NAME']
except KeyError:
	url = ''

form = cgi.FieldStorage()
# Get form info
contentFile = form.getfirst("contentFile", "")
# escape input to prevent sql injection
contentFile = db.dbInsertSafe(contentFile)

accounts = ''
startDate = ''
endDate = ''
costBasis = ''
includedChains = 5
purchaseAddresses = ''
walletGroup = ''
# When content file is passed, viewing a pregenerated report and we look up its options to preset the form
if contentFile != '':
	con = db.aConn()
	with con.cursor() as cur:
		cur.execute('SELECT account, startDate, endDate, costBasis, includedChains, moreOptions, walletGroup, wallets FROM reports WHERE reportContent=%s', (contentFile,))
		row = cur.fetchone()
		if row != None:
			account = row[0]
			if row[6] != '':
				accounts = '{0}'.format(row[6])
			wallets = jsonpickle.decode(row[7])
			for wallet in wallets:
				accounts = '{0}\n{1}...{2}'.format(accounts, wallet[0:6], wallet[38:42])
			startDate = row[1]
			endDate = row[2]
			costBasis = row[3]
			includedChains = row[4]
			moreOptions = jsonpickle.loads(row[5])
			purchaseAddresses = moreOptions['purchaseAddresses']
			walletGroup = row[6]
	con.close()
else:
    accounts = 'Error: Report content not found'

print('Content-type: text/html\n')
env = Environment(loader=FileSystemLoader('templates'))

template = env.get_template('report.html')
print(template.render(url=url, contentFile=contentFile, account=account, startDate=startDate, endDate=endDate, costBasis=costBasis, includedChains=includedChains, purchaseAddresses=purchaseAddresses, walletGroup=walletGroup, wallets=accounts))
