#!/usr/bin/env python3
"""

 Copyright 2023 Paul Willworth <ioscode@gmail.com>

"""

import time
from datetime import timezone, datetime
from web3 import Web3
from web3.logs import STRICT, IGNORE, DISCARD, WARN
import decimal
import db
import settings
import nets

#
PAYMENT_ADDRESS = '0x15Ca8d8d7048F694980C717369C55b53e4FbCAEe'
PAYMENT_TOKENS = {
    'dfkchain': ['0xCCb93dABD71c8Dad03Fc4CE5559dC3D89F67a260','0x04b9dA42306B023f3572e106B11D82aAd9D32EBb','0x3AD9DFE640E1A9Cc1D9B0948620820D975c3803a'],
    'klaytn': ['0x19Aac5f612f524B754CA7e7c41cbFa2E981A4432','0x30C103f8f5A3A732DFe2dCE1Cc9446f545527b43','0xB3F5867E277798b50ba7A71C0b24FDcA03045eDF']
}
TOKEN_SUB_VALUES = {
    '0x19Aac5f612f524B754CA7e7c41cbFa2E981A4432': 0.25, #klay
    '0xCCb93dABD71c8Dad03Fc4CE5559dC3D89F67a260': 0.50, #dfkJewel
    '0x30C103f8f5A3A732DFe2dCE1Cc9446f545527b43': 0.50, #klayJewel
    '0x04b9dA42306B023f3572e106B11D82aAd9D32EBb': 0.05, #crystal
    '0xB3F5867E277798b50ba7A71C0b24FDcA03045eDF': 0.05, #jabe
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

def extractTokenResults(w3, account, receipt, network):
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=settings.ERC20_ABI)
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    transfers = []
    for log in decoded_logs:
        if log['args']['from'] == account:
            otherAddress = log['args']['to']
        elif log['args']['to'] == account:
            otherAddress = log['args']['from']
        else:
            continue
        tokenValue = valueFromWei(log['args']['value'], log['address'], network)

        if tokenValue > 0:
            r = [otherAddress, log['address'], tokenValue]
            transfers.append(r)

    return transfers

# Simple way to determine conversion, maybe change to lookup on chain later
def valueFromWei(amount, token, network):
    #w3.fromWei doesn't seem to have an 8 decimal option for BTC
    if token in ['0x3095c7557bCb296ccc6e363DE01b760bA031F2d9', '0xdc54046c0451f9269FEe1840aeC808D36015697d','0x7516EB8B8Edfa420f540a162335eACF3ea05a247','0x16D0e1fBD024c600Ca0380A4C5D57Ee7a2eCBf9c']:
        return decimal.Decimal(amount) / decimal.Decimal(100000000)
    elif token in ['0x985458E523dB3d53125813eD68c274899e9DfAb4','0x3C2B8Be99c50593081EAA2A724F0B8285F5aba8f','0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664','0xceE8FAF64bB97a73bb51E115Aa89C17FfA8dD167','0x6270B58BE569a7c0b8f47594F191631Ae5b2C86C']: # 1USDC/1USDT
        weiConvert = 'mwei'
    else:
        weiConvert = 'ether'

    return Web3.from_wei(amount, weiConvert)

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

def validatePayment(network, account, txHash):
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
            txToken = settings.GAS_TOKENS[network]
            tokenAmount = txValue
        else:
            # also check for any random token trasfers in the wallet
            results = extractTokenResults(w3, txHash, account, int(datetime.now(timezone.utc).timestamp()), receipt, '', '', network)
            for xfer in results:
                if xfer.address == PAYMENT_ADDRESS:
                    txToken = xfer.coinType
                    tokenAmount = xfer.coinAmount
        if txToken not in PAYMENT_TOKENS[network] or not tokenAmount > 0:
            response = ''.join(('{ "error" : "Error: No valid token transfers were found in that transaction." }'))
            failure = True

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

    return response

def main():
    # Initialize database
    validatePayment()


if __name__ == "__main__":
	main()