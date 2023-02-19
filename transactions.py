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
def getHarmonyData(acct, address, startDate, endDate, walletHash, alreadyFetched=0, page_size=settings.TX_PAGE_SIZE):
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

        db.updateReport(acct, startDate, endDate, walletHash, 'fetched', alreadyFetched + len(txs))

    return txs

# Return array of transactions on DFK Chain for the address
def getCovalentTxList(chainID, account, address, startDate, endDate, walletHash, alreadyFetched=0, page_size=settings.TX_PAGE_SIZE):
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
    if lowerBound > 1648710000:
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
            blockSpan = 86400
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
                # reduce range a bit to see if that helps
                blockSpan = int(blockSpan*0.95)
                continue
            else:
                logging.error("Covalent timeout too many times, exit")
                raise Exception('Covalent Transactions Lookup Failure.')
        else:
            logging.error('{0}: {1}'.format(r.status_code, r.text))
            raise Exception('Covalent Transactions Lookup Failure.')

        db.updateReport(account, startDate, endDate, walletHash, 'fetched', alreadyFetched + len(txs))

    return txs

# Return array of transactions on DFK Chain for the address
def getBitqueryTxList(network, account, address, startDate, endDate, walletHash, alreadyFetched=0, page_size=settings.TX_PAGE_SIZE):
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

        db.updateReport(account, startDate, endDate, walletHash, 'fetched', alreadyFetched + len(txs))

    return txs

# Return array of transactions on Avalanche for the address
def getAvalancheData(account, address, startDate, endDate, walletHash, page_size=settings.TX_PAGE_SIZE, alreadyFetched=0):
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

        db.updateReport(account, startDate, endDate, walletHash, 'fetched', alreadyFetched + len(txs))

    return txs

def getTransactionList(account, wallets, startDate, endDate, txCounts, page_size, includedChains):
    result = {}
    totalTx = 0
    walletHash = db.getWalletHash(wallets)
    for wallet in wallets:
        hmy_txs = []
        dfk_txs = []
        ktn_txs = []
        avx_txs = []
        if includedChains & constants.HARMONY > 0:
            logging.info('Get Harmony data for {0}'.format(wallet))
            hmy_txs = getHarmonyData(account, wallet, startDate, endDate, walletHash, totalTx, page_size)
            # Sometimes the paged return tx lookup can result in duplicate txs in the list
            hmy_txs = list(dict.fromkeys(hmy_txs))
            totalTx += txCounts[wallet][0]
        if includedChains & constants.DFKCHAIN > 0:
            logging.info('Get DFK Chain data for {0}'.format(wallet))
            dfk_txs = getCovalentTxList('53935', account, wallet, startDate, endDate, walletHash, totalTx)
            totalTx += txCounts[wallet][2]
        if includedChains & constants.KLAYTN > 0:
            logging.info('Get Klaytn data for {0}'.format(wallet))
            ktn_txs = getBitqueryTxList('klaytn', account, wallet, startDate, endDate, walletHash, totalTx)
            totalTx += txCounts[wallet][3]
        if includedChains & constants.AVALANCHE > 0:
            logging.info('Get Avalanche data for {0}'.format(wallet))
            avx_txs += getAvalancheData(account, wallet, startDate, endDate, walletHash, page_size, totalTx)
            totalTx += txCounts[wallet][1]
        result[wallet] = [hmy_txs, avx_txs, dfk_txs, ktn_txs]
    return result

def getTotalCount(counts):
    total = 0
    for k, v in counts.items():
        total = total + v[0] + v[1] + v[2] + v[3]
    return total

def getTransactionCount(wallets, includedChains):
    result = ""
    counts = {}

    for address in wallets:
        hmy_result = 0
        avx_result = 0
        dfk_result = 0
        ktn_result = 0
        if includedChains & constants.HARMONY > 0:
            try:
                hmy_result += account.get_transactions_count(address, 'ALL', endpoint=nets.hmy_main)
            except ConnectionError:
                result = 'Error: Failed to connect to Harmony API'
                logging.error("connection to harmony api failed")

        if includedChains & constants.DFKCHAIN > 0:
            w3 = Web3(Web3.HTTPProvider(nets.dfk_web3))
            if not w3.isConnected():
                logging.error('Error: Critical w3 connection failure for dfk chain')
                result = 'Error: Blockchain connection failure.'
            else:
                dfk_result += w3.eth.get_transaction_count(address)

        if includedChains & constants.KLAYTN > 0:
            w3 = Web3(Web3.HTTPProvider(nets.klaytn_web3))
            if not w3.isConnected():
                logging.error('Error: Critical w3 connection failure for Klaytn')
                result = 'Error: Blockchain connection failure.'
            else:
                ktn_result += w3.eth.get_transaction_count(address)

        if includedChains & constants.AVALANCHE > 0:
            try:
                r = requests.get("{1}/api?module=proxy&action=eth_getTransactionCount&address={0}&tag=latest&apikey={2}".format(address, nets.avax_main, nets.avax_key))
            except ConnectionError:
                logging.error("connection to AVAX api failed")

            if r.status_code == 200:
                results = r.json()
                try:
                    avx_result += int(results['result'], base=16)
                    logging.info("got {0} transactions".format(avx_result))
                except Exception as err:
                    result = 'Error: invalid response from Avalanche Snowtrace API - {0}'.format(str(err))
                    logging.error(result)
            else:
                result = 'Error: Failed to connect to Avalanche Snowtrace API'
                logging.error(result)
        counts[address] = [hmy_result, avx_result, dfk_result, ktn_result]

    if result != "":
        return result
    else:
        return counts

if __name__ == "__main__":
    logging.basicConfig(filename='transactions.log', level=logging.INFO)
    result = getTransactionCount('0xeAaAcc98c0d582b6167054fb6017d09cA77bcfc5', 4)
    print(str(result))
