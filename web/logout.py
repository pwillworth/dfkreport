#!/usr/bin/env python3
"""

 Copyright 2022 Paul Willworth <ioscode@gmail.com>

"""

import sys
import cgi
from datetime import timezone, datetime
from web3 import Web3
sys.path.append("../")
import db

form = cgi.FieldStorage()
# Get form info
account = form.getfirst("account", "")
sid = form.getfirst('sid', '')
# escape input to prevent sql injection
account = db.dbInsertSafe(account)
sid = db.dbInsertSafe(sid)

loginState = 0

sess = db.getSession(sid)
if (sess != ''):
    loginState = 1
    currentUser = sess

print('Content-type: text/json\n')
if not Web3.isAddress(account):
    logoutResult = 'Error: That is not a valid address.  Make sure you enter the version that starts with 0x'
else:
    # Ensure consistent checksum version of address
    account = Web3.toChecksumAddress(account)
    if loginState > 0:
        conn = db.aConn()
        cursor = conn.cursor()
        updatestr = 'DELETE FROM sessions WHERE account=%s AND sid=%s'
        cursor.execute(updatestr, (account, sid))
        cursor.close()
        conn.close()
        logoutResult = 'logout complete'
    else:
        logoutResult = 'Error: session was not valid'

print(''.join(('{ "result" : "', str(logoutResult), '" }')))