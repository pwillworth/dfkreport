#!/usr/bin/env python3
"""

 Copyright 2023 Paul Willworth <ioscode@gmail.com>

"""

import sys
import cgi
import time
from datetime import timezone, datetime
from web3 import Web3
import decimal
sys.path.append("../")
import db
import nets
import contracts
import events

#
PAYMENT_ADDRESS = '0x15Ca8d8d7048F694980C717369C55b53e4FbCAEe'
PAYMENT_TOKENS = {
    'dfkchain': ['0xCCb93dABD71c8Dad03Fc4CE5559dC3D89F67a260','0x04b9dA42306B023f3572e106B11D82aAd9D32EBb','0x3AD9DFE640E1A9Cc1D9B0948620820D975c3803a'],
    'klaytn': ['0x19Aac5f612f524B754CA7e7c41cbFa2E981A4432','0x30C103f8f5A3A732DFe2dCE1Cc9446f545527b43','0xB3F5867E277798b50ba7A71C0b24FDcA03045eDF']
}
TOKEN_SUB_VALUES = {
    '0x19Aac5f612f524B754CA7e7c41cbFa2E981A4432': 0.10, #klay
    '0xCCb93dABD71c8Dad03Fc4CE5559dC3D89F67a260': 0.50, #dfkJewel
    '0x30C103f8f5A3A732DFe2dCE1Cc9446f545527b43': 0.50, #klayJewel
    '0x04b9dA42306B023f3572e106B11D82aAd9D32EBb': 0.10, #crystal
    '0xB3F5867E277798b50ba7A71C0b24FDcA03045eDF': 0.10, #jabe
    '0x3AD9DFE640E1A9Cc1D9B0948620820D975c3803a': 1.00 #dfkUSDC
}
def getSubscriptionTime(token, amount):
    tokenRatio = TOKEN_SUB_VALUES[token]
    tokenValue = amount * decimal.Decimal(tokenRatio)
    if tokenValue < 0.5:
        return 0
    if tokenValue > 10:
        return tokenValue * 86400 * 6
    return tokenValue * 86400 * 4

def addPayment(account, txHash, token, amount, network, purchaseTime):
    result = 0
    con = db.aConn()
    with con.cursor() as cur:
        # ensure tx not already credited
        cur.execute("SELECT generatedTimestamp FROM payments WHERE txHash=%s AND network=%s", (txHash, network))
        row = cur.fetchone()
        if row != None and row[0] != None:
            result = -1
        else:
            # calculate time to add and new expiration
            generateTime = int(datetime.now(timezone.utc).timestamp())
            cur.execute("SELECT expiresTimestamp FROM members WHERE account = %s", (account))
            rowu = cur.fetchone()
            previousExpires = 0
            if rowu != None:
                if rowu[0] == None:
                    previousExpires = 0
                else:
                    previousExpires = rowu[0]
            # credit from current time if expired in past or from future if still active
            newExpires = max(generateTime, previousExpires) + int(purchaseTime)
            cur.execute("INSERT INTO payments (account, generatedTimestamp, txHash, token, amount, previousExpires, newExpires, network) VALUES (%s, UTC_TIMESTAMP(), %s, %s, %s, %s, %s, %s)", (account, txHash, token, amount, previousExpires, newExpires, network))
            result = cur.rowcount
            # member record updated if it existed otherwise payments can be picked up on member registration
            if rowu != None:
                cur.execute("UPDATE members SET expiresTimestamp=%s WHERE account=%s", (newExpires, account))
    con.close()

    return result

# Main program
form = cgi.FieldStorage()
# Get form info
network = form.getfirst("network", "")
account = form.getfirst("account", "")
txHash = form.getfirst("txHash", "")
# escape input to prevent sql injection
account = db.dbInsertSafe(account)
txHash = db.dbInsertSafe(txHash)
network = db.dbInsertSafe(network)

failure = False
response = ''
txToken = ''
tokenAmount = 0

if not Web3.isAddress(account):
    response = ''.join(('{ "error" : "Error: The account you provided is not a vaild wallet address: ', account, '." }'))
    failure = True
else:
    account = Web3.toChecksumAddress(account)

# Connect to right network that txs are for
if network == 'klaytn':
    w3 = Web3(Web3.HTTPProvider(nets.klaytn_web3))
elif network == 'dfkchain':
    w3 = Web3(Web3.HTTPProvider(nets.dfk_web3))
else:
    response = ''.join(('{ "error" : "Error: Invalid network,  ', network, ' only dfkchain and klaytn supported." }'))
    failure = True
if not w3.isConnected():
    response = ''.join(('{ "error" : "Error: Critical w3 connection failure for,  ', network, ', please try again later." }'))
    failure = True

# Initial Tx validation
if failure == False:
    # Pause a little to ensure tx is returned from this method as it is sometimes not found right after receipt is available
    time.sleep(5)
    try:
        result = w3.eth.get_transaction(txHash)
    except Exception as err:
        response = ''.join(('{ "error" : "Error: Invalid transaction, additional info: ', str(err), '." }'))
        failure = True

# Tx results Validation
if failure == False:
    if result['from'] != account:
        response = ''.join(('{ "error" : "Error: That transaction was from: ', result['from'], ', not you." }'))
        failure = True
if failure == False:
    txValue = Web3.fromWei(result['value'], 'ether')
    if txValue > 0 and result['to'] != PAYMENT_ADDRESS:
        response = ''.join(('{ "error" : "Error: That transaction went to: ', result['to'], ', not the payment address." }'))
        failure = True
if failure == False:
    try:
        receipt = w3.eth.get_transaction_receipt(txHash)
    except Exception as err:
        response = ''.join(('{ "error" : "Error: Unable to get transaction details: ', str(err), '." }'))
        failure = True
    if failure == False and receipt['status'] != 1:
        response = ''.join(('{ "error" : "Error: That transaction failed, please try your payment again." }'))
        failure = True

# Tx content Validation
if failure == False:
    if txValue > 0:
        txToken = contracts.GAS_TOKENS[network]
        tokenAmount = txValue
    else:
        # also check for any random token trasfers in the wallet
        results = events.extractTokenResults(w3, txHash, account, int(datetime.now(timezone.utc).timestamp()), receipt, '', '', network)
        for xfer in results:
            if xfer.address == PAYMENT_ADDRESS:
                txToken = xfer.coinType
                tokenAmount = xfer.coinAmount
    if txToken not in PAYMENT_TOKENS[network] or not tokenAmount > 0:
        response = ''.join(('{ "error" : "Error: No valid token transfers were found in that transaction." }'))
        failure = True

print('Content-type: text/json\n')
if failure == False:
    purchaseTime = getSubscriptionTime(txToken, tokenAmount)
    if purchaseTime > 0:
        updateResult = addPayment(account, txHash, txToken, tokenAmount, network, purchaseTime)
        if updateResult == 0:
            response = ''.join(('{ "error": "', 'Payment not posted, please contact site admin to ensure credit.', '" }'))
        elif updateResult == -1:
            response = ''.join(('{ "error": "', 'Error: that transaction has already been verified, it cannot be used again.', '" }'))
        else:
            response = ''.join(('{ "updated": "', str(updateResult), ' Payment posted" }'))
    else:
        response = ''.join(('{ "error": "', 'The value of that transaction is below the minimum amount to add subscription time.', '" }'))

print(response)
