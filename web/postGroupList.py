#!/usr/bin/env python3
"""

 Copyright 2022 Paul Willworth <ioscode@gmail.com>

"""

import sys
import jsonpickle
import cgi
import urllib
from web3 import Web3
sys.path.append("../")
import db

#

def addGroupList(account, groupName, addressList):
    result = 0
    con = db.aConn()
    with con.cursor() as cur:
        cur.execute("SELECT account, groupName, wallets FROM groups WHERE account = %s AND groupName=%s", (account,groupName))
        row = cur.fetchone()
        if row != None and row[0] != None:
            cur.execute("UPDATE groups SET wallets=%s, updatedTimestamp=UTC_TIMESTAMP() WHERE account=%s AND groupName=%s", (jsonpickle.encode(addressList), account, groupName))
        else:
            cur.execute("INSERT INTO groups (account, groupName, wallets) VALUES (%s, %s, %s)", (account, groupName, jsonpickle.encode(addressList)))
        result = cur.rowcount
    con.close()

    return result

# Main program
form = cgi.FieldStorage()
# Get form info
account = form.getfirst("account", "")
groupName = form.getfirst("groupName", "")
wallets = form.getfirst("wallets", "")
# escape input to prevent sql injection
account = db.dbInsertSafe(account)
groupName = db.dbInsertSafe(groupName)
failure = False
response = ''
addressList = []
if wallets != '':
    walletAddresses = urllib.parse.unquote(wallets)
    if ',' in walletAddresses:
        input = walletAddresses.split(',')
    else:
        input = walletAddresses.split()
    for address in input:
        address = address.strip()
        if Web3.isAddress(address):
            addressList.append(Web3.toChecksumAddress(address))
        elif len(address) == 0:
            continue
        else:
            response = ''.join(('{ "error" : "Error: You have an invalid address in the wallet list ', address, '." }'))
            failure = True

print('Content-type: text/json\n')
if failure == False:
    listResult = addGroupList(account, groupName, addressList)
    response = ''.join(('{ "updated": ', str(listResult), ' }'))

print(response)
