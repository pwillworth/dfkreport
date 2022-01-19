#!/usr/bin/env python3

from pyhmy import account, transaction
import nets
import db
import requests
import time
import logging
import settings

# Return array of transactions on Harmony for the address
def getHarmonyData(address, startDate="", endDate="", page_size=settings.TX_PAGE_SIZE):
    tx_end = False
    offset = 0
    txs = []
    while tx_end == False:
        try:
            results = account.get_transaction_history(address, page=offset, page_size=page_size, include_full_tx=False, endpoint=nets.hmy_main)
        except ConnectionError as err:
            logging.error("connection to harmony api failed - ".format(str(err)))
            break
        except Exception as err:
            logging.error("harmony connection failure getting records, waiting and trying again.  {0}".format(str(err)))
            time.sleep(1)
            continue

        logging.info("got {0} transactions".format(len(results)))
        if len(results) > 0:
            offset = offset + 1
            txs = txs + results
        else:
            tx_end = True
        
        if startDate != "" and endDate != "":
            db.updateReport(address, startDate, endDate, 'fetched', len(txs))

    tx_end = False
    offset = 0
    while tx_end == False:
        try:
            results = account.get_staking_transaction_history(address, page=offset, page_size=page_size, include_full_tx=False, endpoint=nets.hmy_main)
        except Exception as err:
            logging.error("harmony connection failure getting records, waiting and trying again.  {0}".format(str(err)))
            time.sleep(1)
            continue

        logging.info("got {0} staking transactions".format(len(results)))
        if len(results) > 0:
            offset = offset + 1
            txs = txs + results
        else:
            tx_end = True

    if startDate != "" and endDate != "":
        db.updateReport(address, startDate, endDate, 'fetched', len(txs))

    return txs

# Return array of transactions on Avalanche for the address
def getAvalancheData(address, startDate="", endDate="", page_size=settings.TX_PAGE_SIZE, alreadyFetched=0):
    tx_end = False
    offset = 0
    txs = []
    while tx_end == False:
        try:
            r = requests.get("{3}/api?module=account&action=txlist&address={0}&page={2}&offset={1}&sort=asc&apikey={4}".format(address, offset, page_size, nets.avax_main, nets.avax_key))
        except ConnectionError:
            logging.error("connection to AVAX api failed")
            break
        if r.status_code == 200:
            results = r.json()
            logging.info("got {0} transactions".format(len(results['result'])))
            if len(results['result']) > 0:
                offset = offset + 1
                txs = txs + results['result']
            else:
                tx_end = True
        else:
            logging.error(r.text)
            break

        if startDate != "" and endDate != "":
            db.updateReport(address, startDate, endDate, 'fetched', alreadyFetched + len(txs))

    return txs

def getTransactionList(address, startDate, endDate, page_size):
    hmy_txs = []
    avx_txs = []
    logging.info('Get Harmony data for {0}'.format(address))
    hmy_txs += getHarmonyData(address, startDate, endDate, page_size)
    logging.info('Get Avalanche data for {0}'.format(address))
    avx_txs += getAvalancheData(address, startDate, endDate, page_size, len(hmy_txs))
    return [hmy_txs, avx_txs]

def getTransactionCount(address):
    result = ""
    hmy_result = 0
    avx_result = 0

    try:
        hmy_result = account.get_transactions_count(address, 'ALL', endpoint=nets.hmy_main)
    except ConnectionError:
        result = 'Error: Failed to connect to Harmony API'
        logging.error("connection to harmony api failed")

    try:
        r = requests.get("{1}/api?module=proxy&action=eth_getTransactionCount&address={0}&tag=latest&apikey={2}".format(address, nets.avax_main, nets.avax_key))
    except ConnectionError:
        logging.error("connection to AVAX api failed")

    if r.status_code == 200:
        results = r.json()
        try:
            avx_result = int(results['result'], base=16)
            logging.info("got {0} transactions".format(avx_result))
        except Exception as err:
            result = 'Error: invalid response from Avalanche Snowtrace API - {0}'.format(str(err))
            logging.error(result)
    else:
        result = 'Error: Failed to connect to Avalanche Snowtrace API'
        logging.error(result)

    if result != "":
        return result
    else:
        return hmy_result + avx_result

if __name__ == "__main__":
    logging.basicConfig(filename='transactions.log', level=logging.INFO)
    result = getTransactionCount('0x13a65B9F8039E2c032Bc022171Dc05B30c3f2892')
    print(type(result))
