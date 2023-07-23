#!/usr/bin/env python3
from web3 import Web3
import nets
import requests
import logging


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
        if includedChains & nets.HARMONY > 0:
            w3 = Web3(Web3.HTTPProvider(nets.hmy_web3))
            if not w3.is_connected():
                logging.error('Error: Critical w3 connection failure for harmony')
                result = 'Error: Blockchain connection failure.'
            else:
                hmy_result += w3.eth.get_transaction_count(address)

        if includedChains & nets.DFKCHAIN > 0:
            w3 = Web3(Web3.HTTPProvider(nets.dfk_web3))
            if not w3.is_connected():
                logging.error('Error: Critical w3 connection failure for dfk chain')
                result = 'Error: Blockchain connection failure.'
            else:
                dfk_result += w3.eth.get_transaction_count(address)

        if includedChains & nets.KLAYTN > 0:
            w3 = Web3(Web3.HTTPProvider(nets.klaytn_web3))
            if not w3.is_connected():
                logging.error('Error: Critical w3 connection failure for Klaytn')
                result = 'Error: Blockchain connection failure.'
            else:
                ktn_result += w3.eth.get_transaction_count(address)

        if includedChains & nets.AVALANCHE > 0:
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
