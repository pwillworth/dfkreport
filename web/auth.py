#!/usr/bin/env python3
"""

 Copyright 2022 Paul Willworth <ioscode@gmail.com>

"""

import sys
import cgi
import hashlib
import time
import os
from web3 import Web3
from hexbytes import HexBytes
from eth_account.messages import encode_defunct
from datetime import timezone, datetime
import random
sys.path.append("../")
import db
#

def getSession(account, signature):
    result = 0
    con = db.aConn()
    cur = con.cursor()
    cur.execute("SELECT nonce FROM members WHERE account = %s", (account,))
    row = cur.fetchone()
    if row != None:
        result = row[0]
    else:
        con.close()
        return 'Error: account does not exist'

    msg = 'Lilas Ledger login uses no transaction or gas fees.\n\nClick Sign to verify you own this wallet and login.\n\nIf you have cookies enabled, your session can persist for up to 6 months or until you logout.\n\nnonce: {0}'.format(result)
    w3 = Web3(Web3.HTTPProvider(""))
    message = encode_defunct(text=msg)
    address = w3.eth.account.recover_message(message, signature=HexBytes(signature))
    sys.stderr.write('sig result {0} == {1}'.format(address, account))
    if address == account:
        # new session
        sidHash = str(time.time()) + account
        sid = hashlib.sha1(sidHash.encode()).hexdigest()
        updatestr = 'INSERT INTO sessions (sid, account, expires) VALUES (%s, %s, %s)'
        cur.execute(updatestr, (sid, account, time.time() + duration))
        # update login time and nonce for next login attempt
        generateTime = datetime.now(timezone.utc)
        updatestr = 'UPDATE members SET lastLogin=%s, nonce=%s WHERE account=%s'
        cur.execute(updatestr, (int(datetime.timestamp(generateTime)), random.randint(1,10000000), account))
        result = sid
    else:
        result = 'Error: authentication failed, bad signature'
    con.close()
    return result

# Main program
result = ''
linkappend = ''
#sessions persist up to 180 days
duration = 15552000

form = cgi.FieldStorage()
# Get form info
account = form.getfirst("account", "")
signature = form.getfirst("signature", "")
# escape input to prevent sql injection
account = db.dbInsertSafe(account)
signature = db.dbInsertSafe(signature)

print('Content-type: text/json\n')
if not Web3.isAddress(account):
    sessionResult = 'Error: That is not a valid address.  Make sure you enter the version that starts with 0x'
else:
    # Ensure consistent checksum version of address
    account = Web3.toChecksumAddress(account)
    sessionResult = getSession(account, signature)

print(''.join(('{ "sid" : "', sessionResult, '" }')))

