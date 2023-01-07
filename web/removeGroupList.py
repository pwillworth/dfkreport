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

def removeGroupList(account, groupName):
    result = 0
    con = db.aConn()
    with con.cursor() as cur:
        cur.execute("DELETE FROM groups WHERE account=%s AND groupName=%s", (account, groupName))
        result = cur.rowcount
    con.close()

    return result

# Main program
form = cgi.FieldStorage()
# Get form info
sid = form.getfirst("sid", "")
account = form.getfirst("account", "")
groupName = form.getfirst("groupName", "")
# escape input to prevent sql injection
account = db.dbInsertSafe(account)
groupName = db.dbInsertSafe(groupName)
sid = db.dbInsertSafe(sid)
loginState = 0
failure = False
response = ''

if sid != '' and Web3.isAddress(account):
    account = Web3.toChecksumAddress(account)
    sess = db.getSession(sid)
    if sess == account:
        loginState = 1

if loginState < 1:
    failure = True
    response = ''.join(('{ "error" : "Error: You need be logged in to delete wallet groups." }'))

print('Content-type: text/json\n')
if failure == False:
    listResult = removeGroupList(account, groupName)
    response = ''.join(('{ "updated": ', str(listResult), ' }'))

print(response)
