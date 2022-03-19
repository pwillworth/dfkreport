#!/usr/bin/env python3
import logging
import logging.handlers
import os
from web3 import Web3
from web3.logs import STRICT, IGNORE, DISCARD, WARN
import jsonpickle
import nets
import events
import db


def handleLogs(w3, event):
    timestamp = w3.eth.get_block(event['blockNumber'])['timestamp']
    tx = event['transactionHash'].hex()
    logging.info('handling event for tx {0} block {1}'.format(tx, event['blockNumber']))
    receipt = w3.eth.get_transaction_receipt(tx)
    # Heroes or Lands
    if event['address'] in ['0x13a65B9F8039E2c032Bc022171Dc05B30c3f2892', '0x77D991987ca85214f9686131C58c1ABE4C93E547']:
        if event['address'] == '0x77D991987ca85214f9686131C58c1ABE4C93E547':
            auctionType = 'land'
        else:
            auctionType = 'hero'
        results = events.extractAuctionResults(w3, tx, None, timestamp, receipt, auctionType)
        if results != None and results[1] != None and db.findTransaction(tx, results[1].seller) == None:
            db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[1]), results[1].seller)
    # Three possible addresses for summoning portal
    elif event['address'] in ['0x65DEA93f7b886c33A78c10343267DD39727778c2','0xf4d3aE202c9Ae516f7eb1DB5afF19Bf699A5E355','0xa2D001C829328aa06a2DB2740c05ceE1bFA3c6bb']:
        results = events.extractSummonResults(w3, tx, None, timestamp, receipt)
        if results != None and type(results[1]) != int and len(results[1]) > 2 and results[1][2] != None:
            if db.findTransaction(tx, results[1][2].seller) == None:
                db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[1][2]), results[1][2].seller)
    else:
        logging.error('Unknown contract in filter')


def main():
    # get in the right spot when running this so file paths can be managed relatively
    location = os.path.abspath(__file__)
    os.chdir('/'.join(location.split('/')[0:-1]))
    handler = logging.handlers.RotatingFileHandler('../blockCrawler.log', maxBytes=33554432, backupCount=10)
    logging.basicConfig(handlers=[handler], level=logging.WARNING, format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logging.info('started crawler')
    # Connect to w3
    w3 = Web3(Web3.HTTPProvider(nets.hmy_web3))
    if not w3.isConnected():
        logging.critical('Error: Critical w3 connection failure for '.format(nets.hmy_web3))
        return 'Error: Blockchain connection failure.'
    # pick up where last process left off in blocks
    try:
        with open("last_block_checked.txt") as f:
            blockNumber = int(f.read().strip())
    except IOError as e:
        logging.error("No last checked block using default")
        blockNumber = 22036051
    except ValueError as e:
        logging.error("No last checked block using default")
        blockNumber = 22036051

    logging.warning('Getting events from block {0} through {1}'.format(str(blockNumber), 'latest'))
    # create a filter for unsearched blocks of auction house and summoning portal contracts
    with open('abi/SaleAuction.json', 'r') as f:
        ABI = f.read()
    contract = w3.eth.contract(address='0x13a65B9F8039E2c032Bc022171Dc05B30c3f2892', abi=ABI)
    tavernFilter = contract.events.AuctionSuccessful().createFilter(fromBlock=blockNumber)
    tavernChanges = tavernFilter.get_all_entries()
    w3.eth.uninstall_filter(tavernFilter.filter_id)

    with open('abi/HeroSummoningUpgradeable.json', 'r') as f:
        ABI = f.read()
    contract = w3.eth.contract(address='0x65DEA93f7b886c33A78c10343267DD39727778c2', abi=ABI)
    portalFilter = contract.events.AuctionSuccessful().createFilter(fromBlock=blockNumber)
    portalChanges = portalFilter.get_all_entries()
    w3.eth.uninstall_filter(portalFilter.filter_id)

    hmyChanges = tavernChanges + portalChanges
    for event in hmyChanges:
        handleLogs(w3, event)
        # keep track of what block we are on
        try:
            with open("last_block_checked.txt", "w") as f:
                f.write(str(event['blockNumber']))
        except IOError as e:
            logging.critical('failed to write last block checked {0}'.format(e))


if __name__ == "__main__":
	main()
