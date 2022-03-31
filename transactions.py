#!/usr/bin/env python3

from pyhmy import account
import nets
import db
import requests
import time
import logging
import settings
import constants

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
            time.sleep(2)
            continue

        logging.info("got {0} transactions".format(len(results)))
        if len(results) > 0:
            offset = offset + 1
            txs = txs + results
        else:
            tx_end = True
        
        if startDate != "" and endDate != "":
            db.updateReport(address, startDate, endDate, 'fetched', len(txs))

    return txs

# Return array of transactions on DFK Chain for the address
def getDFKChainData(address, startDate="", endDate="", alreadyFetched=0):
    tx_end = False
    startKey = None
    txs = []

    while tx_end == False:
        if startKey == None:
            rURL = "{1}/transactions?address={0}&sort=asc".format(address, nets.dfk_main)
        else:
            rURL = "{1}/transactions?address={0}&startKey={2}&sort=asc".format(address, nets.dfk_main, startKey)
        try:
            r = requests.get(rURL)
        except ConnectionError:
            logging.error("connection to DFK Chain explorer api failed")
            break
        if r.status_code == 200:
            results = r.json()
            if 'nextPageStartKey' in results:
                startKey = results['nextPageStartKey']
            else:
                startKey = None
                tx_end = True
            if 'transactions' in results and type(results['transactions']) is list and len(results['transactions']) > 0:
                logging.info("got {0} transactions".format(len(results['transactions'])))
                txs = txs + results['transactions']
            else:
                tx_end = True
        else:
            logging.error(r.text)
            break

        if startDate != "" and endDate != "":
            db.updateReport(address, startDate, endDate, 'fetched', alreadyFetched + len(txs))

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
            if results['result'] != None and type(results['result']) is list and len(results['result']) > 0:
                logging.info("got {0} transactions".format(len(results['result'])))
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

def getTransactionList(address, startDate, endDate, page_size, includedChains=constants.HARMONY):
    hmy_txs = []
    dfk_txs = []
    avx_txs = []
    if includedChains & constants.HARMONY > 0:
        logging.info('Get Harmony data for {0}'.format(address))
        hmy_txs += getHarmonyData(address, startDate, endDate, page_size)
        # Sometimes the paged return tx lookup can result in duplicate txs in the list
        hmy_txs = list(dict.fromkeys(hmy_txs))
    if includedChains & constants.DFKCHAIN > 0:
        logging.info('Get DFK Chain data for {0}'.format(address))
        dfk_txs = getDFKChainData(address, startDate, endDate, len(hmy_txs))
    if includedChains & constants.AVALANCHE > 0:
        logging.info('Get Avalanche data for {0}'.format(address))
        avx_txs += getAvalancheData(address, startDate, endDate, page_size, len(hmy_txs)+len(dfk_txs))
    return [hmy_txs, avx_txs, dfk_txs]

def getTransactionCount(address, includedChains=constants.HARMONY):
    result = ""
    hmy_result = 0
    avx_result = 0
    dfk_result = 0

    if includedChains & constants.HARMONY > 0:
        try:
            hmy_result = account.get_transactions_count(address, 'ALL', endpoint=nets.hmy_main)
        except ConnectionError:
            result = 'Error: Failed to connect to Harmony API'
            logging.error("connection to harmony api failed")

    if includedChains & constants.DFKCHAIN > 0:
        initiated = False
        startKey = None
        txCount = 0

        while initiated == False or startKey != None:
            initiated = True
            if startKey == None:
                rURL = "{1}/transactions?address={0}&sort=asc".format(address, nets.dfk_main)
            else:
                rURL = "{1}/transactions?address={0}&startKey={2}&sort=asc".format(address, nets.dfk_main, startKey)
            try:
                r = requests.get(rURL)
            except ConnectionError:
                logging.error("connection to DFK Chain api failed")

            if r.status_code == 200:
                results = r.json()
                if 'nextPageStartKey' in results:
                    startKey = results['nextPageStartKey']
                else:
                    startKey = None
                try:
                    txCount = len(results['transactions'])
                    dfk_result += txCount
                    logging.info("got {0} transactions".format(dfk_result))
                except Exception as err:
                    result = 'Error: invalid response from DFK Chain Explorer API - {0}'.format(str(err))
                    logging.error(result)
            else:
                result = 'Error: Failed to connect to DFK Chain Explorer API'
                logging.error(result)

    if includedChains & constants.AVALANCHE > 0:
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

    if result != "" or hmy_result + avx_result + dfk_result == 0:
        return result
    else:
        return hmy_result + avx_result + dfk_result

if __name__ == "__main__":
    logging.basicConfig(filename='transactions.log', level=logging.INFO)
    result = getTransactionCount('0xeAaAcc98c0d582b6167054fb6017d09cA77bcfc5', 4)
    print(str(result))
