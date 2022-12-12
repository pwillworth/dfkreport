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
    if event['address'] in ['0x13a65B9F8039E2c032Bc022171Dc05B30c3f2892', '0x77D991987ca85214f9686131C58c1ABE4C93E547', '0xc390fAA4C7f66E4D62E59C231D5beD32Ff77BEf0', '0x72F860bF73ffa3FC42B97BbcF43Ae80280CFcdc3', '0x49744F76caA3B63CccE9CE7de5C8282C92c891e5','0x7F2B66DB2D02f642a9eb8d13Bc998d441DDe17A8']:
        if event['address'] in ['0x77D991987ca85214f9686131C58c1ABE4C93E547','0xE74D437d5F4893dB0A5758f5EaeB5B3Af6096036']:
            auctionType = 'land'
        elif event['address'] in ['0x72F860bF73ffa3FC42B97BbcF43Ae80280CFcdc3','0x49744F76caA3B63CccE9CE7de5C8282C92c891e5','0x7aB1C574A8762bEde901F32670481c0427DdF626']:
            auctionType = 'pet'
        else:
            auctionType = 'hero'
        results = events.extractAuctionResults(w3, tx, None, timestamp, receipt, auctionType, network)
        if results != None and results[1] != None and db.findTransaction(tx, results[1].seller) == None:
            db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[1]), results[1].seller, network, 0, 0)
    else:
        logging.error('Unknown contract in filter: {0}'.format(event['address']))

def parseEvents(network):
    # Connect to w3
    if network == 'dfkchain':
        w3 = Web3(Web3.HTTPProvider(nets.dfk_web3))
        # middleware used to allow for interpreting longer data length for get_block on dfkchain
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        tavernContractAddress = '0xc390fAA4C7f66E4D62E59C231D5beD32Ff77BEf0'
        petCatalogContractAddress = '0x49744F76caA3B63CccE9CE7de5C8282C92c891e5'
    elif network == 'klaytn':
        w3 = Web3(Web3.HTTPProvider(nets.klaytn_public_web3))
        tavernContractAddress = '0x7F2B66DB2D02f642a9eb8d13Bc998d441DDe17A8'
        petCatalogContractAddress = '0x7aB1C574A8762bEde901F32670481c0427DdF626'
    elif network == 'harmony':
        w3 = Web3(Web3.HTTPProvider(nets.hmy_web3))
        tavernContractAddress = '0x13a65B9F8039E2c032Bc022171Dc05B30c3f2892'
        petCatalogContractAddress = '0x72F860bF73ffa3FC42B97BbcF43Ae80280CFcdc3'

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
    logging.warning('Getting {2} events from block {0} through {1}'.format(str(blockNumber), str(toBlock), network))

    # create a filter for unsearched blocks of auction houses
    with open('abi/SaleAuction.json', 'r') as f:
        ABI = f.read()
    tavernContract = w3.eth.contract(address=tavernContractAddress, abi=ABI)
    petCatalogContract = w3.eth.contract(address=petCatalogContractAddress, abi=ABI)

    endBlock = blockNumber
    while endBlock < toBlock:
        # DFKChain max blocks to read at a time is 2048 and harmony 1023
        endBlock += 1023
        if endBlock > toBlock:
            endBlock = toBlock
        tavernFilter = tavernContract.events.AuctionSuccessful().createFilter(fromBlock=blockNumber, toBlock=endBlock)
        try:
            tavernChanges = tavernFilter.get_all_entries()
        except ValueError as err:
            logging.warning('got expected error meaning no events getting entries for {0}: {1}'.format(network, str(err)))
        w3.eth.uninstall_filter(tavernFilter.filter_id)

        petSalesFilter = petCatalogContract.events.AuctionSuccessful().createFilter(fromBlock=blockNumber, toBlock=endBlock)
        try:
            petSaleChanges = petSalesFilter.get_all_entries()
        except ValueError as err:
            logging.warning('got expected error meaning no events getting entries for {0}: {1}'.format(network, str(err)))
        w3.eth.uninstall_filter(petSalesFilter.filter_id)
        allChanges = tavernChanges + petSaleChanges

        for event in allChanges:
            # We do not need to call handle function for multiple events in same tx because the fuction handles the whole tx
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

    #parseEvents('harmony')
    parseEvents('dfkchain')
    parseEvents('klaytn')

if __name__ == "__main__":
	main()
