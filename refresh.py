#!/usr/bin/env python3
import nets
import db
from web3 import Web3
import prices
import json
import logging
import logging.handlers
import jsonpickle
import contracts

def main():
    handler = logging.handlers.RotatingFileHandler('refresh.log', maxBytes=33554432, backupCount=10)
    logging.basicConfig(handlers=[handler], level=logging.INFO, format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logging.info('Starting refresh process')
    priceNetwork()

def populateFees():
    # Connect to right network that txs are for
    w3 = Web3(Web3.HTTPProvider(nets.hmy_web3))
    if not w3.isConnected():
        logging.error('Error: Critical w3 connection failure')
        return 'Error: Blockchain connection failure.'

    con = db.aConn()
    cur = con.cursor()
    cur.execute("SELECT DISTINCT account FROM transactions")
    row = cur.fetchone()
    while row != None:
        logging.info('Starting refresh of account {0}'.format(row[0]))
        refreshAccount(w3, con, row[0])
        row = cur.fetchone()
    con.close()

# Iterate through all transactions for account and run refresh actions
def refreshAccount(w3, con, account):
    cur = con.cursor()
    cur.execute("SELECT * FROM transactions WHERE account=%s", (account))
    row = cur.fetchone()
    while row != None:
        if row[7] == None and account not in contracts.address_map:
            addFee(w3, con, row[0], row[2], row[3], account)
        row = cur.fetchone()

# Update the gas transaction fee amount and value assuming tx is on Harmony
def addFee(w3, con, tx, eventType, events, account):
    pd = prices.PriceData()
    # don't want to add gas to payment service tx or tavern sales/hires because gas is paid by other account
    if  (eventType != 'airdrops' or '0x6Ca68D6Df270a047b12Ba8405ec688B5dF42D50C' not in events) and (eventType != 'tavern' or ('sale' not in events and 'hire' not in events)):
        try:
            # sometimes they just don't exist yet
            result = w3.eth.get_transaction(tx)
            receipt = w3.eth.get_transaction_receipt(tx)
        except Exception as err:
            logging.error('Got failed to get transaction {0} {1}'.format(tx, str(err)))
            return 'Error: Failed to get tx'
        block = result['blockNumber']
        timestamp = w3.eth.get_block(block)['timestamp']
        txFee = Web3.fromWei(result['gasPrice'], 'ether') * receipt['gasUsed']
        feeValue = pd.priceLookup(timestamp, '0xcF664087a5bB0237a0BAd6742852ec6c8d69A27a') * txFee
        logging.info('updating gas data {0}: - {1}/{2}'.format(tx, txFee, feeValue))
        # Update each event object inside
        if events != None and events != '':
            results = jsonpickle.decode(events)
            if type(results) is list and len(results) > 0:
                results[0].fiatFeeValue = feeValue
            elif type(results) is not list:
                results.fiatFeeValue = feeValue
            events = jsonpickle.encode(results)

        cur = con.cursor()
        cur.execute("UPDATE transactions SET events=%s, network='harmony', fee=%s, feeValue=%s WHERE txHash=%s AND account=%s", (events, txFee, feeValue, tx, account))
        con.commit()
    else:
        logging.info('skipping tx {0}, does not meet update criteria'.format(tx))

def priceNetwork():
    for k, v in contracts.HARMONY_TOKENS.items():
        logging.info('Clean {0} {1} prices'.format('harmony', v))
        cleanPrices(k, v, 'harmony')
    for k, v in contracts.DFKCHAIN_TOKENS.items():
        logging.info('Clean {0} {1} prices'.format('dfkchain', v))
        cleanPrices(k, v, 'dfkchain')
    for k, v in contracts.KLAYTN_TOKENS.items():
        logging.info('Clean {0} {1} prices'.format('klaytn', v))
        cleanPrices(k, v, 'klaytn')

def cleanPrices(token, tokenName, network):
    # temp set price networks
    currentDate = ''
    goodPriceFound = False
    goodPriceData = []
    priceRemovals = []
    con = db.aConn()
    with con.cursor() as cur:
        cur.execute("SELECT token, date, prices FROM prices WHERE token=%s ORDER BY date", (token,))
        row = cur.fetchone()
        while row != None:
            if row[1] != currentDate:
                with con.cursor() as cur2:
                    for item in priceRemovals:
                        logging.info('delete {0}'.format(str(item)))
                        cur2.execute("DELETE FROM prices WHERE date=%s AND token=%s AND prices=%s", (item[0], item[1], item[2]))

                currentDate = row[1]
                goodPriceFound = False
                priceRemovals = []

            priceData = json.loads(row[2])
            if (goodPriceFound == True and [row[1], row[0], row[2]] != goodPriceData) or priceData['usd'] < 0.000001 or priceData['usd'] > 1000:
                logging.info('tag for removal {0} - {1} - {2}'.format(row[1], tokenName, priceData['usd']))
                priceRemovals.append([row[1], row[0], row[2]])
            else:
                logging.info('keep good price {0} - {1} - {2}'.format(row[1], tokenName, priceData['usd']))
                goodPriceData = [row[1], row[0], row[2]]
                goodPriceFound = True
            row = cur.fetchone()
    with con.cursor() as cur2:
        for item in priceRemovals:
            logging.info('delete {0}'.format(str(item)))
            cur2.execute("DELETE FROM prices WHERE date=%s AND token=%s AND prices=%s", (item[0], item[1], item[2]))
    con.close()

if __name__ == "__main__":
	main()
