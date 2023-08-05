#!/usr/bin/env python3
import os
import requests
from pickletools import read_uint2
from web3 import Web3
from web3.logs import STRICT, IGNORE, DISCARD, WARN
import nets
import records
import prices
import db
import settings
import datetime
import time
import decimal
import jsonpickle
import logging
import contracts


def getABI(contractName):
    location = os.path.abspath(__file__)
    with open('{0}/abi/{1}.json'.format('/'.join(location.split('/')[0:-1]), contractName), 'r') as f:
        ABI = f.read()
    return ABI

def checkTransactions(account, txs, wallet, startDate, endDate, walletHash, network, alreadyComplete=0):
    # Connect to right network that txs are for
    if network == 'klaytn':
        w3 = Web3(Web3.HTTPProvider(nets.klaytn_web3))
    elif network == 'dfkchain':
        w3 = Web3(Web3.HTTPProvider(nets.dfk_web3))
    elif network == 'avalanche':
        w3 = Web3(Web3.HTTPProvider(nets.avax_web3))
    elif network == 'harmony':
        w3 = Web3(Web3.HTTPProvider(nets.hmy_web3))
    else:
        logging.error('could not check transactions for unsupported network: {0}'.format(network))
        return 'Error: Blockchain connection failure'

    if not w3.is_connected():
        logging.error('Error: Critical w3 connection failure for {0}'.format(network))
        return 'Error: Blockchain connection failure.'

    txCount = 0
    heroCrystals = {}
    petEggs = {}
    savedTx = []
    txList = []
    if settings.USE_CACHE:
        savedTx = db.getTransactions(wallet, network)

    for txn in txs:
        # The AVAX list data includes the whole transaction, but harmony is just the hash
        if network == 'avalanche':
            tx = txn['hash']
            timestamp = int(txn['timeStamp'])
        elif network == 'dfkchain':
            tx = txn['nativeTransaction']['txHash']
            timestamp = txn['nativeTransaction']['blockTimestamp']
        elif network == 'klaytn':
            tx = txn['hash']
            timestamp = txn['block']['timestamp']['unixtime']
        else:
            tx = txn
        txList.append(tx)
        eventsFound = False
        # Update report tracking record for status every 50 txs
        if txCount % 50 == 0:
            try:
                db.updateReport(account, datetime.datetime.strftime(startDate, '%Y-%m-%d'), datetime.datetime.strftime(endDate, '%Y-%m-%d'), walletHash, 'complete', alreadyComplete + txCount)
            except Exception as err:
                logging.error('Failed to update tx count {0}'.format(str(err)))

        # No need to process tx if already saved
        checkCache = savedTx.get(tx, None)
        if checkCache != None:
            savedTx.pop(tx)
            txCount += 1
            continue

        try:
            # sometimes they just don't exist yet
            result = w3.eth.get_transaction(tx)
        except Exception as err:
            logging.error('Got failed to get transaction {0} {1}'.format(tx, str(err)))
            time.sleep(1)
            continue
        action = lookupEvent(result['from'], result['to'], wallet)
        value = Web3.from_wei(result['value'], 'ether')
        block = result['blockNumber']
        if network == 'harmony':
            try:
                timestamp = w3.eth.get_block(block)['timestamp']
            except Exception as err:
                logging.error('Got invalid block {0} {1}'.format(block, str(err)))
                time.sleep(1)
                continue
        blockDate = datetime.date.fromtimestamp(timestamp)
        #TODO return list of failed transaction lookups as discrepancies for investigation
        try:
            receipt = w3.eth.get_transaction_receipt(tx)
        except Exception as err:
            logging.error('Got invalid transaction {0} {1}'.format(tx, str(err)))
            time.sleep(1)
            continue
        #TODO deduct gas from cost basis
        txFee = Web3.from_wei(result['gasPrice'], 'ether') * receipt['gasUsed']
        feeValue = prices.priceLookup(timestamp, contracts.GAS_TOKENS[network], network) * txFee
        logging.info('gas data {0} - {1}'.format(txFee, feeValue))
        results = None
        if receipt['status'] == 1:
            logging.info("{5}:{4} | {3}: {0} - {1} - {2}".format(action, '{:f} value'.format(value), '{:f} fee'.format(txFee), tx, datetime.datetime.fromtimestamp(timestamp).isoformat(), network))
            if 'Quest' in action and result['input'] != '0x':
                results = extractQuestResults(w3, tx, timestamp, receipt, result['to'], network)
                if len(results) > 0:
                    results[0].fiatFeeValue = feeValue
                    eventsFound = True
                    db.saveTransaction(tx, timestamp, 'quests', jsonpickle.encode(results), wallet, network, txFee, feeValue)
                else:
                    logging.info('{0} quest with no rewards.'.format(tx))
            elif 'AuctionHouse' in action:
                if 'Pet' in action:
                    results = extractAuctionResults(w3, tx, wallet, timestamp, receipt, 'pet', network)
                else:
                    results = extractAuctionResults(w3, tx, wallet, timestamp, receipt, 'hero', network)
                if results != None and results[0] != None:
                    results[0].fiatFeeValue = feeValue
                    eventsFound = True
                    db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[0]), wallet, network, txFee, feeValue)
                else:
                    logging.info('Ignored an auction interaction, probably listing.')
                # Second record is to be saved in db and will be looked up when seller runs thier tax report
                # All of these get populated by running a report for the Tavern Address though, so we need to
                # skip if record has already been created.
                if results != None and results[1] != None and db.findTransaction(tx, results[1].seller) == None:
                    db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[1]), results[1].seller, network, 0, 0)
            elif 'LandAuction' in action:
                results = extractAuctionResults(w3, tx, wallet, timestamp, receipt, 'land', network)
                if results != None and results[0] != None:
                    results[0].fiatFeeValue = feeValue
                    eventsFound = True
                    db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[0]), wallet, network, txFee, feeValue)
                else:
                    logging.info('Ignored an auction interaction, probably listing.')
                # Second record is to be saved in db and will be looked up when seller runs thier tax report
                # All of these get populated by running a report for the Tavern Address though, so we need to
                # skip if record has already been created.
                if results != None and results[1] != None and db.findTransaction(tx, results[1].seller) == None:
                    db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[1]), results[1].seller, network, 0, 0)
            elif 'Uniswap' in action:
                results = extractSwapResults(w3, tx, wallet, result['to'], timestamp, receipt, value, network)
                if results != None:
                    if type(results) is records.TraderTransaction:
                        results.fiatFeeValue = feeValue
                        eventsFound = True
                        db.saveTransaction(tx, timestamp, 'swaps', jsonpickle.encode(results), wallet, network, txFee, feeValue)
                    elif type(results) is records.LiquidityTransaction:
                        results.fiatFeeValue = feeValue
                        eventsFound = True
                        db.saveTransaction(tx, timestamp, 'liquidity', jsonpickle.encode(results), wallet, network, txFee, feeValue)
                else:
                    logging.error('Error: Failed to parse a swap result. {0}'.format('not needed'))
            elif 'Bazaar' in action:
                results = extractBazaarResults(w3, tx, wallet, result['to'], timestamp, receipt, value, network)
                if results != None:
                    results.fiatFeeValue = feeValue
                    eventsFound = True
                    db.saveTransaction(tx, timestamp, 'trades', jsonpickle.encode(results), wallet, network, txFee, feeValue)
                else:
                    logging.error('Error: Failed to parse a swap result. {0}'.format('not needed'))
            elif 'Gardener' in action:
                results = extractGardenerResults(w3, tx, wallet, timestamp, receipt, network)
                if results != None and len(results) > 0:
                    results[0].fiatFeeValue = feeValue
                    eventsFound = True
                    db.saveTransaction(tx, timestamp, 'gardens', jsonpickle.encode(results), wallet, network, txFee, feeValue)
                else:
                    logging.error('Error: Failed to parse a Gardener LP Pool result. tx {0}'.format(tx))
            elif 'Farms' in action:
                results = extractFarmResults(w3, tx, wallet, timestamp, receipt, network)
                if results != None and len(results) > 0:
                    results[0].fiatFeeValue = feeValue
                    eventsFound = True
                    db.saveTransaction(tx, timestamp, 'gardens', jsonpickle.encode(results), wallet, network, txFee, feeValue)
                else:
                    logging.error('Error: Failed to parse a Gardener LP Pool result. tx {0}'.format(tx))
            elif 'Lending' in action:
                logging.info("Lending activity {0}".format(tx))
                eventsFound = True
                results = extractLendingResults(w3, tx, wallet, timestamp, receipt, network, value)
                if results != None:
                    if results[0] != None:
                        results[0].fiatFeeValue = feeValue
                        db.saveTransaction(tx, timestamp, 'lending', jsonpickle.encode(results[0]), wallet, network, txFee, feeValue)
                    if results[1] != None:
                        db.saveTransaction(tx, timestamp, 'lending', jsonpickle.encode(results[1]), wallet, network, 0, 0)
            elif 'Airdrop' in action:
                results = extractAirdropResults(w3, tx, wallet, timestamp, receipt, network)
                if len(results) > 0:
                    results[0].fiatFeeValue = feeValue
                    eventsFound = True
                    db.saveTransaction(tx, timestamp, 'airdrops', jsonpickle.encode(results), wallet, network, txFee, feeValue)
            elif 'Payment Service' in action:
                # Some payment distributions do not get associated to users wallet, so populate record in db for recipient
                # these transactions are discovered by block crawler
                results = extractAirdropResults(w3, tx, wallet, timestamp, receipt, network)
                for item in results:
                    recipientAccount = ''
                    for item in results:
                        if recipientAccount not in ['', item.address]:
                            logging.error('Bailing from multi recipient payment {0}'.format(tx))
                            continue
                        recipientAccount = item.address
                        item.address = result['from']
                    if recipientAccount != '' and db.findTransaction(tx, recipientAccount) == None:
                        db.saveTransaction(tx, timestamp, 'airdrops', jsonpickle.encode(results), recipientAccount, network, 0, 0)
            elif 'Banker' in action:
                logging.info('Banker interaction, probably just claim which distributes to bank, no events to record. {0}'.format(tx))
            elif result['input'] != '0x' and ('xJewel' in action or 'xCrystal' in action):
                results = extractBankResults(w3, tx, wallet, timestamp, receipt, network)
                if results != None:
                    results.fiatFeeValue = feeValue
                    eventsFound = True
                    db.saveTransaction(tx, timestamp, 'bank', jsonpickle.encode(results), wallet, network, txFee, feeValue)
                else:
                    # if no bank result was parsed, it is just a direct xJewel transfer
                    logging.error('Error: Failed to parse a bank result.')
                    ABI = getABI('xJewel')
                    contract = w3.eth.contract(address='0xA9cE83507D872C5e1273E745aBcfDa849DAA654F', abi=ABI)
                    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
                    for log in decoded_logs:
                        logging.info('banklog: ' + str(log))
            elif 'cJewel' in action or 'sJewel' in action:
                results = extractJewelerResults(w3, tx, wallet, result['to'], timestamp, receipt, network)
                if results[0] != None:
                    results[0].fiatFeeValue = feeValue
                if results[1] != None:
                    if results[0] == None:
                        results[1].fiatFeeValue = feeValue
                if results[2] != None:
                    eventsFound = True
                if results[0] != None or results[1] != None:
                    db.saveTransaction(tx, timestamp, 'bank', jsonpickle.encode([result for result in results if result != None]), wallet, network, txFee, feeValue)
            elif 'Vendor' in action:
                logging.debug('Vendor activity: {0}'.format(str(receipt['logs'][0]['address'])))
                results = extractSwapResults(w3, tx, wallet, result['to'], timestamp, receipt, value, network)
                if results != None and type(results) is records.TraderTransaction:
                    results.fiatFeeValue = feeValue
                    eventsFound = True
                    db.saveTransaction(tx, timestamp, 'swaps', jsonpickle.encode(results), wallet, network, txFee, feeValue)
                else:
                    logging.error('Error: Failed to parse a vendor result. {0}'.format(receipt['logs'][0]['address']))
            elif 'Summoning' in action:
                logging.info('Summoning {1} activity: {0}'.format(tx, action))
                results = extractSummonResults(w3, tx, wallet, timestamp, receipt, network)
                if results != None:
                    if type(results[1]) == int:
                        eventsFound = True
                        logging.info('heroid results {0} {1}'.format(tx, results))
                        if results[0] in heroCrystals:
                            # crystal open event just returns the hero ID summoned so we can now add the full data
                            for r in heroCrystals[results[0]][2]:
                                if r != None:
                                    r.itemID = results[1]
                            events = [heroCrystals[results[0]][2][0], heroCrystals[results[0]][2][1]]
                            events[0].fiatFeeValue = heroCrystals[results[0]][5]
                            events[1].fiatFeeValue = feeValue
                            if heroCrystals[results[0]][2][3] != None:
                                events.append(heroCrystals[results[0]][2][3])
                            if db.findTransaction(heroCrystals[results[0]][0], wallet) == None:
                                db.saveTransaction(heroCrystals[results[0]][0], heroCrystals[results[0]][1], 'tavern', jsonpickle.encode(events), wallet, network, txFee, feeValue)
                            else:
                                logging.info('tried to save portal record that already existed {0}'.format(tx))
                            if db.findTransaction(tx, wallet) == None:
                                db.saveTransaction(tx, timestamp, 'nones', '', wallet, network, heroCrystals[results[0]][4], heroCrystals[results[0]][5])
                            else:
                                logging.info('tried to save none portal when record already existed {0}'.format(tx))
                        else:
                            # on rare occassion the crystal open even might get parsed before the summon crystal
                            heroCrystals[results[0]] = [tx, timestamp, [], results[1], txFee, feeValue]
                    elif len(results[1]) > 1 and results[1][1] != None:
                        eventsFound = True
                        if results[0] not in heroCrystals:
                            # store crystal creation events for later so we can tag it with the summoned hero id
                            heroCrystals[results[0]] = [tx, timestamp, results[1], 0, txFee, feeValue]
                        else:
                            # events came in backwards and now we can save with hero id
                            results[1][1].itemID = heroCrystals[results[0]][3]
                            if results[1][0] != None:
                                results[1][0].itemID = heroCrystals[results[0]][3]
                            events = [results[1][0], results[1][1]]
                            events[0].fiatFeeValue = heroCrystals[results[0]][5]
                            events[1].fiatFeeValue = txFee
                            if results[1][3] != None:
                                events.append(results[1][3])
                            if db.findTransaction(tx, wallet) == None:
                                db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(events), wallet, network, txFee, feeValue)
                            else:
                                logging.info('tried to save backwards portal that already existed {0}'.format(tx))
                            if db.findTransaction(heroCrystals[results[0]][0], wallet) == None:
                                db.saveTransaction(heroCrystals[results[0]][0], timestamp, 'nonec', '', wallet, network, heroCrystals[results[0]][4], heroCrystals[results[0]][5])
                            else:
                                logging.info('tried to save a backwards noen that already existed {0}'.format(tx))
                    if type(results[1]) != int and len(results[1]) > 2 and results[1][2] != None:
                        eventsFound = True
                        # If third event it is hero hire during summon
                        # record is to be saved in db and will be looked up when seller runs thier tax report
                        if db.findTransaction(tx, results[1][2].seller) == None:
                            db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[1][2]), results[1][2].seller, network, 0, 0)
                        else:
                            logging.info('summon hire found but was already in db on {0}.'.format(tx))
                else:
                    logging.info('Error: Failed to parse a summon result. {0}'.format(tx))
            elif 'PetIncubator' in action:
                logging.info('Pet hatching activity: {0}'.format(tx))
                # pet hatching
                results = extractHatchingResults(w3, tx, wallet, timestamp, receipt, network)
                if results != None:
                    if results[1] != None and results[1].event == 'crack':
                        eventsFound = True
                        if results[0] in petEggs and petEggs[results[0]][2] != None and petEggs[results[0]][2].itemID in contracts.EGG_TOKENS[network]:
                            logging.info('complete incubate with crack')
                            # pet crack event includes the pet ID summoned so we can now add the full data
                            logging.info('egg id {0}'.format(petEggs[results[0]][2].itemID))
                            eggToken = contracts.EGG_TOKENS[network][petEggs[results[0]][2].itemID]
                            petEggs[results[0]][2].itemID = results[1].itemID
                            hatchCosts = 0
                            costList = 'costs'
                            for k, v in petEggs[results[0]][6].items():
                                costList = '{0},{1} {2}'.format(costList, v, contracts.getTokenName(k, network))
                                priceEach = prices.priceLookup(timestamp, k, network)
                                hatchCosts += priceEach * v
                                logging.info('Adding cost {0} {1} for {2}'.format(v, contracts.getTokenName(k, network), priceEach))
                            results[1].coinType = eggToken
                            results[1].coinCost = 1
                            results[1].fiatAmount = hatchCosts
                            results[1].seller = costList
                            events = [petEggs[results[0]][2], results[1]]
                            if db.findTransaction(petEggs[results[0]][0], wallet) == None:
                                db.saveTransaction(petEggs[results[0]][0], petEggs[results[0]][1], 'tavern', jsonpickle.encode(events), wallet, network, txFee, feeValue)
                            else:
                                logging.info('tried to save egg record that already existed {0}'.format(tx))
                            if db.findTransaction(tx, wallet) == None:
                                db.saveTransaction(tx, timestamp, 'nonep', '', wallet, network, petEggs[results[0]][4], petEggs[results[0]][5])
                            else:
                                logging.info('tried to save none egg when record already existed {0}'.format(tx))
                        else:
                            # on rare occassion the egg crack event might get parsed before the incubate
                            logging.info('store crack')
                            petEggs[results[0]] = [tx, timestamp, None, results[1], txFee, feeValue, None]
                    elif results[1] != None and results[1].event == 'incubate':
                        eventsFound = True
                        if results[0] not in petEggs:
                            # store incubate events for later so we can tag it with the pet id
                            logging.info('store incubate')
                            petEggs[results[0]] = [tx, timestamp, results[1], None, txFee, feeValue, results[2]]
                        else:
                            # events came in backwards and now we can save with pet id
                            logging.info('complete crack with incubate')
                            eggToken = contracts.EGG_TOKENS[network][results[1].itemID]
                            if petEggs[results[0]][3] != None:
                                results[1].itemID = petEggs[results[0]][3].itemID
                                hatchCosts = 0
                                costList = 'costs'
                                for k, v in results[2].items():
                                    costList = '{0},{1} {2}'.format(costList, v, contracts.getTokenName(k, network))
                                    hatchCosts += prices.priceLookup(timestamp, k, network) * v
                                petEggs[results[0]][3].coinType = eggToken
                                petEggs[results[0]][3].coinCost = 1
                                petEggs[results[0]][3].fiatAmount = hatchCosts
                                petEggs[results[0]][3].seller = costList
                                events = [results[1], petEggs[results[0]][3]]
                                if db.findTransaction(tx, wallet) == None:
                                    db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(events), wallet, network, txFee, feeValue)
                                else:
                                    logging.info('tried to save backwards hatching that already existed {0}'.format(tx))
                                if db.findTransaction(petEggs[results[0]][0], wallet) == None:
                                    db.saveTransaction(petEggs[results[0]][0], timestamp, 'nonep', '', wallet, network, petEggs[results[0]][4], petEggs[results[0]][5])
                                else:
                                    logging.info('tried to save a backwards none hatch that already existed {0}'.format(tx))
                else:
                    logging.info('Error: Failed to parse a hatching result. {0}'.format(tx))
            elif 'Meditation' in action:
                logging.debug('Meditation activity: {0}'.format(tx))
                results = extractMeditationResults(w3, tx, wallet, timestamp, receipt, network)
                if results != None:
                    if results[0] != None:
                        results[0].fiatFeeValue = feeValue
                    for record in results:
                        if type(record) is records.TavernTransaction:
                            eventsFound = True
                    if eventsFound:
                        db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode([r for r in results if r]), wallet, network, txFee, feeValue)
                else:
                    logging.info('Error: Failed to parse a meditation result. {0}'.format(tx))
            elif 'Alchemist' in action or 'Stone Carver' in action:
                logging.debug('Alchemist activity: {0}'.format(tx))
                results = extractAlchemistResults(w3, tx, wallet, timestamp, receipt, network)
                if results != None:
                    results.fiatFeeValue = feeValue
                    eventsFound = True
                    db.saveTransaction(tx, timestamp, 'alchemist', jsonpickle.encode(results), wallet, network, txFee, feeValue)
                else:
                    logging.info('Failed to parse alchemist results tx {0}'.format(tx))
            elif 'HeroSale' in action:
                # Special Gen0 sale events are like a summon but are crystals are bought with jewel
                ABI = getABI('HeroSale')
                contract = w3.eth.contract(address='0xdF0Bf714e80F5e6C994F16B05b7fFcbCB83b89e9', abi=ABI)
                decoded_logs = contract.events.Gen0Purchase().process_receipt(receipt, errors=DISCARD)
                heroId = 0
                purchasePrice = 0
                crystalId = 0
                for log in decoded_logs:
                    logging.info('Purchase Gen0 Crystal id {0} price {1}'.format(log['args']['crystalId'], log['args']['purchasePrice']))
                    crystalId = log['args']['crystalId']
                    purchasePrice = log['args']['purchasePrice']
                decoded_logs = contract.events.CrystalOpen().process_receipt(receipt, errors=DISCARD)
                for log in decoded_logs:
                    logging.info('Open Gen0 Crystal id {0} heroid {1}'.format(log['args']['crystalId'], log['args']['heroId']))
                    crystalId = log['args']['crystalId']
                    heroId = log['args']['heroId']
                if crystalId != 0:
                    eventsFound = True
                    if log['args']['crystalId'] not in heroCrystals:
                        heroCrystals[log['args']['crystalId']] = [tx, timestamp, purchasePrice, heroId, txFee, feeValue]
                    else:
                        heroCrystals[log['args']['crystalId']][2] = max(purchasePrice, heroCrystals[log['args']['crystalId']][2])
                        heroCrystals[log['args']['crystalId']][3] = max(heroId, heroCrystals[log['args']['crystalId']][3])
                        if heroCrystals[log['args']['crystalId']][2] > 0 and heroCrystals[log['args']['crystalId']][3] > 0:
                            heroPrice = Web3.from_wei(heroCrystals[log['args']['crystalId']][2], 'ether')
                            r = records.TavernTransaction(tx, network, 'hero', heroCrystals[log['args']['crystalId']][3], 'purchase', timestamp, '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', heroPrice)
                            r.fiatAmount = prices.priceLookup(timestamp, 'defi-kingdoms', network) * r.coinCost
                            r.fiatFeeValue = feeValue
                            db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(r), wallet, network, txFee, feeValue)
                            db.saveTransaction(heroCrystals[log['args']['crystalId']][0], heroCrystals[log['args']['crystalId']][1], 'noneg', '', wallet, network, heroCrystals[log['args']['crystalId']][4], heroCrystals[log['args']['crystalId']][5])
            elif 'anySwap' in action or 'Bridge' in action:
                logging.debug('Bridge activity: {0}'.format(tx))
                results = extractBridgeResults(w3, tx, wallet, timestamp, receipt, network)
                if results != None:
                    results.fiatFeeValue = feeValue
                    eventsFound = True
                    db.saveTransaction(tx, timestamp, 'wallet', jsonpickle.encode(results), wallet, network, txFee, feeValue)
                else:
                    logging.info('Failed to parse bridge results tx {0}'.format(tx))
            elif 'Potion Use' in action:
                logging.debug('Used Potion: {0}'.format(tx))
                results = extractPotionResults(w3, tx, wallet, timestamp, receipt, result['input'], network)
                eventsFound = True
                if results != None:
                    results.fiatFeeValue = feeValue
                    db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results), wallet, network, txFee, feeValue)
                else:
                    logging.info('Failed to parse potion results {0}'.format(tx))
            elif 'Perilous Journey' in action:
                logging.debug('Perilous Journey activity: {0}'.format(tx))
                results = extractJourneyResults(w3, tx, wallet, timestamp, receipt, result['input'], network)
                eventsFound = True
                if len(results) > 0:
                    results[0].fiatFeeValue = feeValue
                    db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results), wallet, network, txFee, feeValue)
                else:
                    if db.findTransaction(tx, wallet) == None:
                        db.saveTransaction(tx, timestamp, 'nonepj', '', wallet, network, txFee, feeValue)
                    logging.info('No events for Perilous Journey tx {0}'.format(tx))
            elif 'PetTradeIn' in action:
                logging.debug('Pet Trade In activity: {0}'.format(tx))
                results = extractPetBurnResults(w3, tx, wallet, timestamp, receipt, network)
                eventsFound = True
                if len(results) > 0 and results[0] != None:
                    results[0].fiatFeeValue = feeValue
                    db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results), wallet, network, txFee, feeValue)
                else:
                    if db.findTransaction(tx, wallet) == None:
                        db.saveTransaction(tx, timestamp, 'nonept', '', wallet, network, txFee, feeValue)
                    logging.info('No events for Pet Trade In tx {0}'.format(tx))
            elif 'DFKDuel' in action:
                logging.debug('DFK Duel activity: {0}'.format(tx))
                results = extractDFKDuelResults(w3, tx, wallet, timestamp, receipt, result['input'], network)
                eventsFound = True
                if results != None:
                    results.fiatFeeValue = feeValue
                    db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results), wallet, network, txFee, feeValue)
                else:
                    if db.findTransaction(tx, wallet) == None:
                        db.saveTransaction(tx, timestamp, 'nonedd', '', wallet, network, txFee, feeValue)
                    logging.info('No events for DFK Duel tx {0}'.format(tx))
            elif 'Raffle' in action:
                logging.debug('Raffle Master activity: {0}'.format(tx))
                # TODO raffle tix burn tracking
            else:
                # Native token wallet transfers
                results = []
                # Transfers from fund wallets should be considered income payments
                if result['from'] in contracts.payment_wallets:
                    depositEvent = 'payment'
                else:
                    depositEvent = 'deposit'
                if result['to'] != None and 'Donation' in contracts.getAddressName(result['to']):
                    withdrawalEvent = 'donation'
                else:
                    withdrawalEvent = 'withdraw'
                if result['to'] == wallet and value > 0:
                    r = records.walletActivity(tx, network, timestamp, depositEvent, result['from'], contracts.GAS_TOKENS[network], value)
                    r.fiatValue = prices.priceLookup(timestamp, r.coinType, network) * value
                    results.append(r)
                if result['from'] == wallet and value > 0:
                    r = records.walletActivity(tx, network, timestamp, withdrawalEvent, result['to'], contracts.GAS_TOKENS[network], value)
                    r.fiatValue = prices.priceLookup(timestamp, r.coinType, network) * value
                    results.append(r)
                # also check for any random token trasfers in the wallet
                results += extractTokenResults(w3, tx, wallet, timestamp, receipt, depositEvent, withdrawalEvent, network)
                if len(results) > 0:
                    results[0].fiatFeeValue = feeValue
                    eventsFound = True
                    if db.findTransaction(tx, wallet) == None:
                        db.saveTransaction(tx, timestamp, 'wallet', jsonpickle.encode(results), wallet, network, txFee, feeValue)
                else:
                    logging.info('Got no results from anything tx {0}'.format(tx))
        else:
            # transaction failed, mark to ignore later
            eventsFound = True
            db.saveTransaction(tx, timestamp, 'nonef', '', wallet, network, txFee, feeValue)
        # transactions with no relevant data get a none record so they are ignored in later reports
        if eventsFound == False and db.findTransaction(tx, wallet) == None:
            db.saveTransaction(tx, timestamp, 'nonee', '', wallet, network, txFee, feeValue)

        txCount += 1

    db.updateReport(account, datetime.datetime.strftime(startDate, '%Y-%m-%d'), datetime.datetime.strftime(endDate, '%Y-%m-%d'), walletHash, 'complete', alreadyComplete + txCount)
    return txCount

def lookupEvent(fm, to, account):
    fmStr = ''
    toStr = ''

    try:
        fmStr = contracts.address_map[fm]
    except KeyError:
        fmStr = fm

    try:
        toStr = contracts.address_map[to]
    except KeyError:
        if to != None:
            toStr = to

    if '0x' in fmStr and toStr == account:
        fmStr = 'Deposit from {0}'.format(fmStr)
    if '0x' in toStr and fmStr == account:
        toStr = 'Withdrawal to {0}'.format(toStr)

    return "{0} -> {1}".format(fmStr, toStr)

def extractBankResults(w3, txn, account, timestamp, receipt, network):
    ABI = getABI('xJewel')
    contract = w3.eth.contract(address='0xA9cE83507D872C5e1273E745aBcfDa849DAA654F', abi=ABI)
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    rcvdToken = "unk"
    rcvdAmount = 0
    sentToken = "unk"
    sentAmount = 0
    for log in decoded_logs:
        if 'to' in log['args'] and 'from' in log['args']:
            if log['args']['to'] == account:
                rcvdToken = log['address']
                rcvdAmount = Web3.from_wei(log['args']['value'], 'ether')
            if log['args']['from'] == account:
                sentToken = log['address']
                sentAmount = Web3.from_wei(log['args']['value'], 'ether')
        if sentAmount > 0 and rcvdAmount > 0:
            if sentToken in ['0xA9cE83507D872C5e1273E745aBcfDa849DAA654F', '0x6E7185872BCDf3F7a6cBbE81356e50DAFFB002d2']:
                # Dumping xJewel and getting Jewel from bank
                r = records.BankTransaction(txn, network, timestamp, 'withdraw', rcvdAmount / sentAmount, rcvdToken, rcvdAmount)
                r.fiatValue = prices.priceLookup(timestamp, r.coinType, network) * r.coinAmount
            else:
                # Depositing Jewel in the Bank for xJewel or xCrystal
                r = records.BankTransaction(txn, network, timestamp, 'deposit', sentAmount / rcvdAmount, sentToken, sentAmount)
                r.fiatValue = prices.priceLookup(timestamp, r.coinType, network) * r.coinAmount
            return r
    logging.warn('Bank fail data: {0} {1} {2} {3}'.format(sentAmount, sentToken, rcvdAmount, rcvdToken))

def extractJewelerResults(w3, txn, account, jeweler, timestamp, receipt, network):
    r = None
    rc = None
    rb = None
    claimAmount = 0

    ABI = getABI('VoteEscrowRewardPool')
    contract = w3.eth.contract(address='0x9ed2c155632C042CB8bC20634571fF1CA26f5742', abi=ABI)
    decoded_logs = contract.events.RewardClaimed().process_receipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        claimAmount = log['args']['amount']
        logging.info('{0} Claimed {1} Jewel reward from Jeweler.'.format(log['args']['user'], Web3.from_wei(claimAmount, 'ether')))
        rc = records.BankTransaction(txn, network, timestamp, 'claim', 0, contracts.JEWEL_ADDRESSES[network], Web3.from_wei(log['args']['amount'], 'ether'))
        rc.fiatValue = prices.priceLookup(timestamp, rc.coinType, network) * rc.coinAmount

    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    rcvdToken = ''
    rcvdAmount = 0
    sentToken = ''
    sentAmount = 0
    burnToken = ''
    burnAmount = 0
    extendAmount = 0
    for log in decoded_logs:
        # Token Transfers
        if 'to' in log['args'] and 'from' in log['args']:
            # TODO - figure out what event is happening and decode it for what sends normal jewel to account after wrapped is burned
            if log['args']['to'] == account or (log['address'] == contracts.JEWEL_ADDRESSES[network] and log['args']['from'] == jeweler and log['args']['to'] == '0x0000000000000000000000000000000000000000'):
                if claimAmount > 0 and log['args']['value'] == claimAmount:
                    # skip claim already added
                    logging.info('skip already accounted claim')
                elif log['address'] == contracts.JEWEL_ADDRESSES[network] and rcvdAmount > 0 and contracts.valueFromWei(log['args']['value'], log['address'], network) == rcvdAmount:
                    # must be emergency withdraw burn amount
                    burnToken = log['address']
                    burnAmount = contracts.valueFromWei(log['args']['value'], log['address'], network)
                elif log['address'] == contracts.GOVERNANCE_ADDRESSES[network] and rcvdAmount > 0 and rcvdToken == contracts.GOVERNANCE_ADDRESSES[network]:
                    extendAmount = contracts.valueFromWei(log['args']['value'], log['address'], network)
                else:
                    rcvdToken = log['address']
                    rcvdAmount += contracts.valueFromWei(log['args']['value'], log['address'], network)
                    logging.info('rcvd added {0}'.format(contracts.getTokenName(log['address'], network)))
            elif log['args']['from'] == account or (log['address'] == contracts.JEWEL_ADDRESSES[network] and log['args']['to'] == jeweler and log['args']['from'] == '0x0000000000000000000000000000000000000000'):
                sentToken = log['address']
                sentAmount += contracts.valueFromWei(log['args']['value'], log['address'], network)
                logging.info('sent added {0}'.format(contracts.getTokenName(log['address'], network)))
            else:
                logging.debug('ignored Jeweler log {0} to {1} not involving account'.format(log['args']['from'], log['args']['to']))

    if sentToken == contracts.JEWEL_ADDRESSES[network] and rcvdToken == contracts.GOVERNANCE_ADDRESSES[network]:
        # deposited jewel and received cJewel
        r = records.BankTransaction(txn, network, timestamp, 'deposit', rcvdAmount, sentToken, sentAmount)
        r.fiatValue = prices.priceLookup(timestamp, r.coinType, network) * r.coinAmount
        if extendAmount > 0:
            # additional cJewel receipt for extending lock duration
            rb = records.BankTransaction(txn, network, timestamp, 'extend', extendAmount, contracts.JEWEL_ADDRESSES[network], 0)
            rb.fiatValue = prices.priceLookup(timestamp, rb.coinType, network) * rb.coinAmount
    elif sentToken == contracts.GOVERNANCE_ADDRESSES[network] and rcvdToken == contracts.JEWEL_ADDRESSES[network]:
        # withdraw jewel and burn cJewel
        r = records.BankTransaction(txn, network, timestamp, 'withdraw', sentAmount / (2 if burnAmount>0 else 1), rcvdToken, rcvdAmount)
        r.fiatValue = prices.priceLookup(timestamp, r.coinType, network) * r.coinAmount
        if burnAmount > 0:
            # Jewel burn for emergency withdraw
            rb = records.BankTransaction(txn, network, timestamp, 'burn', sentAmount / (2 if burnAmount>0 else 1), burnToken, burnAmount)
            rb.fiatValue = prices.priceLookup(timestamp, rb.coinType, network) * rb.coinAmount
    elif rcvdToken == contracts.GOVERNANCE_ADDRESSES[network] and sentToken == '':
        # extend lock duration only
        r = records.BankTransaction(txn, network, timestamp, 'extend', rcvdAmount, contracts.JEWEL_ADDRESSES[network], 0)
        r.fiatValue = prices.priceLookup(timestamp, r.coinType, network) * r.coinAmount

    return [r, rc, rb]
    

def extractGardenerResults(w3, txn, account, timestamp, receipt, network):
    # events record amount of jewel/crystal received when claiming at the gardens
    powerToken = contracts.POWER_TOKENS[network]
    ABI = getABI('MasterGardener')
    contract = w3.eth.contract(address='0xDB30643c71aC9e2122cA0341ED77d09D5f99F924', abi=ABI)
    events = []
    decoded_logs = contract.events.SendGovernanceTokenReward().process_receipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        receivedAmount = Web3.from_wei(log['args']['amount'], 'ether')
        lockedAmount = Web3.from_wei(log['args']['lockAmount'], 'ether')
        r = records.GardenerTransaction(txn, network, timestamp, 'staking-reward', powerToken, receivedAmount - lockedAmount)
        rl = records.GardenerTransaction(txn, network, timestamp, 'staking-reward-locked', powerToken, lockedAmount)
        tokenPrice = prices.priceLookup(timestamp, powerToken, network)
        r.fiatValue = tokenPrice * r.coinAmount
        rl.fiatValue = tokenPrice * rl.coinAmount
        events.append(r)
        events.append(rl)

    # events record amount of lp tokens put in and out of gardens for farming and when
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    gardenEvent = ''
    gardenToken = ''
    gardenAmount = 0
    for log in decoded_logs:
        # Token Transfers
        tName = contracts.getTokenName(log['address'], network)
        if 'to' in log['args'] and 'from' in log['args'] and log['address'] != tName and 'LP Token' in tName:
            if log['args']['to'] == account:
                gardenEvent = 'withdraw'
                gardenToken = log['address']
                gardenAmount = Web3.from_wei(log['args']['value'], 'ether')
            elif log['args']['from'] == account:
                gardenEvent = 'deposit'
                gardenToken = log['address']
                gardenAmount = Web3.from_wei(log['args']['value'], 'ether')
    if gardenAmount > 0:
        r = records.GardenerTransaction(txn, network, timestamp, gardenEvent, gardenToken, gardenAmount)
        events.append(r)

    return events

def extractFarmResults(w3, txn, account, timestamp, receipt, network):
    # events record amount of rewards received when claiming at the farms
    ABI = getABI('ERC20')
    contract = w3.eth.contract(address='0x1f806f7C8dED893fd3caE279191ad7Aa3798E928', abi=ABI)
    events = []
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    farmEvent = ''
    farmToken = ''
    farmAmount = 0
    rewardEvent = ''
    rewardToken = ''
    rewardAmount = 0
    for log in decoded_logs:
        # Token Transfers
        if 'to' in log['args'] and 'from' in log['args']:
            if ('Tranq' in contracts.getAddressName(log['address']) or 'Pangolin LP' in contracts.getTokenName(log['address'], network)) and log['args']['to'] == account:
                farmEvent = 'withdraw'
                farmToken = log['address']
                farmAmount = Web3.from_wei(log['args']['value'], 'ether')
            if log['args']['to'] == account:
                rewardEvent = 'staking-reward'
                rewardToken = log['address']
                rewardAmount = Web3.from_wei(log['args']['value'], 'ether')
            elif ('Tranq' in contracts.getAddressName(log['address']) or 'Pangolin LP' in contracts.getTokenName(log['address'], network)) and log['args']['from'] == account:
                farmEvent = 'deposit'
                farmToken = log['address']
                farmAmount = Web3.from_wei(log['args']['value'], 'ether')
    if farmAmount > 0:
        r = records.GardenerTransaction(txn, network, timestamp, farmEvent, farmToken, farmAmount)
        events.append(r)
    if rewardAmount > 0:
        rr = records.GardenerTransaction(txn, network, timestamp, rewardEvent, rewardToken, rewardAmount)
        rewardPrice = prices.priceLookup(timestamp, rewardToken, network)
        rr.fiatValue = rewardPrice * rr.coinAmount
        events.append(rr)

    return events

def extractSwapResults(w3, txn, account, dex, timestamp, receipt, value, network):
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    ABI = getABI('Wrapped ONE')
    contract = w3.eth.contract(address='0xcF664087a5bB0237a0BAd6742852ec6c8d69A27a', abi=ABI)
    decoded_logs += contract.events.Withdrawal().process_receipt(receipt, errors=DISCARD)
    decoded_logs += contract.events.Deposit().process_receipt(receipt, errors=DISCARD)
    rcvdToken = []
    rcvdAmount = []
    sentToken = []
    sentAmount = []
    for log in decoded_logs:
        # Token Transfers
        if 'to' in log['args'] and 'from' in log['args']:
            # TODO - figure out what event is happening and decode it for what sends normal jewel to account after wrapped is burned
            if log['args']['to'] == account or (log['address'] == contracts.GAS_TOKENS[network] and log['args']['from'] == dex and log['args']['to'] == '0x0000000000000000000000000000000000000000'):
                rcvdToken.append(log['address'])
                rcvdAmount.append(contracts.valueFromWei(log['args']['value'], log['address'], network))
            elif log['args']['from'] == account or (log['address'] == contracts.GAS_TOKENS[network] and log['args']['to'] == dex and log['args']['from'] == '0x0000000000000000000000000000000000000000'):
                sentToken.append(log['address'])
                sentAmount.append(contracts.valueFromWei(log['args']['value'], log['address'], network))
            else:
                logging.debug('ignored swap log {0} to {1} not involving account'.format(log['args']['from'], log['args']['to']))
        # Native token transfers (src and dst also in args but not used yet)
        if 'wad' in log['args']:
            if log['event'] == 'Withdrawal':
                rcvdToken.append(log['address'])
                rcvdAmount.append(contracts.valueFromWei(log['args']['wad'], log['address'], network))
            if log['event'] == 'Deposit':
                sentToken.append(log['address'])
                sentAmount.append(contracts.valueFromWei(log['args']['wad'], log['address'], network))
    # when swapping gas for something else does not show up as transfer event from self
    if len(sentAmount) == 0 and value > 0:
        sentToken.append(contracts.GAS_TOKENS[network])
        sentAmount.append(value)
    if len(rcvdAmount) > 0 and rcvdAmount[0] > 0:
        if len(sentToken) == 1 and len(rcvdToken) == 1:
            # simple 1 coin in 1 coin out swaps
            r = records.TraderTransaction(txn, network, timestamp, sentToken[0], rcvdToken[0], sentAmount[0], rcvdAmount[0])
            fiatValues = getSwapFiatValues(timestamp, sentToken[0], sentAmount[0], rcvdToken[0], rcvdAmount[0], network)
            r.fiatSwapValue = fiatValues[0]
            r.fiatReceiveValue = fiatValues[1]
            return r
        elif len(sentToken) == 0 or len(rcvdToken) == 0:
            # just incase something weird shows up
            logging.error('wtf swap: {0}: sent-{1} rcvd-{2}'.format(txn, str(sentToken), str(rcvdToken)))
        else:
            # Others should be LP deposit/withdraws
            if len(sentToken) == 1 and len(rcvdToken) == 2:
                # if sending 1 and receiving 2, it is withdraw, sending LP tokens, rcv 2 currency
                logging.info('Liquidity withdraw event {2} send {0} rcvd {1}'.format(str(sentToken), str(rcvdToken), txn))
                r = records.LiquidityTransaction(txn, network, timestamp, 'withdraw', sentToken[0], sentAmount[0], rcvdToken[0], rcvdAmount[0], rcvdToken[1], rcvdAmount[1])
                fiatValues = getSwapFiatValues(timestamp, rcvdToken[0], rcvdAmount[0], rcvdToken[1], rcvdAmount[1], network)
                r.coin1FiatValue = fiatValues[0]
                r.coin2FiatValue = fiatValues[1]
                return r
            elif len(rcvdToken) == 1 and len(sentToken) == 2:
                # receiving LP tokens, sending 2 currencies is LP deposit
                logging.info('Liquidity deposit event {2} send {0} rcvd {1}'.format(str(sentToken), str(rcvdToken), txn))
                r = records.LiquidityTransaction(txn, network, timestamp, 'deposit', rcvdToken[0], rcvdAmount[0], sentToken[0], sentAmount[0], sentToken[1], sentAmount[1])
                fiatValues = getSwapFiatValues(timestamp, sentToken[0], sentAmount[0], sentToken[1], sentAmount[1], network)
                r.coin1FiatValue = fiatValues[0]
                r.coin2FiatValue = fiatValues[1]
                return r
            else:
                errStr = 'txn: {0}|'.format(txn)
                for i in range(len(sentToken)):
                    errStr += 'Sent {0} {1}|'.format(sentAmount[i], sentToken[i])
                for i in range(len(rcvdToken)):
                    errStr += 'Rcvd {0} {1}|'.format(rcvdAmount[i], rcvdToken[i])
                logging.error('Error: Unrecognized Swap combination: ' + errStr)

# Get data related to a bazaar transaction based on order Id
def getBazaarTx(orderId):
    query = """query {
        bazaarTransactions(
            where: { orderId: %s })
            {
                initiator { id }
                owner { id }
                quantity
                price
                side
                tokenAddress
                executedStamp
                txHash
                network
            }
        }
    """
    data = query % (orderId)
    graph_uri = "https://api.defikingdoms.com/graphql"
    try:
        r = requests.post(graph_uri, json={'query': data})
    except Exception as err:
        result = "Error: failed to get bazaar tx - {0}".format(str(err))

    if r.status_code == 200:
        result = r.json()
        if 'data' in result and 'bazaarTransactions' in result['data']:
            if len(result['data']['bazaarTransactions']) > 0:
                result = result['data']['bazaarTransactions'][0]
            else:
                result = "Error: no bazaar transaction found for OrderId {0}".format(orderId)
        else:
            result = str(result)
    else:
        result = "Error: failed to get bazaar transaction - {0} {1}".format(str(r.status_code), r.text)
    return result

def extractBazaarResults(w3, txn, account, bazaarAddress, timestamp, receipt, value, network):
    ABI = getABI('BazaarDiamond')
    contract = w3.eth.contract(address='0x902F2b740bC158e16170d57528405d7f2a793Ca2', abi=ABI)
    decoded_logs = contract.events.OrderExecuted().process_receipt(receipt, errors=DISCARD)
    if network == 'dfkchain':
        # jewel on dfkchain
        bazaarCurrency = '0xCCb93dABD71c8Dad03Fc4CE5559dC3D89F67a260'
    else:
        # unknown otherwise
        bazaarCurrency = ''

    rcvdToken = ''
    rcvdAmount = 0
    sentToken = ''
    sentAmount = 0
    for log in decoded_logs:
        orderId = log['args']['orderId']
        # owner of order is not available in Event, so we must lookup in API
        orderInfo = getBazaarTx(orderId)
        logging.info("order {0}: {1}".format(str(orderId), str(orderInfo)))
        if 'tokenAddress' in orderInfo:
            transactToken = Web3.to_checksum_address(orderInfo['tokenAddress'])
            if (orderInfo['owner']['id'] == account and orderInfo['side'] == 0) or (orderInfo['initiator']['id'] == account and orderInfo['side'] == 1):
                # our buy order initiated by someone else, or someone elses sell order initiated by us
                sentToken = bazaarCurrency
                sentAmount += int(orderInfo['quantity']) * decimal.Decimal(int(orderInfo['price'])/(10.0**30))
                rcvdToken = transactToken
                rcvdAmount += contracts.valueFromWei(int(orderInfo['quantity']), transactToken, network)
            elif (orderInfo['initiator']['id'] == account and orderInfo['side'] == 0) or (orderInfo['owner']['id'] == account and orderInfo['side'] == 1):
                # others buy order filled by us or our sell order someone else bought from
                sentToken = transactToken
                sentAmount += contracts.valueFromWei(int(orderInfo['quantity']), transactToken, network)
                rcvdToken = bazaarCurrency
                rcvdAmount += int(orderInfo['quantity']) * decimal.Decimal(int(orderInfo['price'])/(10.0**30))
            else:
                # If we are not initiator or owner then we were just part of a Tx with multiple fills including other sellers, ignore
                logging.info('Skipping OrderExecute log not involving wallet.')

    if rcvdToken != '' and sentToken != '':
        r = records.TraderTransaction(txn, network, timestamp, sentToken, rcvdToken, sentAmount, rcvdAmount)
        fiatValues = getSwapFiatValues(timestamp, sentToken, sentAmount, rcvdToken, rcvdAmount, network)
        r.fiatSwapValue = fiatValues[0]
        r.fiatReceiveValue = fiatValues[1]
        return r

# Lookup and return the fiat values given two tokens in a swap at a point in time
def getSwapFiatValues(timestamp, sentToken, sentAmount, rcvdToken, rcvdAmount, network):
    # Lookup price for normal tokens, but set direct value of both for fiat type coins
    if sentToken in contracts.fiatTypes['usd']:
        fiatSwapValue = decimal.Decimal(1.0) * sentAmount
        return [fiatSwapValue, fiatSwapValue]
    else:
        fiatSwapValue = prices.priceLookup(timestamp, sentToken, network) * sentAmount

    if rcvdToken in contracts.fiatTypes['usd']:
        fiatReceiveValue = decimal.Decimal(1.0) * rcvdAmount
        return [fiatReceiveValue, fiatReceiveValue]
    else:
        fiatReceiveValue = prices.priceLookup(timestamp, rcvdToken, network) * rcvdAmount

    return [fiatSwapValue, fiatReceiveValue]

def extractSummonResults(w3, txn, account, timestamp, receipt, network):
    # Get the summon costs data
    tearsAmount = decimal.Decimal(0.0)
    jewelAmount = decimal.Decimal(0.0)
    hiringProceeds = decimal.Decimal(0.0)
    hiredFromAccount = ''
    powerToken = contracts.POWER_TOKENS[network]
    tearsToken = contracts.GAIA_TEARS_TOKENS[network]
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.info('{3} transfer for summon from: {0} to: {1} value: {2}'.format(log['args']['from'], log['args']['to'], log['args']['value'], contracts.getTokenName(log['address'], network)))
        if log['address'] == powerToken:
            jewelAmount += Web3.from_wei(log['args']['value'], 'ether')
            # capture transfer amount to other player so we can create a record for thier gains
            if log['args']['to'] not in contracts.tx_fee_targets:
                hiringProceeds = Web3.from_wei(log['args']['value'], 'ether')
                hiredFromAccount = log['args']['to']
        else:
            tearsAmount += log['args']['value']

    ABI = getABI('HeroSummoningUpgradeable')
    r = None
    rc = None
    rs = None
    rt = None
    crystalId = 0
    bonusItem = ''
    summoner = 'unk'
    assistant = 'unk'
    decoded_logs = []
    contract = w3.eth.contract(address='0x65DEA93f7b886c33A78c10343267DD39727778c2', abi=ABI)
    decoded_logs = contract.events.CrystalSummoned().process_receipt(receipt, errors=DISCARD)
    decoded_logs += contract.events.CrystalDarkSummoned().process_receipt(receipt, errors=DISCARD)
    #EnhancementStoneAdded event
    for log in decoded_logs:
        logging.info('Summonning Crystal log: {0}'.format(log))
        if type(log['args']['generation']) is int:
            summoner = log['args']['summonerId']
            assistant = log['args']['assistantId']
            crystalId = log['args']['crystalId']
            if 'bonusItem' in log['args']:
                bonusItem = log['args']['bonusItem']
            elif 'enhancementStone' in log['args']:
                bonusItem = log['args']['enhancementStone']
            else:
                bonusItem = '0x0000000000000000000000000000000000000000'
            rc = records.TavernTransaction(txn, network, 'hero', '/'.join((str(summoner),str(assistant))), 'summon', timestamp, powerToken, jewelAmount)
            rc.fiatAmount = prices.priceLookup(timestamp, rc.coinType, network) * rc.coinCost
            r = records.TavernTransaction(txn, network, 'hero', '/'.join((str(summoner),str(assistant))), 'crystal', timestamp, tearsToken, int(tearsAmount))
            r.fiatAmount = prices.priceLookup(timestamp, r.coinType, network) * r.coinCost
            if bonusItem != '0x0000000000000000000000000000000000000000':
                rt = records.TavernTransaction(txn, network, 'hero', '/'.join((str(summoner),str(assistant))), 'enhance', timestamp, bonusItem, 1)
                rt.fiatAmount = prices.priceLookup(timestamp, bonusItem, network)
            logging.info('{3} Summon Crystal event {0} jewel/{1} tears {2} gen result'.format(jewelAmount, tearsAmount, log['args']['generation'], txn))

    if hiredFromAccount != '':
        logging.info('{0} Summoning hire: {1}'.format(hiredFromAccount, hiringProceeds))
        # Saves record of owner of hired hero gaining proceeds from hire
        hiredHero = assistant
        rs = records.TavernTransaction(txn, network, 'hero', hiredHero, 'hire', timestamp, powerToken, hiringProceeds)
        rs.fiatAmount = prices.priceLookup(timestamp, rs.coinType, network) * rs.coinCost
        rs.seller = hiredFromAccount
        logging.info('Hero hired {0} for {1}'.format(rs.coinCost, rs.itemID))

    decoded_logs = contract.events.CrystalOpen().process_receipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.info('{3} crystal open {0} hero {1} for {2}'.format(log['args']['crystalId'], log['args']['heroId'], log['args']['owner'], txn))
        return [log['args']['crystalId'], log['args']['heroId']]

    return [crystalId, [r, rc, rs, rt]]

def extractMeditationResults(w3, txn, account, timestamp, receipt, network):
    # Get the meditation costs data
    runeAmount = decimal.Decimal(0.0)
    runeCost = decimal.Decimal(0.0)
    ptAmount = decimal.Decimal(0.0)
    ptAddress = ''
    runeAddress = ''
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        if log['address'] == contracts.POWER_TOKENS[network]:
            ptAmount += Web3.from_wei(log['args']['value'], 'ether')
            ptAddress = log['address']
        elif log['address'] in contracts.RUNE_TOKENS[network]:
            runeAmount += log['args']['value']
            runeAddress = log['address']
            runeCost += prices.priceLookup(timestamp, log['address'], network) * log['args']['value']

    ABI = getABI('MeditationCircle')
    contract = w3.eth.contract(address='0x0594D86b2923076a2316EaEA4E1Ca286dAA142C1', abi=ABI)
    complete_logs = contract.events.MeditationBegun().process_receipt(receipt, errors=DISCARD)
    r = None
    rs = None
    rt = None
    heroID = None
    for log in complete_logs:
        heroID = log['args']['heroId']
        crystal = log['args']['attunementCrystal']
        if type(heroID) is int:
            rs = records.TavernTransaction(txn, network, 'hero', heroID, 'levelup', timestamp, ptAddress, ptAmount)
            rs.fiatAmount = prices.priceLookup(timestamp, rs.coinType, network) * rs.coinCost
            r = records.TavernTransaction(txn, network, 'hero', heroID, 'meditate', timestamp, runeAddress, int(runeAmount))
            r.fiatAmount = runeCost
            if crystal != '0x0000000000000000000000000000000000000000':
                rt = records.TavernTransaction(txn, network, 'hero', heroID, 'enhance', timestamp, crystal, 1)
                rt.fiatAmount = prices.priceLookup(timestamp, crystal, network)
            logging.info('{3} Meditation event {0} power token/{1} runes {2} heroid'.format(ptAmount, runeAmount, heroID, txn))
    return [r, rs, rt]

def extractAuctionResults(w3, txn, account, timestamp, receipt, auctionType, network):
    # Get the seller data
    auctionSeller = ""
    auctionToken = ""
    sellerProceeds = decimal.Decimal(0.0)
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.debug('Jewel transfer for auction from: {0} to: {1} value: {2}'.format(log['args']['from'], log['args']['to'], log['args']['value']))
        if log['args']['to'] not in contracts.tx_fee_targets:
            auctionSeller = log['args']['to']
            auctionToken = log['address']
            sellerProceeds = Web3.from_wei(log['args']['value'], 'ether')

    ABI = getABI('SaleAuction')
    contract = w3.eth.contract(address='0x13a65B9F8039E2c032Bc022171Dc05B30c3f2892', abi=ABI)
    decoded_logs = contract.events.AuctionSuccessful().process_receipt(receipt, errors=DISCARD)
    r = None
    rs = None
    for log in decoded_logs:
        auctionPrice = Web3.from_wei(log['args']['totalPrice'], 'ether')
        logging.info("  {2}  Bought {3} {0} for {1} jewel".format(log['args']['tokenId'], auctionPrice, log['args']['winner'], auctionType))
        if log['args']['winner'] == account:
            r = records.TavernTransaction(txn, network, auctionType, log['args']['tokenId'], 'purchase', timestamp, auctionToken, auctionPrice)
            r.fiatAmount = prices.priceLookup(timestamp, auctionToken, network) * r.coinCost

        if auctionSeller != "":
            logging.info("  {2}  Sold {3} {0} for {1} jewel".format(log['args']['tokenId'], auctionPrice, auctionSeller, auctionType))
            rs = records.TavernTransaction(txn, network, auctionType, log['args']['tokenId'], 'sale', timestamp, auctionToken, sellerProceeds)
            rs.fiatAmount = prices.priceLookup(timestamp, auctionToken, network) * rs.coinCost
            rs.seller = auctionSeller
    return [r, rs]

def extractAirdropResults(w3, txn, account, timestamp, receipt, network, source='from'):
    # Create record of the airdrop tokens received
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    rcvdTokens = {}
    results = []
    address = source
    for log in decoded_logs:
        # Token Transfers
        if 'to' in log['args'] and 'from' in log['args']:
            if log['args']['to'] == account:
                address = log['args']['from']
                if log['address'] in rcvdTokens:
                    rcvdTokens[log['address']] += contracts.valueFromWei(log['args']['value'], log['address'], network)
                else:
                    rcvdTokens[log['address']] = contracts.valueFromWei(log['args']['value'], log['address'], network)
            elif log['args']['from'] == account:
                address = log['args']['to']
                if log['address'] in rcvdTokens:
                    rcvdTokens[log['address']] += contracts.valueFromWei(log['args']['value'], log['address'], network)
                else:
                    rcvdTokens[log['address']] = contracts.valueFromWei(log['args']['value'], log['address'], network)
            else:
                logging.info('ignored airdrop log {0} to {1} not involving account'.format(log['args']['from'], log['args']['to']))
    # If some address was passed in, override source address with it instead of using from/to
    if source != 'from':
        address = source
    for k, v in rcvdTokens.items():
        logging.info('AirdropClaimed: {0} {1}'.format(v, k))
        r = records.AirdropTransaction(txn, network, timestamp, address, k, v)
        r.fiatValue = prices.priceLookup(timestamp, k, network) * r.tokenAmount
        results.append(r)
    return results

def extractQuestResults(w3, txn, timestamp, receipt, address, network):
    v3_logs = []
    v2_logs = []
    if address == '0x5100Bd31b822371108A0f63DCFb6594b9919Eaf4':
        # Legacy quest contract version only used on old harmony quest core
        ABI = getABI('QuestCoreV2')
        contract = w3.eth.contract(address='0x5100Bd31b822371108A0f63DCFb6594b9919Eaf4', abi=ABI)
        v2_logs = contract.events.QuestReward().process_receipt(receipt, errors=DISCARD)
    else:
        ABI = getABI('QuestCoreV3')
        contract = w3.eth.contract(address='0xAa9a289ce0565E4D6548e63a441e7C084E6B52F6', abi=ABI)
        v3_logs = contract.events.RewardMinted().process_receipt(receipt, errors=DISCARD)
        v2_logs = contract.events.QuestReward().process_receipt(receipt, errors=DISCARD)

    rewardTotals = {}
    txns = []
    for log in v3_logs:
        if 'amount' in log['args'] and 'reward' in log['args'] and log['args']['reward'] != '0x0000000000000000000000000000000000000000':
            # Keep a running total of each unique reward item in this quest result
            rewardQuantity = contracts.valueFromWei(log['args']['amount'], log['args']['reward'], network)
            logging.info('    Hero {2} on quest {3} got reward of {0} {1}'.format(rewardQuantity, contracts.getTokenName(log['args']['reward'], network), log['args']['heroId'], log['args']['questId']))
            if log['args']['reward'] in rewardTotals:
                rewardTotals[log['args']['reward']] += rewardQuantity
            else:
                rewardTotals[log['args']['reward']] = rewardQuantity
    for log in v2_logs:
        if 'itemQuantity' in log['args'] and 'rewardItem' in log['args'] and log['args']['rewardItem'] != '0x0000000000000000000000000000000000000000':
            # Keep a running total of each unique reward item in this quest result
            rewardQuantity = contracts.valueFromWei(log['args']['itemQuantity'], log['args']['rewardItem'], network)
            rewardName = contracts.getTokenName(log['args']['rewardItem'], network)
            if log['args']['rewardItem'] != rewardName:
                logging.info('    Hero {2} on quest {3} got reward of {0} {1}'.format(rewardQuantity, rewardName, log['args']['heroId'], log['args']['questId']))
                if log['args']['rewardItem'] in rewardTotals:
                    rewardTotals[log['args']['rewardItem']] += rewardQuantity
                else:
                    rewardTotals[log['args']['rewardItem']] = rewardQuantity
            else:
                logging.info('    Hero {2} on quest {3} got reward of {0} unknown({1})'.format(rewardQuantity, log['args']['rewardItem'], log['args']['heroId'], log['args']['questId']))
    for k, v in rewardTotals.items():
        r = records.QuestTransaction(txn, network, timestamp, k, v)
        r.fiatValue = prices.priceLookup(timestamp, k, network) * v
        txns.append(r)
    return txns

def extractAlchemistResults(w3, txn, account, timestamp, receipt, network):
    # Create record of the alchemist crafting activity with total costs
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    rcvdToken = []
    rcvdAmount = []
    sentToken = []
    sentAmount = []
    r = None
    for log in decoded_logs:
        # Token Transfers
        if 'to' in log['args'] and 'from' in log['args']:
            if log['args']['to'] == account:
                rcvdToken.append(log['address'])
                rcvdAmount.append(contracts.valueFromWei(log['args']['value'], log['address'], network))
            elif log['args']['from'] == account:
                sentToken.append(log['address'])
                sentAmount.append(contracts.valueFromWei(log['args']['value'], log['address'], network))
            else:
                logging.debug('ignored alchemist log {0} to {1} not involving account'.format(log['args']['from'], log['args']['to']))
    # Total up value of all ingredients
    ingredientList = ''
    ingredientValue = 0
    for i in range(len(sentToken)):
        ingredientName = contracts.getTokenName(sentToken[i], network)
        ingredientList += '{0}x{1}, '.format(ingredientName, sentAmount[i])
        ingredientValue += prices.priceLookup(timestamp, sentToken[i], network) * sentAmount[i]
    if len(ingredientList) > 1:
        ingredientList = ingredientList[:-2]
    # should be just 1 thing received, the potion, create the record if so
    if len(rcvdToken) == 1:
        r = records.AlchemistTransaction(txn, network, timestamp, rcvdToken[0], rcvdAmount[0])
        r.fiatValue = prices.priceLookup(timestamp, rcvdToken[0], network)
        r.craftingCosts = ingredientList
        r.costsFiatValue = ingredientValue
    else:
        logging.error('Failed to add alchemist record, wrong token rcvd {0}'.format(txn))
    return r

def extractPotionResults(w3, txn, account, timestamp, receipt, inputs, network):
    r = None
    # Determine hero that is consuming potion from tx input
    ABI = '[{"inputs":[{"internalType":"address","name":"_address","type":"address"},{"internalType":"uint256","name":"heroId","type":"uint256"}],"name":"consumeItem","outputs":[],"stateMutability":"view","type":"function"}]'
    contract = w3.eth.contract(address='0x38e76972BD173901B5E5E43BA5cB464293B80C31', abi=ABI)
    input_data = contract.decode_function_input(inputs)
    logging.info(str(input_data))
    heroId = input_data[1]['heroId']

    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    consumedItem = ''
    consumedCount = 0
    for log in decoded_logs:
        if log['args']['from'] == account:
            consumedItem = log['address']
            consumedCount = log['args']['value']
    if consumedItem != '':
        r = records.TavernTransaction(txn, network, 'hero', heroId, 'consume', timestamp, consumedItem, consumedCount)
        r.fiatAmount = prices.priceLookup(timestamp, consumedItem, network) * consumedCount

    return r

def extractJourneyResults(w3, txn, account, timestamp, receipt, inputs, network):
    # Perilous Journey - record dead heroes in tavern transactions with rewards
    ABI = getABI('PerilousJourney')
    contract = w3.eth.contract(address='0xE92Db3bb6E4B21a8b9123e7FdAdD887133C64bb7', abi=ABI)
    input_data = contract.decode_function_input(inputs)
    logging.info(str(input_data))
    rewards = []
    perishedHeroRewards = {}
    # HeroClaimed event contains jewel/crystal rewards
    decoded_logs = contract.events.HeroClaimed().process_receipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.info(log)
        if log['args']['player'] == account and log['args']['heroSurvived'] == False:
            perishedHeroRewards[log['args']['heroId']] = {contracts.JEWEL_ADDRESSES[network]: contracts.valueFromWei(log['args']['jewelAmount'], contracts.JEWEL_ADDRESSES[network], network)}
    # JourneyReward event contains other rewards runes/stones/crystals
    decoded_logs = contract.events.JourneyReward().process_receipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.info(log)
        if log['args']['heroId'] in perishedHeroRewards:
            perishedHeroRewards[log['args']['heroId']][log['args']['rewardItem']] = log['args']['itemQuantity']

    for k, v in perishedHeroRewards.items():
        for k2, v2 in v.items():
            r = records.TavernTransaction(txn, network, 'hero', k, 'perished', timestamp, k2, v2)
            r.fiatAmount = prices.priceLookup(timestamp, k2, network) * v2
            rewards.append(r)

    return rewards

def extractHatchingResults(w3, txn, account, timestamp, receipt, network):
    # Record egg hatching costs and pet nft gains
    jewelAmount = decimal.Decimal(0.0)
    otherCosts = {}
    powerToken = contracts.POWER_TOKENS[network]
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.debug('{3} transfer for incubate from: {0} to: {1} value: {2}'.format(log['args']['from'], log['args']['to'], log['args']['value'], contracts.getTokenName(log['address'], network)))
        if log['address'] == powerToken:
            jewelAmount += Web3.from_wei(log['args']['value'], 'ether')
        else:
            otherCosts[log['address']] = contracts.valueFromWei(log['args']['value'], log['address'], network)

    r = None
    eggId = 0
    ABI = getABI('PetHatching')
    contract = w3.eth.contract(address='0x564D03ccF4A9634D97100Ec18d7770A3C4E45541', abi=ABI)
    incubate_logs = contract.events.EggIncubated().process_receipt(receipt, errors=DISCARD)
    
    for log in incubate_logs:
        logging.info('Incubate Egg log: {0}'.format(log))
        if type(log['args']['eggId']) is int:
            eggId = log['args']['eggId']
            r = records.TavernTransaction(txn, network, 'pet', log['args']['eggType'], 'incubate', timestamp, powerToken, int(jewelAmount))
            r.fiatAmount = prices.priceLookup(timestamp, r.coinType, network) * r.coinCost
            logging.info('{2} Incubate Egg event {0} jewel {1} type {3} tier'.format(jewelAmount, log['args']['eggType'], txn, log['args']['tier']))

    crack_logs = contract.events.EggCracked().process_receipt(receipt, errors=DISCARD)
    for log in crack_logs:
        if type(log['args']['eggId']) is int:
            eggId = log['args']['eggId']
            r = records.TavernTransaction(txn, network, 'pet', log['args']['petId'], 'crack', timestamp, '', 0)
            logging.info('{3} egg crack {0} pet {1} for {2}'.format(log['args']['eggId'], log['args']['petId'], log['args']['owner'], txn))

    return [eggId, r, otherCosts]

def extractPetBurnResults(w3, txn, account, timestamp, receipt, network):
    # Pet trade in - record pastured pets in tavern transactions with rewards
    ABI = getABI('PetExchange')
    contract = w3.eth.contract(address='0xeaF833A0Ae97897f6F69a728C9c17916296cecCA', abi=ABI)
    r1 = None
    r2 = None
    # create one record for each pet burned with egg reward on first one
    decoded_logs = contract.events.PetExchangeCompleted().process_receipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        r1 = records.TavernTransaction(txn, network, 'pet', log['args']['eggId1'], 'perished', timestamp, contracts.EGG_TOKENS[network][log['args']['eggTypeRecieved']], 1)
        r1.fiatAmount = prices.priceLookup(timestamp, contracts.EGG_TOKENS[network][log['args']['eggTypeRecieved']], network)
        r2 = records.TavernTransaction(txn, network, 'pet', log['args']['eggId2'], 'perished', timestamp, '', 0)

    return [r1, r2]

def extractDFKDuelResults(w3, txn, account, timestamp, receipt, inputs, network):
    # Create record of the duel activity with total costs and rewards
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    rcvdToken = []
    rcvdAmount = []
    sentToken = []
    sentAmount = []
    r = None
    for log in decoded_logs:
        # Token Transfers
        if 'to' in log['args'] and 'from' in log['args']:
            if log['args']['to'] == account and log['address'] == contracts.RAFFLE_TIX_TOKENS[network]:
                rcvdToken.append(log['address'])
                rcvdAmount.append(contracts.valueFromWei(log['args']['value'], log['address'], network))
            elif log['args']['from'] == account and log['address'] == contracts.POWER_TOKENS[network]:
                sentToken.append(log['address'])
                sentAmount.append(contracts.valueFromWei(log['args']['value'], log['address'], network))
            else:
                logging.debug('ignored duel log {0} to {1} not involving account'.format(log['args']['from'], log['args']['to']))

    ABI = getABI('DFKDuel')
    contract = w3.eth.contract(address='0xE97196f4011dc9DA0829dd8E151EcFc0f37EE3c7', abi=ABI)
    duelId = -1
    entryId = -1
    try:
        input_data = contract.decode_function_input(inputs)
        logging.info(input_data)
        if '_duelId' in input_data[1]:
            duelId = input_data[1]['_duelId']
    except Exception as err:
        logging.error('Failed to decode DFKDuel input data tx {0}: {1}'.format(txn, err))
    # TODO maybe account for the gold too, seems minimal as winner gets it back anyway
    # if received items, it was pvp complete rewards, otherwise initiation costs/fees
    if len(rcvdToken) > 0:
        r = records.TavernTransaction(txn, network, 'hero', duelId, 'pvpreward', timestamp, rcvdToken[0], rcvdAmount[0])
        r.fiatValue = prices.priceLookup(timestamp, rcvdToken[0], network)
    elif len(sentToken) > 0:
        decoded_logs = contract.events.DuelEntryCreated().process_receipt(receipt, errors=DISCARD)
        for log in decoded_logs:
            entryId = log['args']['id']
        r = records.TavernTransaction(txn, network, 'hero', entryId, 'pvpfee', timestamp, sentToken[0], sentAmount[0])
        r.fiatValue = prices.priceLookup(timestamp, sentToken[0], network)
    return r

def extractBridgeResults(w3, txn, account, timestamp, receipt, network):
    # Record token bridging as a wallet event
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    r = None
    for log in decoded_logs:
        if log['args']['to'] != '0x0000000000000000000000000000000000000000' and log['args']['from'] == account:
            otherAddress = log['args']['to']
        elif log['args']['from'] != '0x0000000000000000000000000000000000000000' and log['args']['to'] == account:
            otherAddress = log['args']['from']
        else:
            logging.info('{3} ignoring token transfer not from/to account from {0} to {1} value {2}'.format(log['args']['from'], log['args']['to'], log['args']['value'], txn))
            continue
        tokenValue = contracts.valueFromWei(log['args']['value'], log['address'], network)
        tokenName = contracts.getTokenName(log['address'], network)
        if tokenValue > 0:
            logging.info('{3} wallet bridge from: {0} to: {1} value: {2}'.format(log['args']['from'], log['args']['to'], tokenValue, tokenName))
            r = records.walletActivity(txn, network, timestamp, 'bridge', otherAddress, log['address'], tokenValue)
            r.fiatValue = prices.priceLookup(timestamp, r.coinType, network) * tokenValue
    return r

def extractLendingResults(w3, txn, account, timestamp, receipt, network, value):
    # Create record of the lending events
    sentToken = ''
    sentValue = 0
    rcvdToken = ''
    ABI = getABI('TqErc20Delegator')
    contract = w3.eth.contract(address='0xCa3e902eFdb2a410C952Fd3e4ac38d7DBDCB8E96', abi=ABI)
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        if log['args']['from'] == account:
            sentToken = log['address']
            sentValue = contracts.valueFromWei(log['args']['amount'], sentToken, network)
        elif  log['args']['to'] == account:
            rcvdToken = log['address']
    if rcvdToken == '':
        rcvdToken = contracts.GAS_TOKENS[network]
    if sentToken == '' and value > 0:
        ABI = getABI('TqOne')
        contract = w3.eth.contract(address='0x34B9aa82D89AE04f0f546Ca5eC9C93eFE1288940', abi=ABI)
        sentToken = contracts.GAS_TOKENS[network]
        sentValue = value

    r = None
    ri = None
    decoded_logs = contract.events.RepayBorrow().process_receipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.info('Pay back {0} of borrow, remaining borrow is now {1} {2} total borrows {3}'.format(contracts.valueFromWei(log['args']['repayAmount'], sentToken, network), contracts.valueFromWei(log['args']['accountBorrows'], sentToken, network), contracts.getTokenName(log['address'], network), contracts.valueFromWei(log['args']['totalBorrows'], sentToken, network)))
        r = records.LendingTransaction(txn, network, timestamp, 'repay', log['address'], sentToken, sentValue)
        r.fiatValue = prices.priceLookup(timestamp, sentToken, network) * sentValue
    decoded_logs = contract.events.Borrow().process_receipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.info('Borrowed {0} {1} account borrowed is now {2} total borrowed is {3}'.format(contracts.valueFromWei(log['args']['borrowAmount'], rcvdToken, network), contracts.getTokenName(log['address'], network), contracts.valueFromWei(log['args']['accountBorrows'], rcvdToken, network), contracts.valueFromWei(log['args']['totalBorrows'], rcvdToken, network)))
        r = records.LendingTransaction(txn, network, timestamp, 'borrow', log['address'], rcvdToken, contracts.valueFromWei(log['args']['borrowAmount'], rcvdToken, network))
        r.fiatValue = prices.priceLookup(timestamp, rcvdToken, network) * contracts.valueFromWei(log['args']['borrowAmount'], rcvdToken, network)
    # TODO figure out interest, the event seems to show in interest accumulated that is unrelated to the borrow being repaid, maybe global for user or contract
    #decoded_logs = contract.events.AccrueInterest().process_receipt(receipt, errors=DISCARD)

    # Redeem is pulling money out of lending, looks like sending tqONE, getting ONE
    decoded_logs = contract.events.Redeem().process_receipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.info('Redeemed {0} {1} for {2} tq tokens'.format(contracts.valueFromWei(log['args']['redeemAmount'], rcvdToken, network), contracts.getTokenName(log['address'], network), log['args']['redeemTokens']))
        r = records.LendingTransaction(txn, network, timestamp, 'redeem', log['address'], rcvdToken, contracts.valueFromWei(log['args']['redeemAmount'], rcvdToken, network))
        r.fiatValue = prices.priceLookup(timestamp, rcvdToken, network) * contracts.valueFromWei(log['args']['redeemAmount'], rcvdToken, network)
    # Mint is Putting money up for lending, looks like sending token and geting tq tokens back
    decoded_logs = contract.events.Mint().process_receipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.info('Lended {0} {1} rcvd {2} tq tokens'.format(contracts.valueFromWei(log['args']['mintAmount'], sentToken, network), contracts.getTokenName(log['address'], network), log['args']['mintTokens']))
        r = records.LendingTransaction(txn, network, timestamp, 'lend', log['address'], sentToken, sentValue)
        r.fiatValue = prices.priceLookup(timestamp, sentToken, network) * sentValue
    decoded_logs = contract.events.LiquidateBorrow().process_receipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.info('Liquidate {0} {3} of borrow, seized {1} {2}'.format(contracts.valueFromWei(log['args']['repayAmount'], sentToken, network), contracts.valueFromWei(log['args']['seizeTokens'], log['args']['tqTokenCollateral'], network), contracts.getTokenName(log['args']['tqTokenCollateral'], network), contracts.getTokenName(rcvdToken, network)))
        r = records.LendingTransaction(txn, network, timestamp, 'liquidate', log['address'], sentToken, sentValue)
        r.fiatValue = prices.priceLookup(timestamp, sentToken, network) * sentValue
        # TODO resolve - seize assets are received as actively lended, so cannot determine value until redeem is done
        #ri = records.LendingTransaction(txn, network, timestamp, 'seize', log['address'], rcvdToken, valueFromWei(log['args']['seizeTokens'], log['args']['tqTokenCollateral'], network))
        #ri.fiatValue = prices.priceLookup(timestamp, rcvdToken, network)

    return [r, ri]


def extractTokenResults(w3, txn, account, timestamp, receipt, depositEvent, withdrawalEvent, network):
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().process_receipt(receipt, errors=DISCARD)
    transfers = []
    for log in decoded_logs:
        if log['args']['from'] == account:
            event = withdrawalEvent
            otherAddress = log['args']['to']
        elif log['args']['to'] == account:
            event = depositEvent
            otherAddress = log['args']['from']
        else:
            logging.info('{3} ignoring token transfer not from/to account from {0} to {1} value {2}'.format(log['args']['from'], log['args']['to'], log['args']['value'], txn))
            continue
        tokenValue = contracts.valueFromWei(log['args']['value'], log['address'], network)

        if tokenValue > 0:
            logging.info('{3} wallet transfer from: {0} to: {1} value: {2}'.format(log['args']['from'], log['args']['to'], tokenValue, contracts.getTokenName(log['address'], network)))
            r = records.walletActivity(txn, network, timestamp, event, otherAddress, log['address'], tokenValue)
            r.fiatValue = prices.priceLookup(timestamp, r.coinType, network) * tokenValue
            transfers.append(r)
        else:
            logging.info('zero value wallet transfer ignored')
    return transfers

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    w3 = Web3(Web3.HTTPProvider(nets.dfk_web3))
    tx = '0x01b32a38595e9cd9fae86ef7ebd8efea9b1dca68dc1e64bd978e04f0c71d5ab8'
    #tx = '0x118f64f5e663a066159beb4e177dda70284edd73ba4244e95c776d32a1359957'
    #tx = '0x715200f3bb4bfde6029da0cc9396fb243d8a6bc4ab17d9acf3d85b61d285a338'
    result = w3.eth.get_transaction(tx)
    action = lookupEvent(result['from'], result['to'], '0xC49601fe84fA58ec4B05E5d51F9054977692cB73')
    value = Web3.from_wei(result['value'], 'ether')
    block = result['blockNumber']
    receipt = w3.eth.get_transaction_receipt(tx)
    results = extractBazaarResults(w3, tx, '0xB9824c4cf87de16ee4a446B36e2450cdEf37D611', result['to'], 1676614935, receipt, value, 'dfkchain')
    print(str(results.__dict__))