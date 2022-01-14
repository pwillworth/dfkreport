#!/usr/bin/env python3

from web3 import Web3
from web3.logs import STRICT, IGNORE, DISCARD, WARN
import nets
import contracts
import records
import prices
import db
import settings
import datetime
import decimal
import jsonpickle
import logging

#TODO fix fail path references so abis don't need to be replicated under web or look em up another way
def checkTransactions(txs, account, startDate, endDate, network, alreadyComplete=0):
    events_map = {
        'tavern': [],
        'swaps' : [],
        'liquidity' : [],
        'wallet' : [],
        'bank' : [],
        'gardens' : [],
        'quests' : [],
        'airdrops' : [],
        'gas' : 0
    }
    # Connect to right network that txs are for
    if network == 'avalanche':
        w3 = Web3(Web3.HTTPProvider(nets.avax_web3))
    else:
        w3 = Web3(Web3.HTTPProvider(nets.hmy_web3))

    if not w3.isConnected():
        logging.error('Error: Critical w3 connection failure for '.format(network))
        return 'Error: Blockchain connection failure.'

    txCount = 0
    summonCrystalStorage = [None, None, None]
    heroIdStorage = None
    heroIdTx = None
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
            db.updateReport(account, datetime.datetime.strftime(startDate, '%Y-%m-%d'), datetime.datetime.strftime(endDate, '%Y-%m-%d'), 'complete', alreadyComplete + txCount)

        if settings.USE_CACHE:
            checkCache = db.findTransaction(str(tx), account)
            if checkCache != None:
                # if event data is empty it is just record with no events we care about and in the db so we dont have to parse blockchain again
                if checkCache[3] != '':
                    events = jsonpickle.decode(checkCache[3])
                    if type(events) is list:
                        for evt in events:
                            logging.debug('loading event from cache {0}'.format(str(evt.__dict__)))
                            events_map[checkCache[2]].append(evt)
                    else:
                        logging.debug('loading event from cache {0}'.format(str(events.__dict__)))
                        events_map[checkCache[2]].append(events)
                txCount += 1
                continue
        try:
            # sometimes they just don't exist yet
            result = w3.eth.get_transaction(tx)
        except Exception:
            continue
        action = lookupEvent(result['from'], result['to'], account)
        value = Web3.fromWei(result['value'], 'ether')
        block = result['blockNumber']
        if network != 'avalanche':
            timestamp = w3.eth.get_block(block)['timestamp']
        blockDate = datetime.date.fromtimestamp(timestamp)
        receipt = w3.eth.get_transaction_receipt(tx)
        #TODO deduct gas from cost basis
        gas = Web3.fromWei(receipt['gasUsed'], 'ether')
        if blockDate >= startDate and blockDate <= endDate:
            events_map['gas'] += gas
        if receipt['status'] == 1:
            logging.info("{5}:{4} | {3}: {0} - {1} - {2}".format(action, '{:f} value'.format(value), '{:f} gas'.format(gas), tx, datetime.datetime.fromtimestamp(timestamp).isoformat(), network))
            if result['input'] != '0x' and 'Quest' in action:
                results = extractQuestResults(w3, tx, result['input'], timestamp, receipt)
                if len(results) > 0:
                    events_map['quests'] += results
                    eventsFound = True
                    if settings.USE_CACHE:
                        db.saveTransaction(tx, timestamp, 'quests', jsonpickle.encode(results), account)
                else:
                    logging.debug('{0} quest with no rewards.')
            elif 'Auction' in action:
                logging.debug('Auction activity: {0}'.format(tx))
                results = extractAuctionResults(w3, tx, result['input'], account, timestamp, receipt)
                if results != None and results[0] != None:
                    events_map['tavern'].append(results[0])
                    eventsFound = True
                    if settings.USE_CACHE:
                        db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[0]), account)
                else:
                    logging.debug('Ignored an auction interaction, probably listing.')
                # Second record is to be saved in db and will be looked up when seller runs thier tax report
                # All of these get populated by running a report for the Tavern Address though, so we need to
                # skip if record has already been created.
                if results != None and results[1] != None and db.findTransaction(tx, results[1].seller) == None:
                    db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[1]), results[1].seller)
                else:
                    logging.info('Failed to detect auction seller on {0}.'.format(tx))
            elif 'Uniswap' in action:
                results = extractSwapResults(w3, tx, result, account, timestamp, receipt)
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
                results = extractGardenerResults(w3, tx, result, account, timestamp, receipt)
                if results != None and len(results) > 0:
                    for item in results:
                        events_map['gardens'].append(item)
                        eventsFound = True
                    if settings.USE_CACHE:
                        db.saveTransaction(tx, timestamp, 'gardens', jsonpickle.encode(results), account)
                else:
                    logging.error('Error: Failed to parse a Gardener LP Pool result. tx {0}'.format(tx))
            elif 'Airdrop' in action:
                results = extractAirdropResults(w3, tx, result['input'], account, timestamp, receipt)
                if results != None:
                    events_map['airdrops'].append(results)
                    eventsFound = True
                    if settings.USE_CACHE:
                        db.saveTransaction(tx, timestamp, 'airdrops', jsonpickle.encode(results), account)
            elif result['input'] != '0x' and 'xJewel' in action:
                results = extractBankResults(w3, tx, result, account, timestamp, receipt)
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
                results = extractSwapResults(w3, tx, result, account, timestamp, receipt)
                if results != None and type(results) is records.TraderTransaction:
                    events_map['swaps'].append(results)
                    eventsFound = True
                    if settings.USE_CACHE:
                        db.saveTransaction(tx, timestamp, 'swaps', jsonpickle.encode(results), account)
                else:
                    logging.error('Error: Failed to parse a vendor result. {0}'.format(receipt['logs'][0]['address']))
            elif 'Summoning' in action:
                logging.debug('Summoning activity: {0}'.format(tx))
                results = extractSummonResults(w3, tx, result['input'], account, timestamp, receipt)
                if results != None:
                    eventsFound = True
                    if type(results) == int:
                        logging.info('heroid results {0} {1}'.format(tx, results))
                        if summonCrystalStorage[2] != None:
                            # crystal open event just returns the hero ID summoned so we can now add the full data
                            for r in summonCrystalStorage[2]:
                                r.itemID = results
                            events_map['tavern'] = events_map['tavern'] + summonCrystalStorage[2]
                            if settings.USE_CACHE and db.findTransaction(summonCrystalStorage[0], account) == None:
                                db.saveTransaction(summonCrystalStorage[0], summonCrystalStorage[1], 'tavern', jsonpickle.encode(summonCrystalStorage[2]), account)
                            if settings.USE_CACHE and db.findTransaction(tx, account) == None:
                                db.saveTransaction(tx, timestamp, 'nones', '', account)
                            summonCrystalStorage = [None, None, None]
                            heroIdStorage = None
                            heroIdTx = None
                        else:
                            # on rare occassion the crystal open even might get parsed before the summon crystal
                            heroIdStorage = results
                            heroIdTx = tx
                    elif len(results) > 1 and results[1] != None:
                        if heroIdStorage == None:
                            # store crystal creation events for later so we can tag it with the summoned hero id
                            summonCrystalStorage[0] = tx
                            summonCrystalStorage[1] = timestamp
                            summonCrystalStorage[2] = [results[0], results[1]]
                        else:
                            # events came in backwards and now we can save with hero id
                            for r in results:
                                r.itemID = heroIdStorage
                            events_map['tavern'] = events_map['tavern'] + results
                            if settings.USE_CACHE and db.findTransaction(tx, account) == None:
                                db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results), account)
                            if settings.USE_CACHE and db.findTransaction(summonCrystalStorage[0], account) == None:
                                db.saveTransaction(heroIdTx, timestamp, 'nonec', '', account)
                            heroIdStorage = None
                            heroIdTx = None
                            summonCrystalStorage = [None, None, None]
                    if type(results) != int and len(results) > 2 and results[2] != None:
                        # other events are single hero hires
                        # record is to be saved in db and will be looked up when seller runs thier tax report
                        # All of these get populated by running a report for the Tavern Address though, so we need to
                        # skip if record has already been created.
                        if db.findTransaction(tx, results[2].seller) == None:
                            db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results[2]), results[2].seller)
                        else:
                            logging.info('Failed to detect summon hire seller on {0}.'.format(tx))
                else:
                    logging.info('Error: Failed to parse a summon result. {0}'.format(tx))
            elif 'Meditation' in action:
                logging.debug('Meditation activity: {0}'.format(tx))
                results = extractMeditationResults(w3, tx, result['input'], account, timestamp, receipt)
                if results != None:
                    for record in results:
                        if type(record) is records.TavernTransaction:
                            events_map['tavern'].append(record)
                            eventsFound = True
                    if settings.USE_CACHE and eventsFound:
                        db.saveTransaction(tx, timestamp, 'tavern', jsonpickle.encode(results), account)
                else:
                    logging.info('Error: Failed to parse a meditation result. {0}'.format(tx))
            # Native token wallet transfers
            elif 'Deposit from' in action and value > 0:
                r = records.walletActivity(timestamp, 'deposit', result['from'], getNativeToken(network), value)
                r.fiatValue = prices.priceLookup(timestamp, r.coinType) * value
                events_map['wallet'].append(r)
                eventsFound = True
                if settings.USE_CACHE:
                    db.saveTransaction(tx, timestamp, 'wallet', jsonpickle.encode(r), account)
            elif 'Withdrawal to' in action and value > 0:
                if 'JewelToken' in action:
                    with open('abi/JewelToken.json', 'r') as f:
                        ABI = f.read()
                    contract = w3.eth.contract(address='0xA9cE83507D872C5e1273E745aBcfDa849DAA654F', abi=ABI)
                    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
                    for log in decoded_logs:
                        logging.info('sendjewel: ' + str(log))
                r = records.walletActivity(timestamp, 'withdraw', result['to'], '0xcF664087a5bB0237a0BAd6742852ec6c8d69A27a', value)
                r.fiatValue = prices.priceLookup(timestamp, r.coinType) * value
                events_map['wallet'].append(r)
                eventsFound = True
                if settings.USE_CACHE:
                    db.saveTransaction(tx, timestamp, 'wallet', jsonpickle.encode(r), account)
            else:
                # Last possibility, check for any random token trasfers in the wallet
                with open('abi/JewelToken.json', 'r') as f:
                    ABI = f.read()
                contract = w3.eth.contract(address='0xA9cE83507D872C5e1273E745aBcfDa849DAA654F', abi=ABI)
                decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
                transfers = []
                for log in decoded_logs:
                    if log['args']['from'] == account:
                        event = 'withdraw'
                        otherAddress = log['args']['to']
                    elif log['args']['to'] == account:
                        event = 'deposit'
                        otherAddress = log['args']['from']
                    else:
                        logging.error('{3} Could not detect wallet transfer direction from {0} to {1} value {2}'.format(log['args']['from'], log['args']['to'], log['args']['value'], tx))
                        continue
                    tokenValue = Web3.fromWei(log['args']['value'], getDecimals(log['address']))
                    # People might be moving weird tokens around in thier wallet not related to DFK
                    tokenName = 'Unknown({0})'.format(log['address'])
                    if log['address'] in contracts.address_map:
                        tokenName = contracts.address_map[log['address']]
                    if tokenValue > 0 and log['address'] in contracts.address_map:
                        logging.info('{3} wallet transfer from: {0} to: {1} value: {2}'.format(log['args']['from'], log['args']['to'], tokenValue, tokenName))
                        r = records.walletActivity(timestamp, event, otherAddress, log['address'], tokenValue)
                        r.fiatValue = prices.priceLookup(timestamp, r.coinType) * tokenValue
                        transfers.append(r)
                        events_map['wallet'].append(r)
                        eventsFound = True
                    else:
                        logging.info('zero value wallet transfer ignored {0}'.format(tx))
                if settings.USE_CACHE and len(transfers) > 0:
                    db.saveTransaction(tx, timestamp, 'wallet', jsonpickle.encode(transfers), account)
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
def getDecimals(token):
    if token in ['0x3a4EDcf3312f44EF027acfd8c21382a5259936e7']: # DFKGOLD
        weiConvert = 'kwei'
    elif token in ['0x985458E523dB3d53125813eD68c274899e9DfAb4']: # 1USDC
        weiConvert = 'mwei'
    elif token in contracts.gold_values:
        weiConvert = 'wei'
    else:
        weiConvert = 'ether'
    return weiConvert

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

def extractBankResults(w3, txn, details, account, timestamp, receipt):
    with open('abi/xJewel.json', 'r') as f:
        ABI = f.read()
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
            #sys.stdout.write("Swapped {0} {1} for {2} {3} in Bank\n".format(sentAmount, contracts.address_map[sentToken], depAmount, contracts.address_map[rcvdToken])
            if sentToken == '0xA9cE83507D872C5e1273E745aBcfDa849DAA654F': # TODO: make this an array including crystal when crystalvale launches
                # Dumping xJewel and getting Jewel from bank
                r = records.BankTransaction(timestamp, 'withdraw', rcvdAmount / sentAmount, rcvdToken, rcvdAmount)
                r.fiatValue = prices.priceLookup(timestamp, r.coinType) * r.coinAmount
            else:
                # Depositing Jewel in the Bank for xJewel
                r = records.BankTransaction(timestamp, 'deposit', sentAmount / rcvdAmount, sentToken, sentAmount)
                r.fiatValue = prices.priceLookup(timestamp, r.coinType) * r.coinAmount
            return r
    logging.warn('Bank fail data: {0} {1} {2} {3}'.format(sentAmount, sentToken, rcvdAmount, rcvdToken))

def extractGardenerResults(w3, txn, details, account, timestamp, receipt):
    with open('abi/MasterGardener.json', 'r') as f:
        ABI = f.read()
    contract = w3.eth.contract(address='0xDB30643c71aC9e2122cA0341ED77d09D5f99F924', abi=ABI)
    logIndexes = ','
    events = []
    for log in receipt['logs']:
        decoded_logs = contract.events.SendGovernanceTokenReward().processReceipt(receipt, errors=DISCARD)
        for log in decoded_logs:
            if ",{0},".format(log['logIndex']) not in logIndexes:
                logIndexes = "{0}{1},".format(logIndexes, log['logIndex'])
                receivedAmount = Web3.fromWei(log['args']['amount'], 'ether')
                lockedAmount = Web3.fromWei(log['args']['lockAmount'], 'ether')
                #sys.stdout.write("Received Reward {0} Jewel and {1} Locked Jewel\n".format(receivedAmount - lockedAmount, lockedAmount))
                r = records.GardenerTransaction(timestamp, 'staking-reward', '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', receivedAmount - lockedAmount)
                rl = records.GardenerTransaction(timestamp, 'staking-reward-locked', '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', lockedAmount)
                jewelPrice = prices.priceLookup(timestamp, '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F')
                r.fiatValue = jewelPrice * r.coinAmount
                rl.fiatValue = jewelPrice * rl.coinAmount
                events.append(r)
                events.append(rl)
    return events


def extractSwapResults(w3, txn, details, account, timestamp, receipt):
    abiPath = "abi/{0}.json".format('JewelToken')
    with open(abiPath, 'r') as f:
        ABI = f.read()
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
    rcvdToken = []
    rcvdAmount = []
    sentToken = []
    sentAmount = []
    for log in decoded_logs:
        if 'to' in log['args'] and 'from' in log['args']:
            weiConvert = getDecimals(log['address'])
            # added criteria excluding source router to prevent duplicate values showing up on LP withdraw
            if log['args']['to'] == account and log['args']['from'] != '0x24ad62502d1C652Cc7684081169D04896aC20f30':
                rcvdToken.append(log['address'])
                rcvdAmount.append(Web3.fromWei(log['args']['value'], weiConvert))
            elif log['args']['from'] == account:
                sentToken.append(log['address'])
                sentAmount.append(Web3.fromWei(log['args']['value'], weiConvert))
            # added criteria excluding swap target to prevent duplicate values showing up on LP withdraw
            elif log['args']['to'] != '0x0000000000000000000000000000000000000000' and log['args']['from'] in contracts.address_map and ('Jewel LP' in contracts.address_map[log['args']['from']] or 'Pangolin LP' in contracts.address_map[log['args']['from']]):
                rcvdToken.append(log['address'])
                rcvdAmount.append(Web3.fromWei(log['args']['value'], weiConvert))
            elif log['args']['to'] in contracts.address_map and ('Jewel LP' in contracts.address_map[log['args']['to']] or 'Pangolin LP' in contracts.address_map[log['args']['to']]):
                sentToken.append(log['address'])
                sentAmount.append(Web3.fromWei(log['args']['value'], weiConvert))
            else:
                if '0x0000000000000000000000000000000000000000' not in [log['args']['from'], log['args']['to']]:
                    logging.error('Error: ignored swap log {0} to {1} maybe missing some LP address'.format(log['args']['from'], log['args']['to']))
    if len(rcvdAmount) > 0 and rcvdAmount[0] > 0:
        if len(sentToken) == 1 and len(rcvdToken) == 1:
            # simple 1 coin in 1 coin out swaps
            r = records.TraderTransaction(timestamp, sentToken[0], rcvdToken[0], sentAmount[0], rcvdAmount[0])
            fiatValues = getSwapFiatValues(timestamp, sentToken[0], sentAmount[0], rcvdToken[0], rcvdAmount[0])
            r.fiatSwapValue = fiatValues[0]
            r.fiatReceiveValue = fiatValues[1]
            return r
        elif len(sentToken) == 0 or len(rcvdToken) == 0:
            # just incase something weird shows up
            logging.error('wtf swap: {0}: {1} {2}'.format(log['address'], Web3.fromWei(log['args']['value'], 'ether'), log['args']['from']))
        else:
            # Others should be LP deposit/withdraws
            if len(sentToken) == 1 and len(rcvdToken) == 2:
                # if sending 1 and receiving 2, it is withdraw, sending LP tokens, rcv 2 currency
                r = records.LiquidityTransaction(timestamp, 'withdraw', sentToken[0], sentAmount[0], rcvdToken[0], rcvdAmount[0], rcvdToken[1], rcvdAmount[1])
                fiatValues = getSwapFiatValues(timestamp, rcvdToken[0], rcvdAmount[0], rcvdToken[1], rcvdAmount[1])
                r.coin1FiatValue = fiatValues[0]
                r.coin2FiatValue = fiatValues[1]
                return r
            elif len(rcvdToken) == 1 and len(sentToken) == 2:
                # receiving LP tokens, sending 2 currencies is LP deposit
                r = records.LiquidityTransaction(timestamp, 'deposit', rcvdToken[0], rcvdAmount[0], sentToken[0], sentAmount[0], sentToken[1], sentAmount[1])
                fiatValues = getSwapFiatValues(timestamp, sentToken[0], sentAmount[0], sentToken[1], sentAmount[1])
                r.coin1FiatValue = fiatValues[0]
                r.coin2FiatValue = fiatValues[1]
                return r
            else:
                errStr = ''
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

def extractSummonResults(w3, txn, inputs, account, timestamp, receipt):
    # Get the summon costs data
    tearsAmount = decimal.Decimal(0.0)
    jewelAmount = decimal.Decimal(0.0)
    hiringProceeds = decimal.Decimal(0.0)
    hiredFromAccount = ''
    with open('abi/JewelToken.json', 'r') as f:
        ABI = f.read()
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.debug('{3} transfer for summon from: {0} to: {1} value: {2}'.format(log['args']['from'], log['args']['to'], log['args']['value'], contracts.address_map[log['address']]))
        if log['address'] == '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F':
            jewelAmount += Web3.fromWei(log['args']['value'], 'ether')
            # capture transfer amount to other player so we can create a record for thier gains
            if log['args']['to'] not in contracts.summon_fee_targets:
                hiringProceeds = Web3.fromWei(log['args']['value'], 'ether')
                hiredFromAccount = log['args']['to']
        else:
            tearsAmount += log['args']['value']

    with open('abi/HeroSummoningUpgradeable.json', 'r') as f:
        ABI = f.read()
    r = None
    rc = None
    rs = None
    contract = w3.eth.contract(address='0x65DEA93f7b886c33A78c10343267DD39727778c2', abi=ABI)
    input_data = contract.decode_function_input(inputs)
    logging.debug('Summon input: {0}'.format(input_data))

    decoded_logs = contract.events.CrystalSummoned().processReceipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.debug('Summonning Crystal log: summonerId {0} assistantId {1} generation {2} summonerTears {3} assistantTears {4}'.format(log['args']['summonerId'], log['args']['assistantId'], log['args']['generation'], log['args']['summonerTears'], log['args']['assistantTears']))
        if type(log['args']['generation']) is int:
            rc = records.TavernTransaction('hero', '/'.join((str(input_data[1]['_summonerId']),str(input_data[1]['_assistantId']))), 'summon', timestamp, '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', jewelAmount)
            rc.fiatAmount = prices.priceLookup(timestamp, rc.coinType) * rc.coinCost
            rc.seller = hiredFromAccount
            r = records.TavernTransaction('hero', '/'.join((str(input_data[1]['_summonerId']),str(input_data[1]['_assistantId']))), 'crystal', timestamp, '0x24eA0D436d3c2602fbfEfBe6a16bBc304C963D04', int(tearsAmount))
            r.fiatAmount = prices.priceLookup(timestamp, r.coinType) * r.coinCost
            r.seller = hiredFromAccount
            logging.debug('{3} Summon Crystal event {0} jewel/{1} tears {2} gen result'.format(jewelAmount, tearsAmount, log['args']['generation'], txn))

    decoded_logs = contract.events.AuctionSuccessful().processReceipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.debug('{0} Summonning Auction log: '.format(txn) + str(log))
        if hiredFromAccount != '':
            # Saves record of owner of hired hero gaining proceeds from hire
            rs = records.TavernTransaction('hero', log['args']['tokenId'], 'hired', timestamp, '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', hiringProceeds)
            rs.fiatAmount = prices.priceLookup(timestamp, rs.coinType) * rs.coinCost
            rs.seller = hiredFromAccount
            logging.info('Hero hired {0} for {1}'.format(rs.coinCost, rs.itemID))

    decoded_logs = contract.events.CrystalOpen().processReceipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.debug('{3} crystal open {0} hero {1} for {2}'.format(log['args']['crystalId'], log['args']['heroId'], log['args']['owner'], txn))
        return log['args']['heroId']

    return [r, rc, rs]

def extractMeditationResults(w3, txn, inputs, account, timestamp, receipt):
    # Get the meditation costs data
    shvasAmount = decimal.Decimal(0.0)
    jewelAmount = decimal.Decimal(0.0)
    with open('abi/JewelToken.json', 'r') as f:
        ABI = f.read()
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.debug('{3} transfer for meditation from: {0} to: {1} value: {2}'.format(log['args']['from'], log['args']['to'], log['args']['value'], contracts.address_map[log['address']]))
        if log['address'] == '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F':
            jewelAmount += Web3.fromWei(log['args']['value'], 'ether')
        else:
            shvasAmount += log['args']['value']

    with open('abi/MeditationCircle.json', 'r') as f:
        ABI = f.read()
    contract = w3.eth.contract(address='0x0594D86b2923076a2316EaEA4E1Ca286dAA142C1', abi=ABI)
    input_data = contract.decode_function_input(inputs)
    logging.debug('{1} Meditation input: {0}'.format(input_data, txn))
    heroID = input_data[1]['_heroId']
    complete_logs = contract.events.MeditationBegun().processReceipt(receipt, errors=DISCARD)
    decoded_logs = complete_logs
    r = None
    rs = None
    for log in decoded_logs:
        logging.debug('Meditation log: ' + str(log))
        if type(heroID) is int:
            rs = records.TavernTransaction('hero', heroID, 'levelup', timestamp, '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', jewelAmount)
            rs.fiatAmount = prices.priceLookup(timestamp, rs.coinType) * rs.coinCost
            r = records.TavernTransaction('hero', heroID, 'meditate', timestamp, '0x66F5BfD910cd83d3766c4B39d13730C911b2D286', int(shvasAmount))
            r.fiatAmount = prices.priceLookup(timestamp, r.coinType) * r.coinCost
            logging.debug('{3} Meditation event {0} jewel/{1} shvas {2} heroid'.format(jewelAmount, shvasAmount, heroID, txn))
    return [r, rs]

def extractAuctionResults(w3, txn, inputs, account, timestamp, receipt):
    # Get the seller data
    heroSeller = ""
    sellerProceeds = decimal.Decimal(0.0)
    with open('abi/JewelToken.json', 'r') as f:
        ABI = f.read()
    contract = w3.eth.contract(address='0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', abi=ABI)
    decoded_logs = contract.events.Transfer().processReceipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.debug('Jewel transfer for auction from: {0} to: {1} value: {2}'.format(log['args']['from'], log['args']['to'], log['args']['value']))
        if log['args']['to'] not in contracts.jewel_pools:
            heroSeller = log['args']['to']
            sellerProceeds = Web3.fromWei(log['args']['value'], 'ether')

    with open('abi/SaleAuction.json', 'r') as f:
        ABI = f.read()
    contract = w3.eth.contract(address='0x13a65B9F8039E2c032Bc022171Dc05B30c3f2892', abi=ABI)
    input_data = contract.decode_function_input(inputs)
    logging.debug('{1} Auction input: {0}'.format(input_data, txn))
    decoded_logs = contract.events.AuctionSuccessful().processReceipt(receipt, errors=DISCARD)
    r = None
    rs = None
    for log in decoded_logs:
        auctionPrice = Web3.fromWei(log['args']['totalPrice'], 'ether')
        logging.info("  {2}  Bought hero {0} for {1} jewel".format(log['args']['tokenId'], auctionPrice, log['args']['winner']))
        r = records.TavernTransaction('hero', log['args']['tokenId'], 'purchase', timestamp, '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', auctionPrice)
        r.fiatAmount = prices.priceLookup(timestamp, 'defi-kingdoms') * r.coinCost

        if heroSeller != "":
            r.seller = heroSeller
            logging.info("  {2}  Sold hero {0} for {1} jewel".format(log['args']['tokenId'], auctionPrice, heroSeller))
            rs = records.TavernTransaction('hero', log['args']['tokenId'], 'sale', timestamp, '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F', sellerProceeds)
            rs.fiatAmount = prices.priceLookup(timestamp, 'defi-kingdoms') * rs.coinCost
            rs.seller = heroSeller
    return [r, rs]

def extractAirdropResults(w3, txn, inputs, account, timestamp, receipt):
    with open('abi/Airdrop.json', 'r') as f:
        ABI = f.read()
    contract = w3.eth.contract(address='0xa678d193fEcC677e137a00FEFb43a9ccffA53210', abi=ABI)
    #decoded_logs = contract.events.OwnershipTransferred().processReceipt(receipt, errors=DISCARD)
    #for log in decoded_logs:
    #    logging.info('AirdropXfer: ' + str(log))
    decoded_logs = contract.events.Claimed().processReceipt(receipt, errors=DISCARD)
    for log in decoded_logs:
        logging.debug('AirdropClaim: ' + str(log))
        airdropAmount = Web3.fromWei(log['args']['amount'], 'ether')
        if log['args']['recipient'] == account:
            r = records.AirdropTransaction(timestamp, 'jewel', airdropAmount)
            r.fiatValue = prices.priceLookup(timestamp, 'defi-kingdoms') * r.tokenAmount
        return r

def extractQuestResults(w3, txn, inputs, timestamp, receipt):
    with open('abi/QuestCoreV2.json', 'r') as f:
        ABI = f.read()
    contract = w3.eth.contract(address='0x5100Bd31b822371108A0f63DCFb6594b9919Eaf4', abi=ABI)
    decoded_logs = contract.events.QuestReward().processReceipt(receipt, errors=DISCARD)
    rewardTotals = {}
    txns = []
    for log in decoded_logs:
        if 'itemQuantity' in log['args'] and 'rewardItem' in log['args'] and log['args']['rewardItem'] != '0x0000000000000000000000000000000000000000':
            # Keep a running total of each unique reward item in this quest result
            weiConvert = getDecimals(log['args']['rewardItem'])
            rewardQuantity = Web3.fromWei(log['args']['itemQuantity'], weiConvert)
            if log['args']['rewardItem'] in contracts.address_map:
                logging.debug('    Hero {2} on quest {3} got reward of {0} {1}\n'.format(rewardQuantity, contracts.address_map[log['args']['rewardItem']], log['args']['heroId'], log['args']['questId']))
                if log['args']['rewardItem'] in rewardTotals:
                    rewardTotals[log['args']['rewardItem']] += rewardQuantity
                else:
                    rewardTotals[log['args']['rewardItem']] = rewardQuantity
            else:
                logging.info('    Hero {2} on quest {3} got reward of {0} unknown({1})\n'.format(rewardQuantity, log['args']['rewardItem'], log['args']['heroId'], log['args']['questId']))
    for k, v in rewardTotals.items():
        r = records.QuestTransaction(timestamp, k, v)
        r.fiatValue = prices.priceLookup(timestamp, k) * v
        txns.append(r)
    return txns
