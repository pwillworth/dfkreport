#!/usr/bin/env python3
import logging
import logging.handlers
import os
from web3 import Web3
from web3.logs import STRICT, IGNORE, DISCARD, WARN
from web3.middleware import geth_poa_middleware
import jsonpickle
import nets
import events
import db


def handleLogs(w3, event, network):
    tx = event['transactionHash'].hex()
    timestamp = w3.eth.get_block(event['blockNumber'])['timestamp']
    logging.info('handling event for tx {0} block {1}'.format(tx, event['blockNumber']))
    receipt = w3.eth.get_transaction_receipt(tx)
    # Heroes or Lands or Pets
    if event['address'] in ['0x13a65B9F8039E2c032Bc022171Dc05B30c3f2892', '0x77D991987ca85214f9686131C58c1ABE4C93E547', '0xc390fAA4C7f66E4D62E59C231D5beD32Ff77BEf0', '0x72F860bF73ffa3FC42B97BbcF43Ae80280CFcdc3']:
        if event['address'] == '0x77D991987ca85214f9686131C58c1ABE4C93E547':
            auctionType = 'land'
        elif event['address'] == '0x72F860bF73ffa3FC42B97BbcF43Ae80280CFcdc3':
            auctionType = 'pet'
        else:
            auctionType = 'hero'
        results = events.extractAuctionResults(w3, tx, None, timestamp, receipt, auctionType)
        if results != None and results[1] != None and db.findTransaction(tx, results[1].seller) == None:
            db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[1]), results[1].seller, network, 0, 0)
    # summoning portal
    elif event['address'] in ['0x65DEA93f7b886c33A78c10343267DD39727778c2','0xf4d3aE202c9Ae516f7eb1DB5afF19Bf699A5E355','0xa2D001C829328aa06a2DB2740c05ceE1bFA3c6bb', '0xBc36D18662Bb97F9e74B1EAA1B752aA7A44595A7']:
        results = events.extractSummonResults(w3, tx, None, timestamp, receipt, network)
        if results != None and type(results[1]) != int and len(results[1]) > 2 and results[1][2] != None:
            if db.findTransaction(tx, results[1][2].seller) == None:
                db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[1][2]), results[1][2].seller, network, 0, 0)
    else:
        logging.error('Unknown contract in filter')

def parseEvents(network):
    # Connect to w3
    if network == 'dfkchain':
        w3 = Web3(Web3.HTTPProvider(nets.dfk_web3))
        # middleware used to allow for interpreting longer data length for get_block on dfkchain
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        tavernContract = '0xc390fAA4C7f66E4D62E59C231D5beD32Ff77BEf0'
        portalContract = '0xBc36D18662Bb97F9e74B1EAA1B752aA7A44595A7'
    else:
        w3 = Web3(Web3.HTTPProvider(nets.hmy_web3))
        tavernContract = '0x13a65B9F8039E2c032Bc022171Dc05B30c3f2892'
        portalContract = '0x65DEA93f7b886c33A78c10343267DD39727778c2'

    if not w3.isConnected():
        logging.critical('Error: Critical w3 connection failure for '.format(network))
        return 'Error: Blockchain connection failure.'
    # pick up where last process left off in blocks
    try:
        with open("last_block_checked_{0}.txt".format(network)) as f:
            blockNumber = int(f.read().strip())
    except IOError as e:
        logging.error("No last checked block using default")
        blockNumber = 22036051
    except ValueError as e:
        logging.error("No last checked block using default")
        blockNumber = 22036051

    toBlock = w3.eth.block_number

    # create a filter for unsearched blocks of auction house and summoning portal contracts
    with open('abi/HeroSummoningUpgradeable.json', 'r') as f:
        ABI = f.read()
    portalContract = w3.eth.contract(address=portalContract, abi=ABI)
    with open('abi/SaleAuction.json', 'r') as f:
        ABI = f.read()
    tavernContract = w3.eth.contract(address=tavernContract, abi=ABI)

    endBlock = blockNumber
    while endBlock < toBlock:
        # DFKChain max blocks to read at a time is 2048 and harmony 1023
        endBlock += 1023
        if endBlock > toBlock:
            endBlock = toBlock
        tavernFilter = tavernContract.events.AuctionSuccessful().createFilter(fromBlock=blockNumber, toBlock=endBlock)
        tavernChanges = tavernFilter.get_all_entries()
        w3.eth.uninstall_filter(tavernFilter.filter_id)

        portalFilter = portalContract.events.AuctionSuccessful().createFilter(fromBlock=blockNumber, toBlock=endBlock)
        portalChanges = portalFilter.get_all_entries()
        w3.eth.uninstall_filter(portalFilter.filter_id)

        allChanges = tavernChanges + portalChanges
        if network == 'harmony':
            petCatalogContract = w3.eth.contract(address='0x72F860bF73ffa3FC42B97BbcF43Ae80280CFcdc3', abi=ABI)
            petSalesFilter = petCatalogContract.events.AuctionSuccessful().createFilter(fromBlock=blockNumber, toBlock=endBlock)
            petSaleChanges = petSalesFilter.get_all_entries()
            w3.eth.uninstall_filter(petSalesFilter.filter_id)
            allChanges = allChanges + petSaleChanges

        for event in allChanges:
            handleLogs(w3, event, network)
            # keep track of what block we are on
            try:
                if event['blockNumber'] > 0:
                    with open("last_block_checked_{0}.txt".format(network), "w") as f:
                        f.write(str(event['blockNumber']))
            except IOError as e:
                logging.critical('failed to write last block checked {0}'.format(e))
        blockNumber = endBlock
    try:
        with open("last_block_checked_{0}.txt".format(network), "w") as f:
            f.write(str(toBlock))
    except IOError as e:
        logging.critical('failed to write last block checked {0}'.format(e))

def main():
    # get in the right spot when running this so file paths can be managed relatively
    location = os.path.abspath(__file__)
    os.chdir('/'.join(location.split('/')[0:-1]))
    handler = logging.handlers.RotatingFileHandler('../blockCrawler.log', maxBytes=33554432, backupCount=10)
    logging.basicConfig(handlers=[handler], level=logging.WARNING, format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logging.info('started crawler')

    parseEvents('harmony')
    parseEvents('dfkchain')

if __name__ == "__main__":
	main()
