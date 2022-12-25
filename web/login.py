#!/usr/bin/env python3
"""

 Copyright 2022 Paul Willworth <ioscode@gmail.com>

"""

import sys
import cgi
import random
from datetime import timezone, datetime
from web3 import Web3
sys.path.append("../")
import db
#

def getAccountNonce(account):
    result = ''
    con = db.aConn()
    cur = con.cursor()
    cur.execute("SELECT nonce FROM members WHERE account = %s", (account,))
    row = cur.fetchone()
    if row != None:
        result = row[0]
    else:
        result = random.randint(1,10000000)
        generateTime = datetime.now(timezone.utc)
        cur.execute("INSERT INTO members (account, nonce, generatedTimestamp) VALUES (%s, %s, %s)", (account, result, int(datetime.timestamp(generateTime))))

    con.close()

    return result

# Main program
form = cgi.FieldStorage()
# Get form info
account = form.getfirst("account", "")
sid = form.getfirst('sid', '')
# escape input to prevent sql injection
account = db.dbInsertSafe(account)
sid = db.dbInsertSafe(sid)
# Get a session
print('Content-type: text/json\n')
if not Web3.isAddress(account):
    nonceResult = 'Error: That is not a valid address.  Make sure you enter the version that starts with 0x'
    print(''.join(('{ "error" : ', str(nonceResult), ' }')))
else:
    # Ensure consistent checksum version of address
    account = Web3.toChecksumAddress(account)

    if sid != '':
        sess = db.getSession(sid)
        if sess == account:
            print(''.join(('{ "sid" : "', sid, '" }')))
        else:
            nonceResult = getAccountNonce(account)
            print(''.join(('{ "nonce" : ', str(nonceResult), ' }')))
        
    else:
        nonceResult = getAccountNonce(account)
        print(''.join(('{ "nonce" : ', str(nonceResult), ' }')))

