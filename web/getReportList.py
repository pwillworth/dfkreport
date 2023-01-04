#!/usr/bin/env python3
"""

 Copyright 2022 Paul Willworth <ioscode@gmail.com>

"""

import sys
import cgi
from web3 import Web3
sys.path.append("../")
import db

#

def getReportList(account):
    result = ''
    con = db.aConn()
    cur = con.cursor()
    cur.execute("SELECT account, startDate, endDate, generatedTimestamp, reportStatus, transactions, transactionsFetched, transactionsComplete, reportContent FROM reports WHERE proc=0 and user = %s ORDER BY generatedTimestamp DESC", (account,))
    row = cur.fetchone()
    while row != None:
        result += '["{0}","{1}","{2}",{3},{4},{5},{6},{7},"{8}"],'.format(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
        row = cur.fetchone()
    con.close()

    return result[:-1]

# Main program
form = cgi.FieldStorage()
# Get form info
account = form.getfirst("account", "")
sid = form.getfirst('sid', '')
# escape input to prevent sql injection
account = db.dbInsertSafe(account)
sid = db.dbInsertSafe(sid)
loginState = 0

print('Content-type: text/json\n')
if not Web3.isAddress(account):
    listResult = 'Error: That is not a valid address.  Make sure you enter the version that starts with 0x'
else:
    # Ensure consistent checksum version of address
    account = Web3.toChecksumAddress(account)
    if sid != '':
        sess = db.getSession(sid)
        if sess == account:
            loginState = 1
    if loginState > 0:
        listResult = getReportList(account)
    else:
        listResult = 'Error: Login first to view reports'

if (listResult.find("Error:") > -1):
    print('{ "error" : "'+listResult+'"}')
else:
    print('{ "reports" : ['+listResult+']}')