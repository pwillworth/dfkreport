#!/usr/bin/env python3
import events
import contracts
import records
import datetime
import logging
import db
import constants
from decimal import *

# Record for final tax report data
class TaxItem:
    def __init__(self, txHash, sentAmount, sentType, rcvdAmount, rcvdType, description, category, soldDate, fiatType='usd', proceeds=0, acquiredDate=None, costs=0, term="short", txFees=0):
        self.description = description
        # gains, income, or expenses
        self.category = category
        self.acquiredDate = acquiredDate
        self.soldDate = soldDate
        self.fiatType = fiatType
        self.proceeds = Decimal(proceeds)
        self.costs = Decimal(costs)
        self.term = term
        self.amountNotAccounted = Decimal(proceeds)
        # source data points
        self.txHash = txHash
        self.sentAmount = sentAmount
        self.sentType = sentType
        self.rcvdAmount = rcvdAmount
        self.rcvdType = rcvdType
        self.txFees = Decimal(txFees)
    # Only calculate gains assets cost basis was found
    def get_gains(self):
        if self.proceeds > 0:
            if hasattr(self, 'txFees'):
                return self.proceeds - self.costs - self.txFees
            else:
                return self.proceeds - self.costs
        else:
            return 0

# A common object structure for combining different types of records
class CostBasisItem:
    def __init__(self, txHash, timestamp, receiveType, receiveAmount, fiatType, fiatReceiveValue):
        self.txHash = txHash
        self.timestamp = timestamp
        self.receiveType = receiveType
        self.receiveAmount = receiveAmount
        self.fiatType = fiatType
        self.fiatReceiveValue = fiatReceiveValue
        self.receiveAmountNotAccounted = receiveAmount

def inReportRange(item, startDate, endDate):
    itemDate = datetime.date.fromtimestamp(item.timestamp)
    return itemDate >= startDate and itemDate <= endDate

# Scrape all events and build the Tax Report from it
def buildTaxMap(txns, txCounts, account, startDate, endDate, costBasis, includedChains, moreOptions):
    # Generate map of all events from transaction list
    logging.info('Start Event map build')
    if includedChains & constants.HARMONY > 0:
        eventMap = events.checkTransactions(txns[0], account, startDate, endDate, 'harmony')
        if eventMap == 'Error: Blockchain connection failure.':
            raise ConnectionError('Service Unavailable')
    else:
        eventMap = events.EventsMap()
    if includedChains & constants.DFKCHAIN > 0:
        eventMapDFK = events.checkTransactions(txns[2], account, startDate, endDate, 'dfkchain', txCounts[0])
        if eventMapDFK == 'Error: Blockchain connection failure.':
            raise ConnectionError('Service Unavailable')
    else:
        eventMapDFK = events.EventsMap()
    if includedChains & constants.KLAYTN > 0:
        eventMapKlay = events.checkTransactions(txns[3], account, startDate, endDate, 'klaytn', txCounts[0]+txCounts[2])
        if eventMapKlay == 'Error: Blockchain connection failure.':
            raise ConnectionError('Service Unavailable')
    else:
        eventMapKlay = events.EventsMap()
    if includedChains & constants.AVALANCHE > 0:
        eventMapAvax = events.checkTransactions(txns[1], account, startDate, endDate, 'avalanche', txCounts[0]+txCounts[2]+txCounts[3])
        if eventMapAvax == 'Error: Blockchain connection failure.':
            raise ConnectionError('Service Unavailable')
    else:
        eventMapAvax = events.EventsMap()
    # Map the events into tax records
    logging.info('Start Tax mapping {0}'.format(account))
    # Have to look up Tavern sale/hire events because they are not associated direct to wallet
    eventMap['tavern'] = eventMap['tavern'] + eventMapDFK['tavern'] + eventMapKlay['tavern'] + db.getTavernSales(account, startDate, endDate)
    eventMap['swaps'] += eventMapAvax['swaps']
    eventMap['swaps'] += eventMapDFK['swaps']
    eventMap['swaps'] += eventMapKlay['swaps']
    eventMap['liquidity'] += eventMapAvax['liquidity']
    eventMap['liquidity'] += eventMapDFK['liquidity']
    eventMap['liquidity'] += eventMapKlay['liquidity']
    eventMap['wallet'] += eventMapAvax['wallet']
    eventMap['wallet'] += eventMapDFK['wallet']
    eventMap['wallet'] += eventMapKlay['wallet']
    eventMap['bank'] += eventMapAvax['bank']
    eventMap['bank'] += eventMapDFK['bank']
    eventMap['bank'] += eventMapKlay['bank']
    eventMap['gardens'] += eventMapAvax['gardens']
    eventMap['gardens'] += eventMapDFK['gardens']
    eventMap['gardens'] += eventMapKlay['gardens']
    eventMap['quests'] += eventMapDFK['quests']
    eventMap['quests'] += eventMapKlay['quests']
    eventMap['alchemist'] += eventMapDFK['alchemist']
    eventMap['alchemist'] += eventMapKlay['alchemist']
    # Look up wallet payments distributed by interacting with Jewel contract also
    eventMap['airdrops'] = eventMap['airdrops'] + eventMapKlay['airdrops'] + eventMapDFK['airdrops'] + db.getWalletPayments(account)
    eventMap['gas'] = eventMap['gas'] + eventMapAvax['gas'] + eventMapDFK['gas'] + eventMapKlay['gas']
    logging.info('building swap data')
    swapData = buildSwapRecords(eventMap['swaps'], startDate, endDate, eventMap['wallet'], eventMap['airdrops'], eventMap['gardens'], eventMap['quests'], eventMap['tavern'], eventMap['lending'], costBasis, moreOptions['purchaseAddresses'])
    logging.info('building liquidity data')
    liquidityData = buildLiquidityRecords(eventMap['liquidity'], startDate, endDate)
    logging.info('building payment data')
    walletData = buildPaymentRecords(eventMap['wallet'], startDate, endDate)
    logging.info('building bank data')
    bankData = buildBankRecords(eventMap['bank'], startDate, endDate)
    logging.info('building gardens data')
    gardensData = buildGardensRecords(eventMap['gardens'], startDate, endDate)
    logging.info('building tavern data')
    tavernData = buildTavernRecords(eventMap['tavern'], startDate, endDate)
    logging.info('building quest data')
    questData = buildQuestRecords(eventMap['quests'], startDate, endDate)
    logging.info('building airdrop data')
    airdropData = buildAirdropRecords(eventMap['airdrops'], startDate, endDate)
    logging.info('building lending data')
    lendingData = buildLendingRecords(eventMap['lending'], startDate, endDate)
    # pop out all events not in date range
    logging.info('paring data to range')
    eventMap['tavern'] = [x for x in eventMap['tavern'] if inReportRange(x, startDate, endDate)]
    eventMap['swaps'] = [x for x in eventMap['swaps'] if inReportRange(x, startDate, endDate)]
    eventMap['wallet'] = [x for x in eventMap['wallet'] if inReportRange(x, startDate, endDate)]
    eventMap['liquidity'] = [x for x in eventMap['liquidity'] if inReportRange(x, startDate, endDate)]
    eventMap['bank'] = [x for x in eventMap['bank'] if inReportRange(x, startDate, endDate)]
    eventMap['gardens'] = [x for x in eventMap['gardens'] if inReportRange(x, startDate, endDate)]
    eventMap['quests'] = [x for x in eventMap['quests'] if inReportRange(x, startDate, endDate)]
    eventMap['alchemist'] = [x for x in eventMap['alchemist'] if inReportRange(x, startDate, endDate)]
    eventMap['airdrops'] = [x for x in eventMap['airdrops'] if inReportRange(x, startDate, endDate)]
    eventMap['lending'] = [x for x in eventMap['lending'] if inReportRange(x, startDate, endDate)]
    eventMap['lending'] = costBasisSort(eventMap['lending'], 'fifo')
    # Return all tax records combined and events
    return {
        'taxes': swapData + liquidityData + walletData + bankData + gardensData + tavernData + questData + airdropData + lendingData,
        'events': eventMap
    }

# For preparing a list with correct sorting before searching through it to apply cost basis
def costBasisSort(eventList, costBasis):
    if costBasis in ['fifo', 'acb']:
        return sorted(eventList, key=lambda x: x.timestamp)
    elif costBasis == 'lifo':
        return sorted(eventList, key=lambda x: x.timestamp, reverse=True)
    elif costBasis == 'hifo':
        return sorted(eventList, key=lambda x: x.fiatReceiveValue / x.receiveAmount if x.receiveAmount else 0, reverse=True)
    else:
        return eventList

# Generate Auction House Tax records from the events
def buildTavernRecords(tavernEvents, startDate, endDate):
    results = []
    heroExpenses = {}
    heroIncome = {}
    landExpenses = {}
    petExpenses = {}
    perishRewards = {}
    # Grab a list of all purchases, summons, and levelups to list as expenses
    for event in tavernEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        if event.event in ['purchase','summon','crystal','meditate','levelup','enhance','incubate','crack']:
            if event.itemType == 'land':
                if event.itemID in landExpenses:
                    if event.event in landExpenses[event.itemID].description:
                        landExpenses[event.itemID].description = landExpenses[event.itemID].description.replace(event.event, '{0}+'.format(event.event))
                    else:
                        landExpenses[event.itemID].description += ''.join((' ', event.event))
                    landExpenses[event.itemID].costs += event.fiatAmount
                    if landExpenses[event.itemID].acquiredDate == None or eventDate < landExpenses[event.itemID].acquiredDate:
                        landExpenses[event.itemID].acquiredDate = eventDate
                    if hasattr(event, 'fiatFeeValue'):
                        landExpenses[event.itemID].txFees += event.fiatFeeValue
                else:
                    ti = TaxItem(event.txHash, event.coinCost, contracts.getTokenName(event.coinType, event.network), 0, '', '{2} {0} {1}'.format(event.itemID, event.event, event.itemType), 'expenses', None, event.fiatType, 0, eventDate, event.fiatAmount)
                    if hasattr(event, 'fiatFeeValue'):
                        ti.txFees = event.fiatFeeValue
                    landExpenses[event.itemID] = ti
            elif event.itemType == 'pet':
                if event.itemID in petExpenses:
                    if event.event in petExpenses[event.itemID].description:
                        petExpenses[event.itemID].description = petExpenses[event.itemID].description.replace(event.event, '{0}+'.format(event.event))
                    else:
                        petExpenses[event.itemID].description += ''.join((' ', event.event))
                    petExpenses[event.itemID].costs += event.fiatAmount
                    if petExpenses[event.itemID].acquiredDate == None or eventDate < petExpenses[event.itemID].acquiredDate:
                        petExpenses[event.itemID].acquiredDate = eventDate
                    if hasattr(event, 'fiatFeeValue'):
                        petExpenses[event.itemID].txFees += event.fiatFeeValue
                else:
                    ti = TaxItem(event.txHash, event.coinCost, contracts.getTokenName(event.coinType, event.network), 0, '', '{2} {0} {1}'.format(event.itemID, event.event, event.itemType), 'expenses', None, event.fiatType, 0, eventDate, event.fiatAmount)
                    if hasattr(event, 'fiatFeeValue'):
                        ti.txFees = event.fiatFeeValue
                    petExpenses[event.itemID] = ti
            else:
                if event.itemID in heroExpenses:
                    if event.event in heroExpenses[event.itemID].description:
                        heroExpenses[event.itemID].description = heroExpenses[event.itemID].description.replace(event.event, '{0}+'.format(event.event))
                    else:
                        heroExpenses[event.itemID].description += ''.join((' ', event.event))
                    heroExpenses[event.itemID].costs += event.fiatAmount
                    if heroExpenses[event.itemID].acquiredDate == None or eventDate < heroExpenses[event.itemID].acquiredDate:
                        heroExpenses[event.itemID].acquiredDate = eventDate
                    if hasattr(event, 'fiatFeeValue'):
                        heroExpenses[event.itemID].txFees += event.fiatFeeValue
                else:
                    ti = TaxItem(event.txHash, event.coinCost, contracts.getTokenName(event.coinType, event.network), 0, '', '{2} {0} {1}'.format(event.itemID, event.event, event.itemType), 'expenses', None, event.fiatType, 0, eventDate, event.fiatAmount)
                    if hasattr(event, 'fiatFeeValue'):
                        ti.txFees = event.fiatFeeValue
                    heroExpenses[event.itemID] = ti

    # Grab a list of all hero hires to list as income
    for event in tavernEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        if event.event in ['hire'] and eventDate >= startDate and eventDate <= endDate:
            if event.itemID in heroIncome:
                if event.event in heroIncome[event.itemID].description:
                    heroIncome[event.itemID].description = heroIncome[event.itemID].description.replace(event.event, '{0}+'.format(event.event))
                else:
                    heroIncome[event.itemID].description += ''.join((' ', event.event))
                heroIncome[event.itemID].proceeds += event.fiatAmount
                # setup the acquired/sold date to tell the range of dates the hires occured
                if heroIncome[event.itemID].acquiredDate == None or eventDate < heroIncome[event.itemID].acquiredDate:
                    heroIncome[event.itemID].acquiredDate = eventDate
                if heroIncome[event.itemID].soldDate == None or eventDate < heroIncome[event.itemID].soldDate:
                    heroIncome[event.itemID].soldDate = eventDate
            else:
                ti = TaxItem(event.txHash, 0, '', event.coinCost, contracts.getTokenName(event.coinType, event.network), 'Hero {0} {1}'.format(event.itemID, event.event), 'income', eventDate, event.fiatType, event.fiatAmount)
                heroIncome[event.itemID] = ti

    for event in tavernEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        # summarize rewards for any perished event in the requested range
        if event.event == 'perished' and eventDate >= startDate and eventDate <= endDate:
            if event.itemID in perishRewards:
                perishRewards[event.itemID].proceeds += event.fiatAmount
                perishRewards[event.itemID].soldDate = eventDate
                if hasattr(event, 'fiatFeeValue'):
                    perishRewards[event.itemID].txFees += event.fiatFeeValue
            else:
                ti = TaxItem(event.txHash, 0, '', event.coinCost, contracts.getTokenName(event.coinType, event.network), 'Perished {1} {0}'.format(event.itemID, event.itemType), 'gains', eventDate, event.fiatType, event.fiatAmount)
                if hasattr(event, 'fiatFeeValue'):
                    ti.txFees = event.fiatFeeValue
                ti.amountNotAccounted = 1
                perishRewards[event.itemID] = ti
    # Create a tax record for any perished hero in the requested range and add cost basis
    for kp, vp in perishRewards.items():
        for k, v in heroExpenses.items():
            if k == kp:
                if vp.acquiredDate == None:
                    vp.acquiredDate = v.acquiredDate
                vp.costs = v.costs
                if 'summon' in v.description or 'purchase' in v.description:
                    vp.amountNotAccounted = 0
                if vp.soldDate - vp.acquiredDate > datetime.timedelta(days=365):
                    vp.term = "long"
                v.proceeds = vp.proceeds
                vp.txFees += v.txFees
        results.append(vp)

    for event in tavernEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        # Create a tax record for any sale event in the requested range
        if event.event == 'sale' and eventDate >= startDate and eventDate <= endDate:
            ti = TaxItem(event.txHash, 0, '', event.coinCost, contracts.getTokenName(event.coinType, event.network), 'Sold {1} {0}'.format(event.itemID, event.itemType), 'gains', eventDate, event.fiatType, event.fiatAmount)
            if hasattr(event, 'fiatFeeValue'):
                ti.txFees = event.fiatFeeValue
            ti.amountNotAccounted = 1
            # Check NFT cost data so gains can be calculated
            if event.itemType == 'land':
                expenseList = landExpenses
            elif event.itemType == 'pet':
                expenseList = petExpenses
            else:
                expenseList = heroExpenses
            for k, v in expenseList.items():
                if k == event.itemID and v.acquiredDate <= eventDate:
                    if ti.acquiredDate == None:
                        ti.acquiredDate = v.acquiredDate
                    ti.costs = v.costs
                    ti.amountNotAccounted = 0
                    if ti.soldDate - ti.acquiredDate > datetime.timedelta(days=365):
                        ti.term = "long"
                    v.proceeds = event.fiatAmount
                    ti.txFees += v.txFees
            results.append(ti)
    for k, v in petExpenses.items():
        results.append(v)
    for k, v in landExpenses.items():
        results.append(v)
    for k, v in heroExpenses.items():
        results.append(v)
    for k, v in heroIncome.items():
        results.append(v)
    return results

def buildSwapRecords(swapEvents, startDate, endDate, walletEvents, airdropEvents, gardensEvents, questEvents, tavernEvents, lendingEvents, costBasis, purchaseAddresses):
    results = []
    # TODO inlcude liquidity withdrawal received tokens for cost basis search
    # Find any wallet transfers to purchase addresses and treat them like a swap for fiat '0x985458E523dB3d53125813eD68c274899e9DfAb4'
    # same with any wallet donations
    for item in walletEvents:
        if (item.action == 'withdraw' and item.address in purchaseAddresses) or item.action == 'donation':
            si = records.TraderTransaction(item.txHash, item.network, item.timestamp, item.coinType, 'fiat value', item.coinAmount, item.fiatValue)
            si.fiatSwapValue = item.fiatValue
            si.fiatReceiveValue = item.fiatValue
            if hasattr(item, 'fiatFeeValue'):
                si.fiatFeeValue = item.fiatFeeValue
            swapEvents.append(si)
    # Find any hero purchases and treat them like a swap for fiat '0x985458E523dB3d53125813eD68c274899e9DfAb4'
    # same with any wallet donations
    for item in tavernEvents:
        if item.event == 'purchase':
            si = records.TraderTransaction(item.txHash, item.network, item.timestamp, item.coinType, 'NFT {0} {1}'.format(item.itemType, item.itemID), item.coinCost, item.fiatAmount)
            si.fiatSwapValue = item.fiatAmount
            si.fiatReceiveValue = item.fiatAmount
            if hasattr(item, 'fiatFeeValue'):
                si.fiatFeeValue = item.fiatFeeValue
            swapEvents.append(si)
    swapEvents = sorted(swapEvents, key=lambda x: x.timestamp)

    # Build list of token recieve events to search for cost basis that can all be sorted together
    logging.info('  setup list for cost basis')
    cbList = []
    for sEvent in swapEvents:
        ci = CostBasisItem(sEvent.txHash, sEvent.timestamp, sEvent.receiveType, sEvent.receiveAmount, sEvent.fiatType, sEvent.fiatReceiveValue)
        cbList.append(ci)
    for aEvent in airdropEvents:
        # This can be removed after a clean of airdrops cached records
        if not hasattr(aEvent, 'amountNotAccounted'):
            aEvent.amountNotAccounted = aEvent.tokenAmount
        ci = CostBasisItem(aEvent.txHash, aEvent.timestamp, aEvent.tokenReceived, aEvent.tokenAmount, aEvent.fiatType, aEvent.fiatValue)
        cbList.append(ci)
    for gEvent in gardensEvents:
        if not hasattr(gEvent, 'amountNotAccounted'):
            gEvent.amountNotAccounted = gEvent.coinAmount
        ci = CostBasisItem(gEvent.txHash, gEvent.timestamp, gEvent.coinType, gEvent.coinAmount, gEvent.fiatType, gEvent.fiatValue)
        cbList.append(ci)
    for qEvent in questEvents:
        if not hasattr(qEvent, 'amountNotAccounted'):
            qEvent.amountNotAccounted = qEvent.rewardAmount
        ci = CostBasisItem(qEvent.txHash, qEvent.timestamp, qEvent.rewardType, qEvent.rewardAmount, qEvent.fiatType, qEvent.fiatValue)
        cbList.append(ci)
    for tEvent in tavernEvents:
        if tEvent.event in ['hire','sale','perished']:
            ci = CostBasisItem(tEvent.txHash, tEvent.timestamp, tEvent.coinType, tEvent.coinCost, tEvent.fiatType, tEvent.fiatAmount)
            cbList.append(ci)
    for lEvent in lendingEvents:
        if lEvent.event in ['borrow']:
            ci = CostBasisItem(lEvent.txHash, lEvent.timestamp, lEvent.coinType, lEvent.coinAmount, lEvent.fiatType, lEvent.fiatValue)
            cbList.append(ci)
    # Also run through direct wallet transactions to try and fill remaining gaps in received value accounting
    # This works assuming the asset was purchased on same day it was transferred in, TODO: maybe add to disclaimer/FAQ
    for wEvent in walletEvents:
        if wEvent.action in ['deposit','payment']:
            ci = CostBasisItem(wEvent.txHash, wEvent.timestamp, wEvent.coinType, wEvent.coinAmount, wEvent.fiatType, wEvent.fiatValue)
            cbList.append(ci)
    cbList = costBasisSort(cbList, costBasis)

    #TODO consider also search bank gains income for cost basis
    logging.info('  build events in range')
    for event in swapEvents:
        # swapping an item for gold does not need to be on tax report (I think)
        # questionable where to draw the line between game and currency trades
        if event.network == 'harmony':
            goldValues = contracts.HARMONY_GOLD_VALUES
        elif event.network == 'klaytn':
            goldValues = contracts.KLAYTN_GOLD_VALUES
        else:
            goldValues = contracts.DFKCHAIN_GOLD_VALUES
        if event.swapType in goldValues and event.receiveType == contracts.GOLD_TOKENS[event.network]:
            continue
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        if eventDate >= startDate and eventDate <= endDate:
            if event.receiveType[0:4] == 'NFT ':
                actionStr = 'Paid for NFT with'
            elif event.receiveType == 'fiat value':
                actionStr = 'Paid for goods/svcs with'
            else:
                actionStr = 'Sold'
            ti = TaxItem(event.txHash, event.swapAmount, contracts.getTokenName(event.swapType, event.network), event.receiveAmount, contracts.getTokenName(event.receiveType, event.network), '{4} {0:.5f} {1} for {2:.5f} {3}'.format(event.swapAmount, contracts.getTokenName(event.swapType, event.network), event.receiveAmount, contracts.getTokenName(event.receiveType, event.network), actionStr), 'gains', eventDate, event.fiatType, event.fiatSwapValue)
            if hasattr(event, 'fiatFeeValue'):
                ti.txFees = event.fiatFeeValue
            # Check all transactions for prior time when sold token was received to calc gains
            acbUnits = 0
            acbValue = 0
            for searchEvent in cbList:
                searchEventDate = datetime.date.fromtimestamp(searchEvent.timestamp)
                if searchEvent.receiveType == event.swapType and searchEvent.timestamp < event.timestamp and event.swapAmountNotAccounted > 0 and searchEvent.receiveAmountNotAccounted > 0:
                    # setting date here although it could get overwritten later if multiple recieves are used
                    # to account for single swap (likely)
                    if ti.acquiredDate == None:
                        ti.acquiredDate = searchEventDate
                    if ti.soldDate - ti.acquiredDate > datetime.timedelta(days=365):
                        ti.term = "long"
                    if costBasis == 'acb':
                        if searchEvent.receiveAmountNotAccounted > 0:
                            acbUnits += searchEvent.receiveAmountNotAccounted
                            if hasattr(searchEvent, 'fiatFeeValue'):
                                acbValue += (searchEvent.fiatReceiveValue + searchEvent.fiatFeeValue) * Decimal(searchEvent.receiveAmountNotAccounted / searchEvent.receiveAmount)
                            else:
                                acbValue += searchEvent.fiatReceiveValue * Decimal(searchEvent.receiveAmountNotAccounted / searchEvent.receiveAmount)
                        if searchEvent.receiveAmountNotAccounted <= event.swapAmountNotAccounted:
                            event.swapAmountNotAccounted -= searchEvent.receiveAmountNotAccounted
                            searchEvent.receiveAmountNotAccounted = 0
                        else:
                            event.swapAmountNotAccounted = 0
                            searchEvent.receiveAmountNotAccounted -= event.swapAmountNotAccounted
                    else:
                        if searchEvent.receiveAmountNotAccounted <= event.swapAmountNotAccounted:
                            # use up all receive transaction amount and update amount left to match still
                            ti.costs += searchEvent.fiatReceiveValue * Decimal(searchEvent.receiveAmountNotAccounted / searchEvent.receiveAmount)
                            event.swapAmountNotAccounted -= searchEvent.receiveAmountNotAccounted
                            searchEvent.receiveAmountNotAccounted = 0
                        else:
                            # use up as much of recieve transaction as swap was for and update amount left to account for on receive
                            ti.costs += Decimal(searchEvent.fiatReceiveValue / searchEvent.receiveAmount) * event.swapAmountNotAccounted
                            searchEvent.receiveAmountNotAccounted -= event.swapAmountNotAccounted
                            event.swapAmountNotAccounted = 0
                            break
            # For Adjusted cost basis, we use the average cost paid for all purchases prior to sale
            if costBasis == 'acb':
                if acbUnits > 0:
                    ti.costs = Decimal(acbValue / acbUnits) * event.swapAmount
            # Note any amount of cost basis not found for later red flag
            ti.amountNotAccounted = event.swapAmountNotAccounted

            results.append(ti)

    return results

def buildLiquidityRecords(liquidityEvents, startDate, endDate):
    results = []
    for event in liquidityEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        # Withdrawal from liquidity pool triggers realized growth or loss, make tax item and find cost basis
        if event.action == 'withdraw' and eventDate >= startDate and eventDate <= endDate:
            ti = TaxItem(event.txHash, event.poolAmount, contracts.getTokenName(event.poolAddress, event.network), '{0}/{1}'.format(event.coin1Amount, event.coin2Amount), '{0}/{1}'.format(contracts.getTokenName(event.coin1Type, event.network), contracts.getTokenName(event.coin2Type, event.network)), 'Liquidity Withdrawal {0}'.format(contracts.getTokenName(event.poolAddress, event.network)), 'gains', eventDate, event.fiatType, event.coin1FiatValue + event.coin2FiatValue)
            if hasattr(event, 'fiatFeeValue'):
                ti.txFees = event.fiatFeeValue
            # Check history for deposit data so gains/losses can be calculated
            for searchEvent in liquidityEvents:
                searchEventDate = datetime.date.fromtimestamp(searchEvent.timestamp)
                if searchEvent.action == 'deposit' and searchEvent.poolAddress == event.poolAddress and searchEvent.timestamp <= event.timestamp:
                    # TODO: maybe only set acquiredDate if not set so it always uses the oldest date?
                    ti.acquiredDate = searchEventDate
                    if ti.soldDate - ti.acquiredDate > datetime.timedelta(days=365):
                        ti.term = "long"
                    searchEventTotalValue = searchEvent.coin1FiatValue + searchEvent.coin2FiatValue
                    if searchEvent.amountNotAccounted <= event.amountNotAccounted:
                        # deposit is smaller than this event, so use it all up as cost basis
                        ti.costs += searchEventTotalValue * (searchEvent.amountNotAccounted / (searchEvent.coin1Amount + searchEvent.coin2Amount))
                        event.amountNotAccounted -= searchEvent.amountNotAccounted
                        searchEvent.amountNotAccounted = 0
                    else:
                        # deposit is larger than remaining cost basis we need to find so use part of it
                        ti.costs += (searchEventTotalValue / searchEvent.poolAmount) * event.amountNotAccounted
                        searchEvent.amountNotAccounted -= event.amountNotAccounted
                        event.amountNotAccounted = 0
            # Note any amount of cost basis not found for later red flag
            ti.amountNotAccounted = event.amountNotAccounted

            results.append(ti)
    # TODO Also list unmatched liquidity deposits in current assets

    return results

# Generate Bank xJewel rewards Tax records from the events
def buildBankRecords(bankEvents, startDate, endDate):
    results = []
    bankEvents = costBasisSort(bankEvents, 'fifo')
    for event in bankEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        # Withdrawal from Bank triggers realized xJewel rewards, make tax item and find cost basis
        if (event.action == 'claim' or (event.action == 'withdraw' and event.coinType == contracts.POWER_TOKENS[event.network])) and eventDate >= startDate and eventDate <= endDate:
            ti = TaxItem(event.txHash, 0, '', event.coinAmount, contracts.getTokenName(event.coinType, event.network), 'Bank Rewards {0}'.format(contracts.getTokenName(event.coinType, event.network)), 'income', eventDate, event.fiatType, event.fiatValue)
            if hasattr(event, 'fiatFeeValue'):
                ti.txFees = event.fiatFeeValue
            # Use Jewel cost at withdraw time for all calcs so we are not including Jewel price functuation in Bank Rewards
            jewelPrice = event.fiatValue / event.coinAmount
            # Check history for deposit data so gains can be calculated
            for searchEvent in bankEvents:
                searchEventDate = datetime.date.fromtimestamp(searchEvent.timestamp)
                if searchEvent.action == 'deposit' and searchEvent.coinType == event.coinType and searchEvent.timestamp <= event.timestamp:
                    # TODO: maybe only set acquiredDate if not set so it always uses the oldest date?
                    ti.acquiredDate = searchEventDate
                    if searchEvent.amountNotAccounted <= event.amountNotAccounted:
                        # deposit is smaller than this event, so use it all up as cost basis
                        if event.xRate > 0:
                            ti.costs += (jewelPrice * searchEvent.coinAmount) * (searchEvent.amountNotAccounted / (searchEvent.coinAmount / searchEvent.xRate)) * (searchEvent.xRate / event.xRate)
                        else:
                            ti.costs += (jewelPrice * searchEvent.coinAmount) * (searchEvent.amountNotAccounted / searchEvent.xRate)
                        event.amountNotAccounted -= searchEvent.amountNotAccounted
                        searchEvent.amountNotAccounted = 0
                    else:
                        # deposit is larger than remaining cost basis we need to find so use part of it
                        if event.xRate > 0:
                            ti.costs += ((jewelPrice * searchEvent.coinAmount) / searchEvent.amountNotAccounted) * event.amountNotAccounted * (searchEvent.xRate / event.xRate)
                        else:
                            ti.costs += ((jewelPrice * searchEvent.coinAmount) / searchEvent.xRate) * event.amountNotAccounted
                        event.amountNotAccounted = 0
                        searchEvent.amountNotAccounted -= event.amountNotAccounted
            # Note any amount of cost basis not found for later red flag
            ti.amountNotAccounted = event.amountNotAccounted

            results.append(ti)
    return results

# Generate Gardens Staking rewards Tax events
def buildGardensRecords(gardensEvents, startDate, endDate):
    results = []
    # use dict to summarize rewards by day
    rewardGroups = {}
    for event in gardensEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        # Create basic income tax record for any staking reward claim that is not locked
        # Locked Jewel is accounted for when mined from mining quest and it actually is available and realized
        if event.event == 'staking-reward' and eventDate >= startDate and eventDate <= endDate:
            if ''.join((eventDate.strftime('%d-%m-%Y'), event.event, event.coinType)) in rewardGroups:
                rewardGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.event, event.coinType))].proceeds += event.fiatValue
                # this is hacky, but I'm just gonna use it to keep track of total jewel since it is not needed
                rewardGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.event, event.coinType))].costs += event.coinAmount
            else:
                ti = TaxItem(event.txHash, 0, '', event.coinAmount, contracts.getTokenName(event.coinType, event.network), '{0} Staking Reward'.format(contracts.getTokenName(event.coinType, event.network)), 'income', eventDate, event.fiatType, event.fiatValue)
                if hasattr(event, 'fiatFeeValue'):
                    ti.txFees = event.fiatFeeValue
                # Not really!
                ti.costs = event.coinAmount
                ti.amountNotAccounted = 0
                rewardGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.event, event.coinType))] = ti

    for k, v in rewardGroups.items():
        v.description += ' {:.3f}'.format(v.costs)
        v.costs = 0
        results.append(v)
    return results

# Generate Airdrop income Tax events
def buildAirdropRecords(airdropEvents, startDate, endDate):
    results = []
    for event in airdropEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        eventTitle = 'Airdrop'
        if hasattr(event, 'address') and event.address in contracts.payment_wallets:
            eventTitle = 'Payment'
        if not hasattr(event, 'network'):
            event.network = 'dfkchain'
        # Create basic income tax record for any airdrop
        if eventDate >= startDate and eventDate <= endDate:
            if event.tokenAmount % 1 > 0:
                desc = '{2} {0:.3f} {1}'.format(event.tokenAmount, contracts.getTokenName(event.tokenReceived, event.network), eventTitle)
            else:
                desc = '{2} {0} {1}'.format(int(event.tokenAmount), contracts.getTokenName(event.tokenReceived, event.network), eventTitle)
            ti = TaxItem(event.txHash, 0, '', event.tokenAmount, contracts.getTokenName(event.tokenReceived, event.network), desc, 'income', eventDate, event.fiatType, event.fiatValue)
            if hasattr(event, 'fiatFeeValue'):
                ti.txFees = event.fiatFeeValue
            ti.amountNotAccounted = 0
            results.append(ti)

    return results

# Generate Lending income Tax events
def buildLendingRecords(lendingEvents, startDate, endDate):
    results = []
    for event in lendingEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        if event.event == 'interest' and eventDate >= startDate and eventDate <= endDate:
            desc = '{0} {1:.3f} {2}'.format(event.event, event.coinAmount, contracts.getTokenName(event.coinType, event.network))
            ti = TaxItem(event.txHash, event.coinAmount, event.coinType, 0, '', desc, 'expenses', eventDate, event.fiatType, 0, None, event.fiatValue)
            ti.amountNotAccounted = 0
            results.append(ti)
    return results

# Generate Quest rewards Tax events
def buildQuestRecords(questEvents, startDate, endDate):
    results = []
    # use dict to summarize rewards by type/day
    itemGroups = {}
    #questEvents.sort(key=lambda x: x.timestamp)
    for event in questEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        # Create basic income tax record for any jewel reward from quests
        # TODO decide if we maybe want to include other items as income, but I don't think so
        if (event.rewardType == contracts.POWER_TOKENS[event.network] or event.rewardType == contracts.JEWEL_ADDRESSES[event.network]) and eventDate >= startDate and eventDate <= endDate:
            if ''.join((eventDate.strftime('%d-%m-%Y'), event.rewardType)) in itemGroups:
                itemGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.rewardType))].proceeds += event.fiatValue
                # this is hacky, but I'm just gonna use it to keep track of total jewel since it is not needed
                itemGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.rewardType))].costs += event.rewardAmount
            else:
                ti = TaxItem(event.txHash, 0, '', event.rewardAmount, contracts.getTokenName(event.rewardType, event.network), 'Quest {0} Rewards'.format(contracts.getTokenName(event.rewardType, event.network)), 'income', eventDate, event.fiatType, event.fiatValue)
                # Not really!
                ti.costs = event.rewardAmount
                if hasattr(event, 'fiatFeeValue'):
                    ti.txFees += event.fiatFeeValue
                itemGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.rewardType))] = ti
    for k, v in itemGroups.items():
        v.description = 'Quest {0} Rewards {1:.3f}'.format(v.rcvdType, v.costs)
        v.rcvdAmount = v.costs
        # zero out costs because we were just using it to trace the sum of coin amount
        v.costs = 0
        v.amountNotAccounted = 0
        results.append(v)

    return results

# Generate Payment income Tax events and Donation events
def buildPaymentRecords(walletEvents, startDate, endDate):
    results = []
    # use dict to summarize payments by type/day
    itemGroups = {}
    donationGroups = {}
    for event in walletEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        # Create basic income tax record for any wallet deposit from a payment address
        if event.action == 'payment' and eventDate >= startDate and eventDate <= endDate:
            if ''.join((eventDate.strftime('%d-%m-%Y'), event.coinType)) in itemGroups:
                itemGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.coinType))].proceeds += event.fiatValue
                # this is hacky, but I'm just gonna use it to keep track of total jewel since it is not needed
                itemGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.coinType))].costs += event.coinAmount
            else:
                ti = TaxItem(event.txHash, 0, '', event.coinAmount, contracts.getTokenName(event.coinType, event.network), 'Payment', 'income', eventDate, event.fiatType, event.fiatValue)
                if hasattr(event, 'fiatFeeValue'):
                    ti.txFees += event.fiatFeeValue
                # Not really!
                ti.costs = event.coinAmount
                itemGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.coinType))] = ti
        elif event.action == 'donation' and eventDate >= startDate and eventDate <= endDate:
            if ''.join((eventDate.strftime('%d-%m-%Y'), event.coinType)) in donationGroups:
                donationGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.coinType))].costs += event.fiatValue
                # this is hacky, but I'm just gonna use it to keep track of total jewel since it is not needed
                donationGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.coinType))].proceeds += event.coinAmount
            else:
                ti = TaxItem(event.txHash, event.coinAmount, contracts.getTokenName(event.coinType, event.network), 0, '', 'Charitable Donation', 'expenses', eventDate, event.fiatType, 0, None, event.fiatValue)
                if hasattr(event, 'fiatFeeValue'):
                    ti.txFees += event.fiatFeeValue
                # Not really!
                ti.proceeds = event.coinAmount
                donationGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.coinType))] = ti
    for k, v in itemGroups.items():
        v.description += ' {0:.3f} {1}'.format(v.costs, v.rcvdType)
        # zero out costs because we were just using it to trace the sum of coin amount
        v.costs = 0
        v.amountNotAccounted = 0
        results.append(v)
    for k, v in donationGroups.items():
        v.description += ' {0:.3f} {1}'.format(v.proceeds, v.sentType)
        # zero out proceeds because we were just using it to trace the sum of coin amount
        v.proceeds = 0
        v.amountNotAccounted = 0
        results.append(v)

    return results