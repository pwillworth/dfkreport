#!/usr/bin/env python3
import os
from web3 import Web3
from web3.logs import STRICT, IGNORE, DISCARD, WARN
import nets
import contracts
import records
import prices
import db
import settings
import datetime
import time
import decimal
import jsonpickle
import logging

def EventsMap():
    return {
        'tavern': [],
        'swaps': [],
        'liquidity': [],
        'wallet': [],
        'bank': [],
        'gardens': [],
        'quests': [],
        'alchemist': [],
        'airdrops': [],
        'gas': 0
    }

def getABI(contractName):
    location = os.path.abspath(__file__)
    with open('{0}/abi/{1}.json'.format('/'.join(location.split('/')[0:-1]), contractName), 'r') as f:
        ABI = f.read()
    return ABI

def checkTransactions(txs, account, startDate, endDate, network, alreadyComplete=0):
    events_map = EventsMap()

    # Connect to right network that txs are for
    if network == 'avalanche':
        w3 = Web3(Web3.HTTPProvider(nets.avax_web3))
    else:
        w3 = Web3(Web3.HTTPProvider(nets.hmy_web3))

    if not w3.isConnected():
        logging.error('Error: Critical w3 connection failure for {0}'.format(network))
        return 'Error: Blockchain connection failure.'

    txCount = 0
    summonCrystalStorage = [None, None, None]
    heroIdStorage = None
    heroIdTx = None
    heroCrystals = {}
    for txn in txs:
        # The AVAX list data includes the whole transaction, but harmony is just the hash
        if network == 'avalanche':
            tx = txn['hash']
            timestamp = int(txn['timeStamp'])
        else:
            tx = txn
        eventsFound = False
        # Update report tracking record for status every 10 txs
        if txCount % 10 == 0:
            try:
                db.updateReport(account, datetime.datetime.strftime(startDate, '%Y-%m-%d'), datetime.datetime.strftime(endDate, '%Y-%m-%d'), 'complete', alreadyComplete + txCount)
            except Exception as err:
                logging.error('Failed to update tx count {0}'.format(str(err)))

        if settings.USE_CACHE:
            checkCache = db.findTransaction(str(tx), account)
            if checkCache != None:
                # if event data is empty it is just record with no events we care about and in the db so we dont have to parse blockchain again
                if checkCache[3] != '':
                    events = jsonpickle.decode(checkCache[3])
                    if type(events) is list:
                        for evt in events:
                            evt.txHash = tx
                            events_map[checkCache[2]].append(evt)
                    else:
                        # cache records saved before feb 2022 did not have txHash property
                        events.txHash = tx
                        events_map[checkCache[2]].append(events)
                txCount += 1
                continue
        try:
            # sometimes they just don't exist yet
            result = w3.eth.get_transaction(tx)
        except Exception as err:
            logging.error('Got failed to get transaction {0} {1}'.format(tx, str(err)))
            time.sleep(1)
            continue
        action = lookupEvent(result['from'], result['to'], account)
        value = Web3.fromWei(result['value'], 'ether')
        block = result['blockNumber']
        if network != 'avalanche':
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
        gas = Web3.fromWei(receipt['gasUsed'], 'gwei')
        if blockDate >= startDate and blockDate <= endDate:
            events_map['gas'] += gas
        results = None
        if receipt['status'] == 1:
            logging.info("{5}:{4} | {3}: {0} - {1} - {2}".format(action, '{:f} value'.format(value), '{:f} gas'.format(gas), tx, datetime.datetime.fromtimestamp(timestamp).isoformat(), network))
            if 'Quest' in action and result['input'] != '0x':
                results = extractQuestResults(w3, tx, timestamp, receipt)
                if len(results) > 0:
                    events_map['quests'] += results
                    eventsFound = True
                    if settings.USE_CACHE:
                        db.saveTransaction(tx, timestamp, 'quests', jsonpickle.encode(results), account)
                else:
                    logging.info('{0} quest with no rewards.'.format(tx))
            elif 'AuctionHouse' in action:
                results = extractAuctionResults(w3, tx, account, timestamp, receipt, 'hero')
                if results != None and results[0] != None:
                    events_map['tavern'].append(results[0])
                    eventsFound = True
                    if settings.USE_CACHE:
                        db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[0]), account)
                else:
                    logging.info('Ignored an auction interaction, probably listing.')
                # Second record is to be saved in db and will be looked up when seller runs thier tax report
                # All of these get populated by running a report for the Tavern Address though, so we need to
                # skip if record has already been created.
                if results != None and results[1] != None and db.findTransaction(tx, results[1].seller) == None:
                    db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[1]), results[1].seller)
            elif 'LandAuction' in action:
                results = extractAuctionResults(w3, tx, account, timestamp, receipt, 'land')
                if results != None and results[0] != None:
                    events_map['tavern'].append(results[0])
                    eventsFound = True
                    if settings.USE_CACHE:
                        db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[0]), account)
                else:
                    logging.info('Ignored an auction interaction, probably listing.')
                # Second record is to be saved in db and will be looked up when seller runs thier tax report
                # All of these get populated by running a report for the Tavern Address though, so we need to
                # skip if record has already been created.
                if results != None and results[1] != None and db.findTransaction(tx, results[1].seller) == None:
                    db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[1]), results[1].seller)
            elif 'Uniswap' in action:
                results = extractSwapResults(w3, tx, account, timestamp, receipt, network)
                if results != None:
                    if type(results) is records.TraderTransaction:
                        events_map['swaps'].append(results)
                        eventsFound = True
                        if settings.USE_CACHE:
                            db.saveTransaction(tx, timestamp, 'swaps', jsonpickle.encode(results), account)
                    elif type(results) is records.LiquidityTransaction:
                        events_map['liquidity'].append(results)
                        eventsFound = True
                        if settings.USE_CACHE:
                            db.saveTransaction(tx, timestamp, 'liquidity', jsonpickle.encode(results), account)
                else:
                    logging.error('Error: Failed to parse a swap result. {0}'.format('not needed'))
            elif 'Gardener' in action:
                results = extractGardenerResults(w3, tx, account, timestamp, receipt)
                if results != None and len(results) > 0:
                    for item in results:
                        events_map['gardens'].append(item)
                        eventsFound = True
                    if settings.USE_CACHE:
                        db.saveTransaction(tx, timestamp, 'gardens', jsonpickle.encode(results), account)
                else:
                    logging.error('Error: Failed to parse a Gardener LP Pool result. tx {0}'.format(tx))
            elif 'Farms' in action:
                results = extractFarmResults(w3, tx, account, timestamp, receipt)
                if results != None and len(results) > 0:
                    for item in results:
                        events_map['gardens'].append(item)
                        eventsFound = True
                    if settings.USE_CACHE:
                        db.saveTransaction(tx, timestamp, 'gardens', jsonpickle.encode(results), account)
                else:
                    logging.error('Error: Failed to parse a Gardener LP Pool result. tx {0}'.format(tx))
            elif 'Airdrop' in action:
                results = extractAirdropResults(w3, tx, account, timestamp, receipt)
                for item in results:
                    events_map['airdrops'].append(item)
                    eventsFound = True
                if settings.USE_CACHE and len(results) > 0:
                    db.saveTransaction(tx, timestamp, 'airdrops', jsonpickle.encode(results), account)
            elif 'Payment Service' in action:
                # Some payment distributions do not get associated to users wallet, so populate record in db for recipient
                # these transactions are discovered by block crawler
                results = extractAirdropResults(w3, tx, account, timestamp, receipt)
                for item in results:
                    recipientAccount = ''
                    for item in results:
                        if recipientAccount not in ['', item.address]:
                            logging.error('Bailing from multi recipient payment {0}'.format(tx))
                            continue
                        recipientAccount = item.address
                        item.address = result['from']
                    if recipientAccount != '' and db.findTransaction(tx, recipientAccount) == None:
                        db.saveTransaction(tx, timestamp, 'airdrops', jsonpickle.encode(results), recipientAccount)
            elif 'Banker' in action:
                logging.info('Banker interaction, probably just claim which distributes to bank, no events to record. {0}'.format(tx))
            elif result['input'] != '0x' and 'xJewel' in action:
                results = extractBankResults(w3, tx, account, timestamp, receipt)
                if results != None:
                    events_map['bank'].append(results)
                    eventsFound = True
                    if settings.USE_CACHE:
                        db.saveTransaction(tx, timestamp, 'bank', jsonpickle.encode(results), account)
                else:
                    # if no bank result was parsed, it is just a direct xJewel transfer
                    logging.error('Error: Failed to parse a bank result.')
                    with open('abi/xJewel.json', 'r') as f:
                        ABI = f.read()
                    contract = w3.eth.contract(address='0xA9cE83507D872C5e1273E745aBcfDa849DAA654F', abi=ABI)
                    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
                    for log in decoded_logs:
                        logging.info('banklog: ' + str(log))
            elif 'Vendor' in action:
                logging.debug('Vendor activity: {0}'.format(str(receipt['logs'][0]['address'])))
                results = extractSwapResults(w3, tx, account, timestamp, receipt, network)
                if results != None and type(results) is records.TraderTransaction:
                    events_map['swaps'].append(results)
                    eventsFound = True
                    if settings.USE_CACHE:
                        db.saveTransaction(tx, timestamp, 'swaps', jsonpickle.encode(results), account)
                else:
                    logging.error('Error: Failed to parse a vendor result. {0}'.format(receipt['logs'][0]['address']))
            elif 'Summoning' in action:
                logging.debug('Summoning activity: {0}'.format(tx))
                results = extractSummonResults(w3, tx, account, timestamp, receipt)
                if results != None:
                    if type(results) == int:
                        eventsFound = True
                        logging.info('heroid results {0} {1}'.format(tx, results))
                        if summonCrystalStorage[2] != None:
                            # crystal open event just returns the hero ID summoned so we can now add the full data
                            for r in summonCrystalStorage[2]:
                                r.itemID = results
                            events_map['tavern'] = events_map['tavern'] + summonCrystalStorage[2]
                            if settings.USE_CACHE and db.findTransaction(summonCrystalStorage[0], account) == None:
                                db.saveTransaction(summonCrystalStorage[0], summonCrystalStorage[1], 'tavern', jsonpickle.encode(summonCrystalStorage[2]), account)
                            else:
                                logging.info('tried to save portal record that already existed {0}'.format(tx))
                            if settings.USE_CACHE and db.findTransaction(tx, account) == None:
                                db.saveTransaction(tx, timestamp, 'nones', '', account)
                            else:
                                logging.info('tried to save none portal when record already existed {0}'.format(tx))
                            summonCrystalStorage = [None, None, None]
                            heroIdStorage = None
                            heroIdTx = None
                        else:
                            # on rare occassion the crystal open even might get parsed before the summon crystal
                            heroIdStorage = results
                            heroIdTx = tx
                    elif len(results) > 1 and results[1] != None:
                        eventsFound = True
                        if heroIdStorage == None:
                            # store crystal creation events for later so we can tag it with the summoned hero id
                            summonCrystalStorage[0] = tx
                            summonCrystalStorage[1] = timestamp
                            summonCrystalStorage[2] = [results[0], results[1]]
                        else:
                            # events came in backwards and now we can save with hero id
                            results[1].itemID = heroIdStorage
                            if results[0] != None:
                                results[0].itemID = heroIdStorage
                            events_map['tavern'] = events_map['tavern'] + [results[0], results[1]]
                            if settings.USE_CACHE and db.findTransaction(tx, account) == None:
                                db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode([results[0], results[1]]), account)
                            else:
                                logging.info('tried to save backwards portal that already existed {0}'.format(tx))
                            if settings.USE_CACHE and db.findTransaction(summonCrystalStorage[0], account) == None:
                                db.saveTransaction(heroIdTx, timestamp, 'nonec', '', account)
                            else:
                                logging.info('tried to save a backwards noen that already existed {0}'.format(tx))
                            heroIdStorage = None
                            heroIdTx = None
                            summonCrystalStorage = [None, None, None]
                    if type(results) != int and len(results) > 2 and results[2] != None:
                        eventsFound = True
                        # other events are single hero hires
                        # record is to be saved in db and will be looked up when seller runs thier tax report
                        # All of these get populated by running a report for the Tavern Address though, so we need to
                        # skip if record has already been created.
                        if db.findTransaction(tx, results[2].seller) == None:
                            db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[2]), results[2].seller)
                        else:
                            logging.info('summon hire found but was already in db on {0}.'.format(tx))
                else:
                    logging.info('Error: Failed to parse a summon result. {0}'.format(tx))
            elif 'Meditation' in action:
                logging.debug('Meditation activity: {0}'.format(tx))
                results = extractMeditationResults(w3, tx, account, timestamp, receipt)
                if results != None:
                    for record in results:
                        if type(record) is records.TavernTransaction:
                            events_map['tavern'].append(record)
                            eventsFound = True
                    if settings.USE_CACHE and eventsFound:
                        db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results), account)
                else:
                    logging.info('Error: Failed to parse a meditation result. {0}'.format(tx))
            elif 'Alchemist' in action:
                logging.debug('Alchemist activity: {0}'.format(tx))
                results = extractAlchemistResults(w3, tx, account, timestamp, receipt)
                if results != None:
                    events_map['alchemist'].append(results)
                    eventsFound = True
                    if settings.USE_CACHE:
                        db.saveTransaction(tx, timestamp, 'alchemist', jsonpickle.encode(results), account)
                else:
                    logging.info('Failed to parse alchemist results tx {0}'.format(tx))
            elif 'HeroSale' in action:
                # Special Gen0 sale events are like a summon but are crystals are bought with jewel
                with open('abi/HeroSale.json', 'r') as f:
                    ABI = f.read()
                contract = w3.eth.contract(address='0xdF0Bf714e80F5e6C994F16B05b7fFcbCB83b89e9', abi=ABI)
                decoded_logs = contract.events.Gen0Purchase().processReceipt(receipt, errors=DISCARD)
                heroId = 0
                purchasePrice = 0
                crystalId = 0
                for log in decoded_logs:
                    logging.info('Purchase Gen0 Crystal id {0} price {1}'.format(log['args']['crystalId'], log['args']['purchasePrice']))
                    crystalId = log['args']['crystalId']
                    purchasePrice = log['args']['purchasePrice']
                decoded_logs = contract.events.CrystalOpen().processReceipt(receipt, errors=DISCARD)
                for log in decoded_logs:
                    logging.info('Open Gen0 Crystal id {0} heroid {1}'.format(log['args']['crystalId'], log['args']['heroId']))
                    crystalId = log['args']['crystalId']
                    heroId = log['args']['heroId']
                if crystalId != 0:
                    eventsFound = True
                    if log['args']['crystalId'] not in heroCrystals:
                        heroCrystals[log['args']['crystalId']] = [tx, timestamp, purchasePrice, heroId]
                    else:
                        heroCrystals[log['args']['crystalId']][2] = max(purchasePrice, heroCrystals[log['args']['crystalId']][2])
                        heroCrystals[log['args']['crystalId']][3] = max(heroId, heroCrystals[log['args']['crystalId']][3])
                        if heroCrystals[log['args']['crystalId']][2] > 0 and heroCrystals[log['args']['crystalId']][3] > 0:
                            heroPrice = Web3.fromWei(heroCrystals[log['args']['crystalId']][2], 'ether')
                            r = records.TavernTransaction(tx, 'hero', heroCrystals[log['args']['crystalId']][3], 'purchase', timestamp, '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', heroPrice)
                            r.fiatAmount = prices.priceLookup(timestamp, 'defi-kingdoms') * r.coinCost
                            events_map['tavern'].append(r)
                            if settings.USE_CACHE:
                                db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(r), account)
                                db.saveTransaction(heroCrystals[log['args']['crystalId']][0], heroCrystals[log['args']['crystalId']][1], 'noneg', '', account)
            elif 'anySwap' in action or 'Bridge' in action:
                logging.debug('Bridge activity: {0}'.format(tx))
                results = extractBridgeResults(w3, tx, account, timestamp, receipt)
                if results != None:
                    events_map['wallet'].append(results)
                    eventsFound = True
                    if settings.USE_CACHE:
                        db.saveTransaction(tx, timestamp, 'wallet', jsonpickle.encode(results), account)
                else:
                    logging.info('Failed to parse bridge results tx {0}'.format(tx))
            else:
                # Native token wallet transfers
                results = []
                # Transfers from fund wallets should be considered income payments
                if result['from'] in contracts.payment_wallets:
                    depositEvent = 'payment'
                else:
                    depositEvent = 'deposit'
                if 'Deposit from' in action and value > 0:
                    r = records.walletActivity(tx, timestamp, depositEvent, result['from'], getNativeToken(network), value)
                    r.fiatValue = prices.priceLookup(timestamp, r.coinType) * value
                    results.append(r)
                if 'Withdrawal to' in action and value > 0:
                    r = records.walletActivity(tx, timestamp, 'withdraw', result['to'], getNativeToken(network), value)
                    r.fiatValue = prices.priceLookup(timestamp, r.coinType) * value
                    results.append(r)
                # also check for any random token trasfers in the wallet
                results += extractTokenResults(w3, tx, account, timestamp, receipt, depositEvent)
                if results != None:
                    for item in results:
                        events_map['wallet'].append(item)
                    eventsFound = True
                    if settings.USE_CACHE and db.findTransaction(tx, account) == None:
                        db.saveTransaction(tx, timestamp, 'wallet', jsonpickle.encode(results), account)
                else:
                    logging.info('Got no results from anything tx {0}'.format(tx))
        else:
            # transaction failed, mark to ignore later
            eventsFound = True
            db.saveTransaction(tx, timestamp, 'nonef', '', account)
        # transactions with no relevant data get a none record so they are ignored in later reports
        if eventsFound == False and settings.USE_CACHE and db.findTransaction(tx, account) == None:
            db.saveTransaction(tx, timestamp, 'nonee', '', account)

        txCount += 1

    db.updateReport(account, startDate, endDate, 'complete', alreadyComplete + len(txs))
    return events_map

# Simple way to determine conversion, maybe change to lookup on chain later
def valueFromWei(amount, token):
    #w3.fromWei doesn't seem to have an 8 decimal option for BTC
    if token in ['0x3095c7557bCb296ccc6e363DE01b760bA031F2d9', '0xdc54046c0451f9269FEe1840aeC808D36015697d']:
        return amount / decimal.Decimal(100000000)
    else:
        if token in ['0x3a4EDcf3312f44EF027acfd8c21382a5259936e7']: # DFKGOLD
            weiConvert = 'kwei'
        elif token in ['0x985458E523dB3d53125813eD68c274899e9DfAb4','0x3C2B8Be99c50593081EAA2A724F0B8285F5aba8f','0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664']: # 1USDC/1USDT
            weiConvert = 'mwei'
        elif token in contracts.gold_values:
            weiConvert = 'wei'
        else:
            weiConvert = 'ether'
        return Web3.fromWei(amount, weiConvert)

def getNativeToken(network):
    if network == 'avalanche':
        return '0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7'
    else:
        return '0xcF664087a5bB0237a0BAd6742852ec6c8d69A27a'

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

def extractBankResults(w3, txn, account, timestamp, receipt):
    ABI = getABI('xJewel')
    contract = w3.eth.contract(address='0xA9cE83507D872C5e1273E745aBcfDa849DAA654F', abi=ABI)
    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
    rcvdToken = "unk"
    rcvdAmount = 0
    sentToken = "unk"
    sentAmount = 0
    for log in decoded_logs:
        if 'to' in log['args'] and 'from' in log['args']:
            if log['args']['to'] == account:
                rcvdToken = log['address']
                rcvdAmount = Web3.fromWei(log['args']['value'], 'ether')
            if log['args']['from'] == account:
                sentToken = log['address']
                sentAmount = Web3.fromWei(log['args']['value'], 'ether')
        if sentAmount > 0 and rcvdAmount > 0:
            if sentToken == '0xA9cE83507D872C5e1273E745aBcfDa849DAA654F': # TODO: make this an array including crystal when crystalvale launches
                # Dumping xJewel and getting Jewel from bank
                r = records.BankTransaction(txn, timestamp, 'withdraw', rcvdAmount / sentAmount, rcvdToken, rcvdAmount)
                r.fiatValue = prices.priceLookup(timestamp, r.coinType) * r.coinAmount
            else:
                # Depositing Jewel in the Bank for xJewel
                r = records.BankTransaction(txn, timestamp, 'deposit', sentAmount / rcvdAmount, sentToken, sentAmount)
                r.fiatValue = prices.priceLookup(timestamp, r.coinType) * r.coinAmount
            return r
    logging.warn('Bank fail data: {0} {1} {2} {3}'.format(sentAmount, sentToken, rcvdAmount, rcvdToken))

def extractGardenerResults(w3, txn, account, timestamp, receipt):
    # events record amount of jewel received when claiming at the gardens
    ABI = getABI('MasterGardener')
    contract = w3.eth.contract(address='0xDB30643c71aC9e2122cA0341ED77d09D5f99F924', abi=ABI)
    events = []
    decoded_logs = contract.events.SendGovernanceTokenReward().processReceipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        receivedAmount = Web3.fromWei(log['args']['amount'], 'ether')
        lockedAmount = Web3.fromWei(log['args']['lockAmount'], 'ether')
        r = records.GardenerTransaction(txn, timestamp, 'staking-reward', '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', receivedAmount - lockedAmount)
        rl = records.GardenerTransaction(txn, timestamp, 'staking-reward-locked', '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', lockedAmount)
        jewelPrice = prices.priceLookup(timestamp, '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F')
        r.fiatValue = jewelPrice * r.coinAmount
        rl.fiatValue = jewelPrice * rl.coinAmount
        events.append(r)
        events.append(rl)

    # events record amount of lp tokens put in and out of gardens for farming and when
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
    gardenEvent = ''
    gardenToken = ''
    gardenAmount = 0
    for log in decoded_logs:
        # Token Transfers
        if 'to' in log['args'] and 'from' in log['args'] and log['address'] in contracts.address_map and 'Jewel LP' in contracts.address_map[log['address']]:
            if log['args']['to'] == account:
                gardenEvent = 'withdraw'
                gardenToken = log['address']
                gardenAmount = Web3.fromWei(log['args']['value'], 'ether')
            elif log['args']['from'] == account:
                gardenEvent = 'deposit'
                gardenToken = log['address']
                gardenAmount = Web3.fromWei(log['args']['value'], 'ether')
    if gardenAmount > 0:
        r = records.GardenerTransaction(txn, timestamp, gardenEvent, gardenToken, gardenAmount)
        events.append(r)

    return events

def extractFarmResults(w3, txn, account, timestamp, receipt):
    # events record amount of rewards received when claiming at the farms
    ABI = getABI('ERC20')
    contract = w3.eth.contract(address='0x1f806f7C8dED893fd3caE279191ad7Aa3798E928', abi=ABI)
    events = []
    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
    farmEvent = ''
    farmToken = ''
    farmAmount = 0
    rewardEvent = ''
    rewardToken = ''
    rewardAmount = 0
    for log in decoded_logs:
        # Token Transfers
        if 'to' in log['args'] and 'from' in log['args']:
            if 'Pangolin LP' in contracts.getAddressName(log['address']) and log['args']['to'] == account:
                farmEvent = 'withdraw'
                farmToken = log['address']
                farmAmount = Web3.fromWei(log['args']['value'], 'ether')
            if log['args']['to'] == account:
                rewardEvent = 'staking-reward'
                rewardToken = log['address']
                rewardAmount = Web3.fromWei(log['args']['value'], 'ether')
            elif 'Pangolin LP' in contracts.getAddressName(log['address']) and log['args']['from'] == account:
                farmEvent = 'deposit'
                farmToken = log['address']
                farmAmount = Web3.fromWei(log['args']['value'], 'ether')
    if farmAmount > 0:
        r = records.GardenerTransaction(txn, timestamp, farmEvent, farmToken, farmAmount)
        events.append(r)
    if rewardAmount > 0:
        rr = records.GardenerTransaction(txn, timestamp, rewardEvent, rewardToken, rewardAmount)
        rewardPrice = prices.priceLookup(timestamp, rewardToken)
        rr.fiatValue = rewardPrice * rr.coinAmount
        events.append(rr)

    return events

def extractSwapResults(w3, txn, account, timestamp, receipt, network):
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
    ABI = getABI('Wrapped ONE')
    contract = w3.eth.contract(address='0xcF664087a5bB0237a0BAd6742852ec6c8d69A27a', abi=ABI)
    decoded_logs += contract.events.Withdrawal().processReceipt(receipt, errors=DISCARD)
    decoded_logs += contract.events.Deposit().processReceipt(receipt, errors=DISCARD)
    rcvdToken = []
    rcvdAmount = []
    sentToken = []
    sentAmount = []
    for log in decoded_logs:
        # Token Transfers
        if 'to' in log['args'] and 'from' in log['args']:
            if log['args']['to'] == account:
                rcvdToken.append(log['address'])
                rcvdAmount.append(valueFromWei(log['args']['value'], log['address']))
            elif log['args']['from'] == account:
                sentToken.append(log['address'])
                sentAmount.append(valueFromWei(log['args']['value'], log['address']))
            else:
                logging.debug('ignored swap log {0} to {1} not involving account'.format(log['args']['from'], log['args']['to']))
        # Native token transfers (src and dst also in args but not used yet)
        if 'wad' in log['args']:
            if log['event'] == 'Withdrawal':
                rcvdToken.append(log['address'])
                rcvdAmount.append(valueFromWei(log['args']['wad'], log['address']))
            if log['event'] == 'Deposit':
                sentToken.append(log['address'])
                sentAmount.append(valueFromWei(log['args']['wad'], log['address']))

    if len(rcvdAmount) > 0 and rcvdAmount[0] > 0:
        if len(sentToken) == 1 and len(rcvdToken) == 1:
            # simple 1 coin in 1 coin out swaps
            r = records.TraderTransaction(txn, timestamp, sentToken[0], rcvdToken[0], sentAmount[0], rcvdAmount[0])
            fiatValues = getSwapFiatValues(timestamp, sentToken[0], sentAmount[0], rcvdToken[0], rcvdAmount[0])
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
                r = records.LiquidityTransaction(txn, timestamp, 'withdraw', sentToken[0], sentAmount[0], rcvdToken[0], rcvdAmount[0], rcvdToken[1], rcvdAmount[1])
                fiatValues = getSwapFiatValues(timestamp, rcvdToken[0], rcvdAmount[0], rcvdToken[1], rcvdAmount[1])
                r.coin1FiatValue = fiatValues[0]
                r.coin2FiatValue = fiatValues[1]
                return r
            elif len(rcvdToken) == 1 and len(sentToken) == 2:
                # receiving LP tokens, sending 2 currencies is LP deposit
                logging.info('Liquidity deposit event {2} send {0} rcvd {1}'.format(str(sentToken), str(rcvdToken), txn))
                r = records.LiquidityTransaction(txn, timestamp, 'deposit', rcvdToken[0], rcvdAmount[0], sentToken[0], sentAmount[0], sentToken[1], sentAmount[1])
                fiatValues = getSwapFiatValues(timestamp, sentToken[0], sentAmount[0], sentToken[1], sentAmount[1])
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

# Lookup and return the fiat values given two tokens in a swap at a point in time
def getSwapFiatValues(timestamp, sentToken, sentAmount, rcvdToken, rcvdAmount):
    # Lookup price for normal tokens, but set direct value of both for fiat type coins
    if sentToken in contracts.fiatTypes['usd']:
        fiatSwapValue = decimal.Decimal(1.0) * sentAmount
        return [fiatSwapValue, fiatSwapValue]
    else:
        fiatSwapValue = prices.priceLookup(timestamp, sentToken) * sentAmount

    if rcvdToken in contracts.fiatTypes['usd']:
        fiatReceiveValue = decimal.Decimal(1.0) * rcvdAmount
        return [fiatReceiveValue, fiatReceiveValue]
    else:
        fiatReceiveValue = prices.priceLookup(timestamp, rcvdToken) * rcvdAmount

    return [fiatSwapValue, fiatReceiveValue]

def extractSummonResults(w3, txn, account, timestamp, receipt):
    # Get the summon costs data
    tearsAmount = decimal.Decimal(0.0)
    jewelAmount = decimal.Decimal(0.0)
    hiringProceeds = decimal.Decimal(0.0)
    hiredFromAccount = ''
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.debug('{3} transfer for summon from: {0} to: {1} value: {2}'.format(log['args']['from'], log['args']['to'], log['args']['value'], contracts.getAddressName(log['address'])))
        if log['address'] == '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F':
            jewelAmount += Web3.fromWei(log['args']['value'], 'ether')
            # capture transfer amount to other player so we can create a record for thier gains
            if log['args']['to'] not in contracts.tx_fee_targets:
                hiringProceeds = Web3.fromWei(log['args']['value'], 'ether')
                hiredFromAccount = log['args']['to']
        else:
            tearsAmount += log['args']['value']

    ABI = getABI('HeroSummoningUpgradeable')
    r = None
    rc = None
    rs = None
    summoner = 'unk'
    assistant = 'unk'
    contract = w3.eth.contract(address='0x65DEA93f7b886c33A78c10343267DD39727778c2', abi=ABI)
    decoded_logs = contract.events.CrystalSummoned().processReceipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.info('Summonning Crystal log: summonerId {0} assistantId {1} generation {2} summonerTears {3} assistantTears {4}'.format(log['args']['summonerId'], log['args']['assistantId'], log['args']['generation'], log['args']['summonerTears'], log['args']['assistantTears']))
        if type(log['args']['generation']) is int:
            summoner = log['args']['summonerId']
            assistant = log['args']['assistantId']
            rc = records.TavernTransaction(txn, 'hero', '/'.join((str(summoner),str(assistant))), 'summon', timestamp, '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', jewelAmount)
            rc.fiatAmount = prices.priceLookup(timestamp, rc.coinType) * rc.coinCost
            r = records.TavernTransaction(txn, 'hero', '/'.join((str(summoner),str(assistant))), 'crystal', timestamp, '0x24eA0D436d3c2602fbfEfBe6a16bBc304C963D04', int(tearsAmount))
            r.fiatAmount = prices.priceLookup(timestamp, r.coinType) * r.coinCost
            logging.info('{3} Summon Crystal event {0} jewel/{1} tears {2} gen result'.format(jewelAmount, tearsAmount, log['args']['generation'], txn))

    decoded_logs = contract.events.AuctionSuccessful().processReceipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.info('{0} Summonning Auction log: '.format(txn) + str(log))
        if hiredFromAccount != '':
            # Saves record of owner of hired hero gaining proceeds from hire
            hiredHero = log['args']['tokenId']
            if assistant != 'unk':
                hiredHero = assistant
            rs = records.TavernTransaction(txn, 'hero', hiredHero, 'hire', timestamp, '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', hiringProceeds)
            rs.fiatAmount = prices.priceLookup(timestamp, rs.coinType) * rs.coinCost
            rs.seller = hiredFromAccount
            logging.info('Hero hired {0} for {1}'.format(rs.coinCost, rs.itemID))

    decoded_logs = contract.events.CrystalOpen().processReceipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.info('{3} crystal open {0} hero {1} for {2}'.format(log['args']['crystalId'], log['args']['heroId'], log['args']['owner'], txn))
        return log['args']['heroId']

    return [r, rc, rs]

def extractMeditationResults(w3, txn, account, timestamp, receipt):
    # Get the meditation costs data
    shvasAmount = decimal.Decimal(0.0)
    jewelAmount = decimal.Decimal(0.0)
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        if log['address'] == '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F':
            jewelAmount += Web3.fromWei(log['args']['value'], 'ether')
        else:
            shvasAmount += log['args']['value']

    ABI = getABI('MeditationCircle')
    contract = w3.eth.contract(address='0x0594D86b2923076a2316EaEA4E1Ca286dAA142C1', abi=ABI)
    complete_logs = contract.events.MeditationBegun().processReceipt(receipt, errors=DISCARD)
    r = None
    rs = None
    heroID = None
    for log in complete_logs:
        heroID = log['args']['heroId']
        if type(heroID) is int:
            rs = records.TavernTransaction(txn, 'hero', heroID, 'levelup', timestamp, '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', jewelAmount)
            rs.fiatAmount = prices.priceLookup(timestamp, rs.coinType) * rs.coinCost
            r = records.TavernTransaction(txn, 'hero', heroID, 'meditate', timestamp, '0x66F5BfD910cd83d3766c4B39d13730C911b2D286', int(shvasAmount))
            r.fiatAmount = prices.priceLookup(timestamp, r.coinType) * r.coinCost
            logging.info('{3} Meditation event {0} jewel/{1} shvas {2} heroid'.format(jewelAmount, shvasAmount, heroID, txn))
    return [r, rs]

def extractAuctionResults(w3, txn, account, timestamp, receipt, auctionType):
    # Get the seller data
    auctionSeller = ""
    auctionToken = ""
    sellerProceeds = decimal.Decimal(0.0)
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.debug('Jewel transfer for auction from: {0} to: {1} value: {2}'.format(log['args']['from'], log['args']['to'], log['args']['value']))
        if log['args']['to'] not in contracts.tx_fee_targets:
            auctionSeller = log['args']['to']
            auctionToken = log['address']
            sellerProceeds = Web3.fromWei(log['args']['value'], 'ether')

    ABI = getABI('SaleAuction')
    contract = w3.eth.contract(address='0x13a65B9F8039E2c032Bc022171Dc05B30c3f2892', abi=ABI)
    decoded_logs = contract.events.AuctionSuccessful().processReceipt(receipt, errors=DISCARD)
    r = None
    rs = None
    for log in decoded_logs:
        auctionPrice = Web3.fromWei(log['args']['totalPrice'], 'ether')
        logging.info("  {2}  Bought {3} {0} for {1} jewel".format(log['args']['tokenId'], auctionPrice, log['args']['winner'], auctionType))
        r = records.TavernTransaction(txn, auctionType, log['args']['tokenId'], 'purchase', timestamp, auctionToken, auctionPrice)
        r.fiatAmount = prices.priceLookup(timestamp, auctionToken) * r.coinCost

        if auctionSeller != "":
            logging.info("  {2}  Sold {3} {0} for {1} jewel".format(log['args']['tokenId'], auctionPrice, auctionSeller, auctionType))
            rs = records.TavernTransaction(txn, auctionType, log['args']['tokenId'], 'sale', timestamp, auctionToken, sellerProceeds)
            rs.fiatAmount = prices.priceLookup(timestamp, auctionToken) * rs.coinCost
            rs.seller = auctionSeller
    return [r, rs]

def extractAirdropResults(w3, txn, account, timestamp, receipt):
    # Create record of the airdrop tokens received
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
    rcvdTokens = {}
    results = []
    address = ''
    for log in decoded_logs:
        # Token Transfers
        if 'to' in log['args'] and 'from' in log['args']:
            if log['args']['to'] == account:
                address = log['args']['from']
                if log['address'] in rcvdTokens:
                    rcvdTokens[log['address']] += valueFromWei(log['args']['value'], log['address'])
                else:
                    rcvdTokens[log['address']] = valueFromWei(log['args']['value'], log['address'])
            elif log['args']['from'] == account:
                address = log['args']['to']
                if log['address'] in rcvdTokens:
                    rcvdTokens[log['address']] += valueFromWei(log['args']['value'], log['address'])
                else:
                    rcvdTokens[log['address']] = valueFromWei(log['args']['value'], log['address'])
            else:
                logging.info('ignored airdrop log {0} to {1} not involving account'.format(log['args']['from'], log['args']['to']))
    for k, v in rcvdTokens.items():
        logging.info('AirdropClaimed: {0} {1}'.format(v, k))
        r = records.AirdropTransaction(txn, timestamp, address, k, v)
        r.fiatValue = prices.priceLookup(timestamp, k) * r.tokenAmount
        results.append(r)
    return results

def extractQuestResults(w3, txn, timestamp, receipt):
    ABI = getABI('QuestCoreV2')
    contract = w3.eth.contract(address='0x5100Bd31b822371108A0f63DCFb6594b9919Eaf4', abi=ABI)
    decoded_logs = contract.events.QuestReward().processReceipt(receipt, errors=DISCARD)
    rewardTotals = {}
    txns = []
    for log in decoded_logs:
        if 'itemQuantity' in log['args'] and 'rewardItem' in log['args'] and log['args']['rewardItem'] != '0x0000000000000000000000000000000000000000':
            # Keep a running total of each unique reward item in this quest result
            rewardQuantity = valueFromWei(log['args']['itemQuantity'], log['args']['rewardItem'])
            if log['args']['rewardItem'] in contracts.address_map:
                logging.debug('    Hero {2} on quest {3} got reward of {0} {1}\n'.format(rewardQuantity, contracts.address_map[log['args']['rewardItem']], log['args']['heroId'], log['args']['questId']))
                if log['args']['rewardItem'] in rewardTotals:
                    rewardTotals[log['args']['rewardItem']] += rewardQuantity
                else:
                    rewardTotals[log['args']['rewardItem']] = rewardQuantity
            else:
                logging.info('    Hero {2} on quest {3} got reward of {0} unknown({1})\n'.format(rewardQuantity, log['args']['rewardItem'], log['args']['heroId'], log['args']['questId']))
    for k, v in rewardTotals.items():
        r = records.QuestTransaction(txn, timestamp, k, v)
        r.fiatValue = prices.priceLookup(timestamp, k) * v
        txns.append(r)
    return txns

def extractAlchemistResults(w3, txn, account, timestamp, receipt):
    # Create record of the alchemist crafting activity with total costs
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
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
                rcvdAmount.append(valueFromWei(log['args']['value'], log['address']))
            elif log['args']['from'] == account:
                sentToken.append(log['address'])
                sentAmount.append(valueFromWei(log['args']['value'], log['address']))
            else:
                logging.debug('ignored alchemist log {0} to {1} not involving account'.format(log['args']['from'], log['args']['to']))
    # Total up value of all ingredients
    ingredientList = ''
    ingredientValue = 0
    for i in range(len(sentToken)):
        ingredientList += '{0}x{1}, '.format(contracts.address_map[sentToken[i]], sentAmount[i])
        ingredientValue += prices.priceLookup(timestamp, sentToken[i]) * sentAmount[i]
    if len(ingredientList) > 1:
        ingredientList = ingredientList[:-2]
    # should be just 1 thing received, the potion, create the record if so
    if len(rcvdToken) == 1:
        r = records.AlchemistTransaction(txn, timestamp, rcvdToken[0], rcvdAmount[0])
        r.fiatValue = prices.priceLookup(timestamp, rcvdToken[0])
        r.craftingCosts = ingredientList
        r.costsFiatValue = ingredientValue
    else:
        logging.error('Failed to add alchemist record, wrong token rcvd {0}'.format(txn))
    return r

def extractBridgeResults(w3, txn, account, timestamp, receipt):
    # Record token bridging as a wallet event
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
    r = None
    for log in decoded_logs:
        if log['args']['to'] != '0x0000000000000000000000000000000000000000' and log['args']['from'] == account:
            otherAddress = log['args']['to']
        elif log['args']['from'] != '0x0000000000000000000000000000000000000000' and log['args']['to'] == account:
            otherAddress = log['args']['from']
        else:
            logging.info('{3} ignoring token transfer not from/to account from {0} to {1} value {2}'.format(log['args']['from'], log['args']['to'], log['args']['value'], txn))
            continue
        tokenValue = valueFromWei(log['args']['value'], log['address'])
        tokenName = contracts.getAddressName(log['address'])
        if tokenValue > 0:
            logging.info('{3} wallet bridge from: {0} to: {1} value: {2}'.format(log['args']['from'], log['args']['to'], tokenValue, tokenName))
            r = records.walletActivity(txn, timestamp, 'bridge', otherAddress, log['address'], tokenValue)
            r.fiatValue = prices.priceLookup(timestamp, r.coinType) * tokenValue
    return r

def extractTokenResults(w3, txn, account, timestamp, receipt, depositEvent):
    ABI = getABI('JewelToken')
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
    transfers = []
    for log in decoded_logs:
        if log['args']['from'] == account:
            event = 'withdraw'
            otherAddress = log['args']['to']
        elif log['args']['to'] == account:
            event = depositEvent
            otherAddress = log['args']['from']
        else:
            logging.info('{3} ignoring token transfer not from/to account from {0} to {1} value {2}'.format(log['args']['from'], log['args']['to'], log['args']['value'], txn))
            continue
        tokenValue = valueFromWei(log['args']['value'], log['address'])

        if tokenValue > 0:
            logging.info('{3} wallet transfer from: {0} to: {1} value: {2}'.format(log['args']['from'], log['args']['to'], tokenValue, contracts.getAddressName(log['address'])))
            r = records.walletActivity(txn, timestamp, event, otherAddress, log['address'], tokenValue)
            r.fiatValue = prices.priceLookup(timestamp, r.coinType) * tokenValue
            transfers.append(r)
        else:
            logging.info('zero value wallet transfer ignored')
    return transfers
