#!/usr/bin/env python3
from web3 import Web3
from web3.middleware import geth_poa_middleware
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

# Return array of transactions on Harmony for the address
def getHarmonyData(address, network, page_size=settings.TX_PAGE_SIZE):
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

        logging.info("got {0} transactions for {1}".format(len(results), address))
        if len(results) > 0:
            offset = offset + 1
            txs = txs + results
        else:
            tx_end = True

        db.updateWalletStatus(address, network, 'fetched', len(txs))

    return txs

# Return array of transactions on DFK Chain for the address
def getCovalentTxList(chainID, address, network, page_size=settings.TX_PAGE_SIZE):
    tx_end = False
    startKey = 0
    retryCount = 0
    txs = []

    while tx_end == False:
        rURL = "{2}/{0}/address/{1}/transactions_v2/?block-signed-at-asc=true&no-logs=true&page-size={3}&page-number={4}".format(chainID, address, nets.covalent, page_size, startKey)

        try:
            r = requests.get(rURL, auth=(dfkInfo.COV_KEY,''))
        except ConnectionError:
            logging.error("connection to Covalent api failed")
            raise Exception('DFK Chain Transactions Lookup Failure.')
        logging.info(rURL)
        if r.status_code == 200:
            retryCount = 0
            results = r.json()

            if 'pagination' in results['data'] and results['data']['pagination']['has_more'] == True:
                startKey = results['data']['pagination']['page_number']+1
            else:
                startKey = 0
                tx_end = True

            if 'items' in results['data'] and type(results['data']['items']) is list and len(results['data']['items']) > 0:
                logging.info("got {0} transactions".format(len(results['data']['items'])))
                txs = txs + results['data']['items']
            else:
                tx_end = True
        elif r.status_code == 429:
            # rate limiting
            # covalent gateway timeout
            logging.warning("Covalent rate limit hit, wait and retrying")
            if retryCount < 3:
                retryCount += 1
                time.sleep(2)
                continue
            else:
                logging.error("Covalent rate limit hit too many times, exit")
                raise Exception('Covalent Transactions Lookup Failure.')
        elif r.status_code in [504,524]:
            # covalent gateway timeout
            logging.warning("Covalent gateway timeout getting Txs, retrying")
            if retryCount < 3:
                retryCount += 1
                time.sleep(8)
                continue
            else:
                logging.error("Covalent timeout too many times, exit")
                raise Exception('Covalent Transactions Lookup Failure.')
        else:
            logging.error('{0}: {1}'.format(r.status_code, r.text))
            raise Exception('Covalent Transactions Lookup Failure.')

        db.updateWalletStatus(address, network, 'fetched', len(txs))

    return txs

# Return array of transactions on DFK Chain for the address
def getBitqueryTxList(network, address, page_size=settings.TX_PAGE_SIZE):
    tx_end = False
    startKey = 0
    retryCount = 0
    txs = []
    lowerBound = db.getLastTransactionTimestamp(address, network)
    sinceDateTime = datetime.datetime.fromtimestamp(lowerBound)
    sinceDateTime.replace(tzinfo=timezone.utc)
    sinceDateTimeStr = sinceDateTime.strftime('%Y-%m-%dT%H:%M:%SZ')

    while tx_end == False:
        query = """query MyQuery {
                ethereum(network: %s) {
                    transactions(
                        txSender: {is: "%s"}
                        options: {limit: %s, offset: %s}
                        time: {since: "%s"}
                    ) {
                    hash
                    block {
                        timestamp {
                        unixtime
                        }
                    }
                    }
                }
                }
        """
        data = query % (network, address, page_size, startKey, sinceDateTimeStr)

        try:
            r = requests.post(nets.bitquery, headers={'X-API-KEY': dfkInfo.BTQ_KEY}, json={'query': data})
        except ConnectionError:
            logging.error("connection to Bitquery api failed")
            raise Exception('{0} Transactions Lookup Failure.'.format(network))
        if r.status_code == 200:
            retryCount = 0
            results = r.json()

            if 'ethereum' in results['data'] and 'transactions' in results['data']['ethereum'] and type(results['data']['ethereum']['transactions']) is list and len(results['data']['ethereum']['transactions']) > 0:
                firstTime = results['data']['ethereum']['transactions'][0]['block']['timestamp']['unixtime']
                lastTime = results['data']['ethereum']['transactions'][len(results['data']['ethereum']['transactions'])-1]['block']['timestamp']['unixtime']
                logging.info("got {0} transactions {1} through {2}".format(len(results['data']['ethereum']['transactions']), firstTime, lastTime))
                txs = txs + results['data']['ethereum']['transactions']
                startKey += page_size
            else:
                tx_end = True
        elif r.status_code == 429:
            # rate limiting
            logging.warning("Bitquery rate limit hit, wait and retrying")
            if retryCount < 3:
                retryCount += 1
                time.sleep(2)
                continue
            else:
                logging.error("Bitquery rate limit hit too many times, exit")
                raise Exception('Bitquery Transactions Lookup Failure.')
        elif r.status_code in [504,524]:
            # provider gateway timeout
            logging.warning("Bitquery gateway timeout getting Txs, retrying")
            if retryCount < 3:
                retryCount += 1
                time.sleep(8)
                continue
            else:
                logging.error("Bitquery timeout too many times, exit")
                raise Exception('Bitquery Transactions Lookup Failure.')
        else:
            logging.error('{0}: {1}'.format(r.status_code, r.text))
            raise Exception('Bitquery Transactions Lookup Failure.')

        db.updateWalletStatus(address, network, 'fetched', len(txs))

    return txs

# Return array of transactions on Avalanche for the address
def getAvalancheData(address, network, page_size=settings.TX_PAGE_SIZE):
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

        db.updateWalletStatus(address, network, 'fetched', len(txs))

    return txs

# Return array of transactions on DFK Chain for the address
def getGlacierTxList(chainID, address, network, page_size=settings.TX_PAGE_SIZE):
    tx_end = False
    # override with glacier max
    page_size = 100
    nextPageToken = ''
    retryCount = 0
    txs = []
    blockFilter = ""
    lowerBound = db.getLastTransactionTimestamp(address, network)
    if network == 'dfkchain' and lowerBound > 1648710000:
        w3 = Web3(Web3.HTTPProvider(nets.dfk_web3))
        # middleware used to allow for interpreting longer data length for get_block on dfkchain
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        if not w3.is_connected():
            logging.error('Error: Critical w3 connection failure for dfk chain')
        else:
            latestBlock = w3.eth.get_block('finalized')
            latestBlockTimestamp = latestBlock.timestamp
            # estimate block at timestamp based on assumption that each block is about 2s
            # this will give a buffer of overlap since blocks usually take slightly over 2s on DFKChain
            estimatedBlock = latestBlock.number - int((latestBlockTimestamp - lowerBound) / 2)
            logging.info("estimatedBlock = {0} - int(({1} - {2}) / 2)".format(latestBlock.number, latestBlockTimestamp, lowerBound))
            blockFilter = "&startBlock={0}".format(estimatedBlock)

    while tx_end == False:
        if nextPageToken != '':
            rURL = "{2}/chains/{0}/addresses/{1}/transactions?pageSize={3}{4}&pageToken={5}".format(chainID, address, nets.glacier, page_size, blockFilter, nextPageToken)
        else:
            rURL = "{2}/chains/{0}/addresses/{1}/transactions?pageSize={3}{4}".format(chainID, address, nets.glacier, page_size, blockFilter)
        logging.info(rURL)

        try:
            r = requests.get(rURL, auth=(dfkInfo.COV_KEY,''))
        except ConnectionError:
            logging.error("connection to Covalent api failed")
            raise Exception('DFK Chain Transactions Lookup Failure.')
        logging.info(rURL)
        if r.status_code == 200:
            retryCount = 0
            results = r.json()

            if 'nextPageToken' in results:
                nextPageToken = results['nextPageToken']
                logging.info('next page token {0}'.format(nextPageToken))
                if nextPageToken == '':
                    tx_end = True
            else:
                tx_end = True

            if 'transactions' in results and type(results['transactions']) is list and len(results['transactions']) > 0:
                logging.info("got {0} transactions".format(len(results['transactions'])))
                txs = txs + results['transactions']
            else:
                tx_end = True

        elif r.status_code == 429:
            # rate limiting
            logging.warning("glacier rate limit hit, wait and retrying")
            if retryCount < 3:
                retryCount += 1
                time.sleep(2)
                continue
            else:
                logging.error("glacier rate limit hit too many times, exit")
                raise Exception('glacier Transactions Lookup Failure.')
        elif r.status_code in [504,524]:
            # glacier gateway timeout
            logging.warning("glacier gateway timeout getting Txs, retrying")
            if retryCount < 3:
                retryCount += 1
                time.sleep(8)
                continue
            else:
                logging.error("glacier timeout too many times, exit")
                raise Exception('Glacier Transactions Lookup Failure.')
        else:
            logging.error('{0}: {1}'.format(r.status_code, r.text))
            raise Exception('Glacier Transactions Lookup Failure.')

        db.updateWalletStatus(address, network, 'fetched', len(txs))

    return txs

def getTransactionList(wallet, network, page_size):
    result = []
    if network == 'harmony':
        logging.info('Get Harmony data for {0}'.format(wallet))
        hmy_txs = getHarmonyData(wallet, network, page_size)
        # Sometimes the paged return tx lookup can result in duplicate txs in the list
        result = list(dict.fromkeys(hmy_txs))
    elif network == 'dfkchain':
        logging.info('Get DFK Chain data for {0}'.format(wallet))
        result = getGlacierTxList('53935', wallet, network, page_size)
    elif network == 'klaytn':
        logging.info('Get Klaytn data for {0}'.format(wallet))
        result = getBitqueryTxList('klaytn', wallet, page_size)
    elif network == 'avalanche':
        logging.info('Get Avalanche data for {0}'.format(wallet))
        result += getAvalancheData(wallet, network, page_size)
    else:
        result = []

    return result

def getTransactionCount(address, network):
    result = 0

    if network == 'harmony':
        w3 = Web3(Web3.HTTPProvider(nets.hmy_web3))
        if not w3.is_connected():
            logging.error('Error: Critical w3 connection failure for harmony')
            result = 'Error: Blockchain connection failure.'
        else:
            result += w3.eth.get_transaction_count(address)
    elif network == 'dfkchain':
        w3 = Web3(Web3.HTTPProvider(nets.dfk_web3))
        if not w3.is_connected():
            logging.error('Error: Critical w3 connection failure for dfk chain')
            result = 'Error: Blockchain connection failure.'
        else:
            result += w3.eth.get_transaction_count(address)
    elif network == 'klaytn':
        w3 = Web3(Web3.HTTPProvider(nets.klaytn_web3))
        if not w3.is_connected():
            logging.error('Error: Critical w3 connection failure for Klaytn')
            result = 'Error: Blockchain connection failure.'
        else:
            result += w3.eth.get_transaction_count(address)
    elif network == 'avalanche':
        try:
            r = requests.get("{1}/api?module=proxy&action=eth_getTransactionCount&address={0}&tag=latest&apikey={2}".format(address, nets.avax_main, nets.avax_key))
        except ConnectionError:
            logging.error("connection to AVAX api failed")

        if r.status_code == 200:
            results = r.json()
            try:
                result += int(results['result'], base=16)
                logging.info("got {0} transactions".format(result))
            except Exception as err:
                result = 'Error: invalid response from Avalanche Snowtrace API - {0}'.format(str(err))
                logging.error(result)
        else:
            result = 'Error: Failed to connect to Avalanche Snowtrace API'
            logging.error(result)
    else:
        result = 'Error: invalid network {0}, try harmony,dfkchain,klaytn,avalanche'.format(network)

    return result


if __name__ == "__main__":
    logging.basicConfig(filename='transactions.log', level=logging.INFO)
    #result = getTransactionCount('0xeAaAcc98c0d582b6167054fb6017d09cA77bcfc5', 4)
    result = getGlacierTxList('53935', '0x0FD279b463ff6fAf896Ca753adb5ad2232Ee9AAF', '0x0FD279b463ff6fAf896Ca753adb5ad2232Ee9AAF', '2023-08-01', '2023-08-05', '')
    #result = getCovalentTxList('53935', '0x0FD279b463ff6fAf896Ca753adb5ad2232Ee9AAF', '0x0FD279b463ff6fAf896Ca753adb5ad2232Ee9AAF', '2022-01-01', '2022-02-01', '')
    print(str(result))
