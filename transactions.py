#!/usr/bin/env python3
from web3 import Web3
from pyhmy import account
import nets
import db
import dfkInfo
import requests
import datetime
from datetime import timezone
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
            raise Exception('Harmony Transactions Lookup Failure.')
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
def getCovalentTxList(chainID, address, startDate="", endDate="", alreadyFetched=0, page_size=settings.TX_PAGE_SIZE):
    tx_end = False
    startKey = 0
    blockLimit = None
    blockSpan = 86400
    retryCount = 0
    txs = []
    if chainID == '8217':
        lowerBound = db.getLastTransactionTimestamp(address, 'klaytn')
    else:
        lowerBound = db.getLastTransactionTimestamp(address, 'dfkchain')
    upperBound = datetime.datetime.utcnow().timestamp()+86400
    if lowerBound > 0:
        blockLimit = lowerBound

    while tx_end == False or (blockLimit != None and blockLimit < upperBound):
        if blockLimit == None:
            rURL = "{2}/{0}/address/{1}/transactions_v2/?block-signed-at-asc=true&no-logs=true&block-signed-at-limit=0&block-signed-at-span=86400&page-size=1".format(chainID, address, nets.covalent)
        else:
            rURL = "{2}/{0}/address/{1}/transactions_v2/?block-signed-at-asc=true&no-logs=true&block-signed-at-limit={5}&block-signed-at-span={6}&page-size={3}&page-number={4}".format(chainID, address, nets.covalent, page_size, startKey, blockLimit, blockSpan)

        try:
            r = requests.get(rURL, auth=(dfkInfo.COV_KEY,''))
        except ConnectionError:
            logging.error("connection to Covalent api failed")
            raise Exception('DFK Chain Transactions Lookup Failure.')
        if r.status_code == 200:
            retryCount = 0
            results = r.json()
            if blockLimit == None:
                # blockLimit not set means we are looking up the first transaction for this account to start
                if 'items' in results['data'] and type(results['data']['items']) is list and len(results['data']['items']) > 0:
                    blockDate = datetime.datetime.strptime(results['data']['items'][0]['block_signed_at'], '%Y-%m-%dT%H:%M:%SZ')
                    blockDate = blockDate.replace(tzinfo=timezone.utc)
                    blockLimit = int(blockDate.timestamp())
                else:
                    logging.info('No first tx for account found.')
                    break
            else:
                # processing 1 day of transactions from blockLimit timestamp
                if 'pagination' in results['data'] and results['data']['pagination']['has_more'] == True:
                    startKey = results['data']['pagination']['page_number']+1
                else:
                    startKey = 0
                    tx_end = True
                    blockLimit += blockSpan

                if 'items' in results['data'] and type(results['data']['items']) is list and len(results['data']['items']) > 0:
                    logging.info("got {0} transactions".format(len(results['data']['items'])))
                    txs = txs + results['data']['items']
                else:
                    tx_end = True
        elif r.status_code == 429:
            # rate limiting
            logging.error('Exceeded rate limit for Covalent API')
            raise Exception('Covalent Transactions Lookup Failure.')
        elif r.status_code == 504:
            # covalent gateway timeout
            logging.warning("Covalent gateway timeout getting Txs, retrying")
            if retryCount < 3:
                retryCount += 1
                time.sleep(13)
                continue
            else:
                logging.error("Covalent timeout too many times, exit")
                raise Exception('Covalent Transactions Lookup Failure.')
        else:
            logging.error('{0}: {1}'.format(r.status_code, r.text))
            raise Exception('Covalent Transactions Lookup Failure.')

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
            raise Exception('Avalanche Transactions Lookup Failure.')
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
            raise Exception('Avalanche Transactions Lookup Failure.')

        if startDate != "" and endDate != "":
            db.updateReport(address, startDate, endDate, 'fetched', alreadyFetched + len(txs))

    return txs

def getTransactionList(address, startDate, endDate, page_size, includedChains=constants.DFKCHAIN):
    hmy_txs = []
    dfk_txs = []
    ktn_txs = []
    avx_txs = []
    if includedChains & constants.HARMONY > 0:
        logging.info('Get Harmony data for {0}'.format(address))
        hmy_txs = getHarmonyData(address, startDate, endDate, page_size)
        # Sometimes the paged return tx lookup can result in duplicate txs in the list
        hmy_txs = list(dict.fromkeys(hmy_txs))
    if includedChains & constants.DFKCHAIN > 0:
        logging.info('Get DFK Chain data for {0}'.format(address))
        dfk_txs = getCovalentTxList('53935', address, startDate, endDate, len(hmy_txs))
    if includedChains & constants.KLAYTN > 0:
        logging.info('Get Klaytn data for {0}'.format(address))
        ktn_txs = getCovalentTxList('8217', address, startDate, endDate, len(hmy_txs)+len(dfk_txs))
    if includedChains & constants.AVALANCHE > 0:
        logging.info('Get Avalanche data for {0}'.format(address))
        avx_txs += getAvalancheData(address, startDate, endDate, page_size, len(hmy_txs)+len(dfk_txs)+len(ktn_txs))
    return [hmy_txs, avx_txs, dfk_txs, ktn_txs]

def getTransactionCount(address, includedChains=constants.DFKCHAIN):
    result = ""
    hmy_result = 0
    avx_result = 0
    dfk_result = 0
    ktn_result = 0

    if includedChains & constants.HARMONY > 0:
        try:
            hmy_result = account.get_transactions_count(address, 'ALL', endpoint=nets.hmy_main)
        except ConnectionError:
            result = 'Error: Failed to connect to Harmony API'
            logging.error("connection to harmony api failed")

    if includedChains & constants.DFKCHAIN > 0:
        w3 = Web3(Web3.HTTPProvider(nets.dfk_web3))
        if not w3.isConnected():
            logging.error('Error: Critical w3 connection failure for dfk chain')
            result = 'Error: Blockchain connection failure.'
        else:
            dfk_result = w3.eth.get_transaction_count(address)

    if includedChains & constants.KLAYTN > 0:
        w3 = Web3(Web3.HTTPProvider(nets.klaytn_web3))
        if not w3.isConnected():
            logging.error('Error: Critical w3 connection failure for Klaytn')
            result = 'Error: Blockchain connection failure.'
        else:
            ktn_result = w3.eth.get_transaction_count(address)

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

    if result != "":
        return result
    elif hmy_result + avx_result + dfk_result + ktn_result == 0:
        return 'Error: No transactions found for that wallet'
    else:
        return [hmy_result, avx_result, dfk_result, ktn_result]

if __name__ == "__main__":
    logging.basicConfig(filename='transactions.log', level=logging.INFO)
    result = getTransactionCount('0xeAaAcc98c0d582b6167054fb6017d09cA77bcfc5', 4)
    print(str(result))
