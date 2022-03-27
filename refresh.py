#!/usr/bin/env python3
import nets
import db
from web3 import Web3
import prices
import logging
import logging.handlers
import jsonpickle

def main():
    handler = logging.handlers.RotatingFileHandler('../refresh.log', maxBytes=33554432, backupCount=10)
    logging.basicConfig(handlers=[handler], level=logging.INFO, format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logging.info('Starting refresh process')
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
        if row[7] == None:
            addFee(w3, con, row[0], row[2], row[3], account)
        row = cur.fetchone()

# Update the gas transaction fee amount and value assuming tx is on Harmony
def addFee(w3, con, tx, eventType, events, account):
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
        feeValue = prices.priceLookup(timestamp, '0xcF664087a5bB0237a0BAd6742852ec6c8d69A27a') * txFee
        logging.info('updating gas data {0}: - {1}/{2}'.format(tx, txFee, feeValue))
        # Update each event object inside
        if events != None and events != '':
            results = jsonpickle.decode(events)
            if type(results) is list:
                results[0].fiatFeeValue = feeValue
            else:
                results.fiatFeeValue = feeValue
            events = jsonpickle.encode(results)

        cur = con.cursor()
        cur.execute("UPDATE transactions SET events=%s, network='harmony', fee=%s, feeValue=%s WHERE txHash=%s AND account=%s", (events, txFee, feeValue, tx, account))
        con.commit()
    else:
        logging.info('skipping tx {0}, does not meet update criteria'.format(tx))


if __name__ == "__main__":
	main()
