#!/usr/bin/env python3

from pyhmy import account, transaction
import nets
import db
import requests
import sys
import logging

# Return array of transactions on Harmony for the address
def getHarmonyData(address, startDate="", endDate=""):
    tx_end = False
    offset = 0
    page_size = 80
    txs = []
    while tx_end == False:
        try:
            results = account.get_transaction_history(address, page=offset, page_size=page_size, include_full_tx=False, endpoint=nets.hmy_main)
        except ConnectionError:
            sys.stderr.write("connection to harmony api failed")
            break

        logging.info("got {0} transactions".format(len(results)))
        if len(results) > 0:
            offset = offset + 1
            txs = txs + results
        else:
            tx_end = True
        
        if startDate != "" and endDate != "":
            db.updateReport(address, startDate, endDate, 'fetched', len(txs))
            logging.info('updated report fetched {0}'.format(len(txs)))

    tx_end = False
    offset = 0
    page_size = 80
    while tx_end == False:
        try:
            results = account.get_staking_transaction_history(address, page=offset, page_size=page_size, include_full_tx=False, endpoint=nets.hmy_main)
        except ConnectionError:
            sys.stderr.write("connection to harmony api failed")
            break

        logging.info("got {0} staking transactions".format(len(results)))
        if len(results) > 0:
            offset = offset + 1
            txs = txs + results
        else:
            tx_end = True

    return txs

# Return array of transactions on Avalanche for the address
def getAvalancheData(address, startDate="", endDate=""):
    tx_end = False
    offset = 0
    page_size = 140
    txs = []
    while tx_end == False:
        try:
            r = requests.get("{3}api?module=account&action=txlist&address={0}&page={1}&offset={2}&sort=asc&apikey={4}".format(address, offset, page_size, nets.avax_main, nets.avax_key))
        except ConnectionError:
            sys.stderr.write("connection to AVAX api failed")
            break
        if r.status_code == 200:
            results = r.json()
            sys.stdout.write("got {0} transactions".format(len(results)))
            if len(results) > 0:
                offset = offset + page_size
                txs = txs + results
                for tx in results:
                    sys.stdout.write(tx['hash'])
            else:
                sys.stdout.write(r.text)
                tx_end = True
        else:
            sys.stdout.write(r.text)
            break
    return txs

def getTransactionList(address, startDate, endDate):
    txs = []
    logging.info('Get Harmony data for {0}'.format(address))
    txs = txs + getHarmonyData(address, startDate, endDate)
    #txs = txs + transactions.getAvalancheData(address, startDate, endDate)
    return txs

def getTransactionCount(address):
    try:
        result = account.get_transaction_count(address, endpoint=nets.hmy_main)
    except ConnectionError:
        result = 'Error: Failed to connect to Harmony API'
        sys.stderr.write("connection to harmony api failed")
    return result

if __name__ == "__main__":
    logging.basicConfig(filename='transactions.log', level=logging.INFO)
    result = getTransactionCount('0x0FD279b463ff6fAf896Ca753adb5ad2232Ee9AAF')
    print(type(result))
