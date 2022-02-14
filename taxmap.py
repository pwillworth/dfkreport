#!/usr/bin/env python3
import events
import contracts
import datetime
import logging
import db
import constants
from decimal import *

# Record for final tax report data
class TaxItem:
    def __init__(self, txHash, sentAmount, sentType, rcvdAmount, rcvdType, description, category, soldDate, fiatType='usd', proceeds=0, acquiredDate=None, costs=0, term="short"):
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
    # Only calculate gains assets cost basis was found
    def get_gains(self):
        if self.proceeds > 0:
            return self.proceeds - self.costs
        else:
            return 0

def inReportRange(item, startDate, endDate):
    itemDate = datetime.date.fromtimestamp(item.timestamp)
    return itemDate >= startDate and itemDate <= endDate

# Scrape all events and build the Tax Report from it
def buildTaxMap(txns, account, startDate, endDate, costBasis, includedChains):
    # Generate map of all events from transaction list
    logging.info('Start Event map build')
    if includedChains & constants.HARMONY > 0:
        eventMap = events.checkTransactions(txns[0], account, startDate, endDate, 'harmony')
        if eventMap == 'Error: Blockchain connection failure.':
            raise ConnectionError('Service Unavailable')
    else:
        eventMap = events.EventsMap()
    if includedChains & constants.AVALANCHE > 0:
        eventMapAvax = events.checkTransactions(txns[1], account, startDate, endDate, 'avalanche', len(txns[0]))
        if eventMapAvax == 'Error: Blockchain connection failure.':
            raise ConnectionError('Service Unavailable')
    else:
        eventMapAvax = events.EventsMap()
    # Map the events into tax records
    logging.info('Start Tax mapping {0}'.format(account))
    # Have to look up Tavern sale/hire events because they are not associated direct to wallet
    eventMap['tavern'] = eventMap['tavern'] + eventMapAvax['tavern'] + db.getTavernSales(account, startDate, endDate)
    eventMap['swaps'] += eventMapAvax['swaps']
    eventMap['liquidity'] += eventMapAvax['liquidity']
    eventMap['wallet'] += eventMapAvax['wallet']
    eventMap['bank'] += eventMapAvax['bank']
    eventMap['gardens'] += eventMapAvax['gardens']
    eventMap['quests'] += eventMapAvax['quests']
    eventMap['alchemist'] += eventMapAvax['alchemist']
    # Look up wallet payments distributed by interacting with Jewel contract also
    eventMap['airdrops'] += eventMapAvax['airdrops'] + db.getWalletPayments(account)
    eventMap['gas'] += eventMapAvax['gas']
    tavernData = buildTavernRecords(eventMap['tavern'], startDate, endDate)
    swapData = buildSwapRecords(eventMap['swaps'], startDate, endDate, eventMap['wallet'], eventMap['airdrops'], eventMap['gardens'], eventMap['quests'], costBasis)
    liquidityData = buildLiquidityRecords(eventMap['liquidity'], startDate, endDate)
    bankData = buildBankRecords(eventMap['bank'], startDate, endDate)
    gardensData = buildGardensRecords(eventMap['gardens'], startDate, endDate)
    questData = buildQuestRecords(eventMap['quests'], startDate, endDate)
    airdropData = buildAirdropRecords(eventMap['airdrops'], startDate, endDate)
    walletData = buildPaymentRecords(eventMap['wallet'], startDate, endDate)
    # pop out all events not in date range
    eventMap['tavern'] = [x for x in eventMap['tavern'] if inReportRange(x, startDate, endDate)]
    eventMap['swaps'] = [x for x in eventMap['swaps'] if inReportRange(x, startDate, endDate)]
    eventMap['wallet'] = [x for x in eventMap['wallet'] if inReportRange(x, startDate, endDate)]
    eventMap['liquidity'] = [x for x in eventMap['liquidity'] if inReportRange(x, startDate, endDate)]
    eventMap['bank'] = [x for x in eventMap['bank'] if inReportRange(x, startDate, endDate)]
    eventMap['gardens'] = [x for x in eventMap['gardens'] if inReportRange(x, startDate, endDate)]
    eventMap['quests'] = [x for x in eventMap['quests'] if inReportRange(x, startDate, endDate)]
    eventMap['alchemist'] = [x for x in eventMap['alchemist'] if inReportRange(x, startDate, endDate)]
    eventMap['airdrops'] = [x for x in eventMap['airdrops'] if inReportRange(x, startDate, endDate)]
    # Return all tax records combined and events
    return {
        'taxes': tavernData + swapData + liquidityData + bankData + gardensData + questData + airdropData + walletData,
        'events': eventMap
    }

# For preparing a list with correct sorting before searching through it to apply cost basis
def costBasisSort(eventList, costBasis):
    if costBasis == 'fifo':
        return sorted(eventList, key=lambda x: x.timestamp)
    elif costBasis == 'lifo':
        return sorted(eventList, key=lambda x: x.timestamp, reverse=True)
    elif costBasis == 'hifo':
        return sorted(eventList, key=lambda x: x.fiatReceiveValue / x.receiveAmount, reverse=True)
    else:
        return eventList

# Generate Auction House Tax records from the events
def buildTavernRecords(tavernEvents, startDate, endDate):
    results = []
    heroExpenses = {}
    heroIncome = {}
    landExpenses = {}
    # Grab a list of all purchases, summons, and levelups to list as expenses
    for event in tavernEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        if event.event in ['purchase','summon','crystal','meditate','levelup'] and eventDate >= startDate and eventDate <= endDate:
            if event.itemType == 'land':
                if event.itemID in landExpenses:
                    if event.event in landExpenses[event.itemID].description:
                        landExpenses[event.itemID].description = landExpenses[event.itemID].description.replace(event.event, '{0}+'.format(event.event))
                    else:
                        landExpenses[event.itemID].description += ''.join((' ', event.event))
                    landExpenses[event.itemID].costs += event.fiatAmount
                    if landExpenses[event.itemID].acquiredDate == None or eventDate < landExpenses[event.itemID].acquiredDate:
                        landExpenses[event.itemID].acquiredDate = eventDate
                else:
                    ti = TaxItem(event.txHash, event.coinCost, contracts.getAddressName(event.coinType), 0, '', '{2} {0} {1}'.format(event.itemID, event.event, event.itemType), 'expenses', None, event.fiatType, 0, eventDate, event.fiatAmount)
                    landExpenses[event.itemID] = ti
            else:
                if event.itemID in heroExpenses:
                    if event.event in heroExpenses[event.itemID].description:
                        heroExpenses[event.itemID].description = heroExpenses[event.itemID].description.replace(event.event, '{0}+'.format(event.event))
                    else:
                        heroExpenses[event.itemID].description += ''.join((' ', event.event))
                    heroExpenses[event.itemID].costs += event.fiatAmount
                    if heroExpenses[event.itemID].acquiredDate == None or eventDate < heroExpenses[event.itemID].acquiredDate:
                        heroExpenses[event.itemID].acquiredDate = eventDate
                else:
                    ti = TaxItem(event.txHash, event.coinCost, contracts.getAddressName(event.coinType), 0, '', '{2} {0} {1}'.format(event.itemID, event.event, event.itemType), 'expenses', None, event.fiatType, 0, eventDate, event.fiatAmount)
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
                ti = TaxItem(event.txHash, 0, '', event.coinCost, contracts.getAddressName(event.coinType), 'Hero {0} {1}'.format(event.itemID, event.event), 'income', eventDate, event.fiatType, event.fiatAmount)
                heroIncome[event.itemID] = ti

    for event in tavernEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        # Create a tax record for any sale event in the requested range
        if event.event == 'sale' and eventDate >= startDate and eventDate <= endDate:
            ti = TaxItem(event.txHash, 0, '', event.coinCost, contracts.getAddressName(event.coinType), 'Sold {1} {0}'.format(event.itemID, event.itemType), 'gains', eventDate, event.fiatType, event.fiatAmount)
            ti.amountNotAccounted = 1
            # Check NFT cost data so gains can be calculated
            if event.itemType == 'land':
                expenseList = landExpenses
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
            results.append(ti)
    for k, v in landExpenses.items():
        results.append(v)
    for k, v in heroExpenses.items():
        results.append(v)
    for k, v in heroIncome.items():
        results.append(v)
    return results

def buildSwapRecords(swapEvents, startDate, endDate, walletEvents, airdropEvents, gardensEvents, questEvents, costBasis):
    results = []
    #TODO Also search income for cost basis like bank gains and staking rewards
    for event in swapEvents:
        # swapping an item for gold does not need to be on tax report (I think)
        # questionable where to draw the line between game and currency trades
        if event.swapType in contracts.gold_values and event.receiveType == '0x3a4EDcf3312f44EF027acfd8c21382a5259936e7':
            continue
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        if eventDate >= startDate and eventDate <= endDate:
            ti = TaxItem(event.txHash, event.swapAmount, contracts.getAddressName(event.swapType), event.receiveAmount, contracts.getAddressName(event.receiveType), 'Sold {0:.5f} {1} for {2:.5f} {3}'.format(event.swapAmount, contracts.getAddressName(event.swapType), event.receiveAmount, contracts.getAddressName(event.receiveType)), 'gains', eventDate, event.fiatType, event.fiatSwapValue)
            # Check all transactions for prior time when sold token was received to calc gains
            cbList = costBasisSort(swapEvents, costBasis)
            for searchEvent in cbList:
                searchEventDate = datetime.date.fromtimestamp(searchEvent.timestamp)
                if searchEvent.receiveType == event.swapType and searchEvent.timestamp < event.timestamp and event.swapAmountNotAccounted > 0 and searchEvent.receiveAmountNotAccounted > 0:
                    # setting date here although it could get overwritten later if multiple recieves are used
                    # to account for single swap (likely)
                    if ti.acquiredDate == None:
                        ti.acquiredDate = searchEventDate
                    if ti.soldDate - ti.acquiredDate > datetime.timedelta(days=365):
                        ti.term = "long"
                    if searchEvent.receiveAmountNotAccounted <= event.swapAmountNotAccounted:
                        # use up all receive transaction amount and update amount left to match still
                        ti.costs += searchEvent.fiatReceiveValue * (searchEvent.receiveAmountNotAccounted / searchEvent.receiveAmount)
                        event.swapAmountNotAccounted -= searchEvent.receiveAmountNotAccounted
                        searchEvent.receiveAmountNotAccounted = 0
                    else:
                        # use up as much of recieve transaction as swap was for and update amount left to account for on receive
                        ti.costs += (searchEvent.fiatReceiveValue / searchEvent.receiveAmountNotAccounted) * event.swapAmountNotAccounted
                        searchEvent.receiveAmountNotAccounted -= event.swapAmountNotAccounted
                        event.swapAmountNotAccounted = 0
                        break
            # Also run through airdrop transactions to try and fill remaining gaps in received value accounting
            if event.swapAmountNotAccounted > 0:
                for airdropEvent in airdropEvents:
                    airdropEventDate = datetime.date.fromtimestamp(airdropEvent.timestamp)
                    # This can be removed after a clean of airdrops cached records
                    if not hasattr(airdropEvent, 'amountNotAccounted'):
                        airdropEvent.amountNotAccounted = airdropEvent.tokenAmount
                    if event.swapType == airdropEvent.tokenReceived and airdropEvent.amountNotAccounted > 0 and airdropEvent.timestamp < event.timestamp and event.swapAmountNotAccounted > 0:
                        if ti.acquiredDate == None:
                            ti.acquiredDate = airdropEventDate
                        if airdropEvent.amountNotAccounted <= event.swapAmountNotAccounted:
                            # use up all receive transaction amount and update amount left to match still
                            ti.costs += airdropEvent.fiatValue * (airdropEvent.amountNotAccounted / airdropEvent.tokenAmount)
                            event.swapAmountNotAccounted -= airdropEvent.amountNotAccounted
                            airdropEvent.amountNotAccounted = 0
                        else:
                            # use up as much of recieve transaction as swap was for and update amount left to account for on receive
                            ti.costs += (airdropEvent.fiatValue / airdropEvent.amountNotAccounted) * event.swapAmountNotAccounted
                            event.swapAmountNotAccounted = 0
                            airdropEvent.amountNotAccounted -= event.swapAmountNotAccounted
                            break
            # Also run through garden/farming staking reward transactions to try and fill remaining gaps in received value accounting
            if event.swapAmountNotAccounted > 0:
                for gardensEvent in gardensEvents:
                    gardensEventDate = datetime.date.fromtimestamp(gardensEvent.timestamp)
                    # This can be removed after a clean of gardens cached records
                    if not hasattr(gardensEvent, 'amountNotAccounted'):
                        gardensEvent.amountNotAccounted = gardensEvent.coinAmount
                    if event.swapType == gardensEvent.coinType and gardensEvent.amountNotAccounted > 0 and gardensEvent.timestamp < event.timestamp and event.swapAmountNotAccounted > 0:
                        if ti.acquiredDate == None:
                            ti.acquiredDate = gardensEventDate
                        if gardensEvent.amountNotAccounted <= event.swapAmountNotAccounted:
                            # use up all receive transaction amount and update amount left to match still
                            ti.costs += gardensEvent.fiatValue * (gardensEvent.amountNotAccounted / gardensEvent.coinAmount)
                            event.swapAmountNotAccounted -= gardensEvent.amountNotAccounted
                            gardensEvent.amountNotAccounted = 0
                        else:
                            # use up as much of recieve transaction as swap was for and update amount left to account for on receive
                            ti.costs += (gardensEvent.fiatValue / gardensEvent.amountNotAccounted) * event.swapAmountNotAccounted
                            event.swapAmountNotAccounted = 0
                            gardensEvent.amountNotAccounted -= event.swapAmountNotAccounted
                            break
            # Also run through quest transactions to try and fill remaining gaps in received value accounting
            if event.swapAmountNotAccounted > 0:
                for questEvent in questEvents:
                    questEventDate = datetime.date.fromtimestamp(questEvent.timestamp)
                    # This can be removed after a clean of quests cached records
                    if not hasattr(questEvent, 'amountNotAccounted'):
                        questEvent.amountNotAccounted = questEvent.rewardAmount
                    if event.swapType == questEvent.rewardType and questEvent.amountNotAccounted > 0 and questEvent.timestamp < event.timestamp and event.swapAmountNotAccounted > 0:
                        if ti.acquiredDate == None:
                            ti.acquiredDate = questEventDate
                        if questEvent.amountNotAccounted <= event.swapAmountNotAccounted:
                            # use up all receive transaction amount and update amount left to match still
                            ti.costs += questEvent.fiatValue * (questEvent.amountNotAccounted / questEvent.rewardAmount)
                            event.swapAmountNotAccounted -= questEvent.amountNotAccounted
                            questEvent.amountNotAccounted = 0
                        else:
                            # use up as much of recieve transaction as swap was for and update amount left to account for on receive
                            ti.costs += (questEvent.fiatValue / questEvent.amountNotAccounted) * event.swapAmountNotAccounted
                            event.swapAmountNotAccounted = 0
                            questEvent.amountNotAccounted -= event.swapAmountNotAccounted
                            break
            # Also run through direct wallet transactions to try and fill remaining gaps in received value accounting
            # This works assuming the asset was purchased on same day it was transferred in, TODO: maybe add to disclaimer/FAQ
            if event.swapAmountNotAccounted > 0:
                for walletEvent in walletEvents:
                    walletEventDate = datetime.date.fromtimestamp(walletEvent.timestamp)
                    if walletEvent.action in ['deposit','payment'] and event.swapType == walletEvent.coinType and walletEvent.amountNotAccounted > 0 and walletEvent.timestamp < event.timestamp and event.swapAmountNotAccounted > 0:
                        if ti.acquiredDate == None:
                            ti.acquiredDate = walletEventDate
                        if walletEvent.amountNotAccounted <= event.swapAmountNotAccounted:
                            # use up all receive transaction amount and update amount left to match still
                            ti.costs += walletEvent.fiatValue * (walletEvent.amountNotAccounted / walletEvent.coinAmount)
                            event.swapAmountNotAccounted -= walletEvent.amountNotAccounted
                            walletEvent.amountNotAccounted = 0
                        else:
                            # use up as much of recieve transaction as swap was for and update amount left to account for on receive
                            ti.costs += (walletEvent.fiatValue / walletEvent.amountNotAccounted) * event.swapAmountNotAccounted
                            event.swapAmountNotAccounted = 0
                            walletEvent.amountNotAccounted -= event.swapAmountNotAccounted
                            break
            # Note any amount of cost basis not found for later red flag
            ti.amountNotAccounted = event.swapAmountNotAccounted

            results.append(ti)

    # TODO Also list unmatched received tokens in current assets

    return results

def buildLiquidityRecords(liquidityEvents, startDate, endDate):
    results = []
    for event in liquidityEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        # Withdrawal from liquidity pool triggers realized growth or loss, make tax item and find cost basis
        if event.action == 'withdraw' and eventDate >= startDate and eventDate <= endDate:
            ti = TaxItem(event.txHash, event.poolAmount, contracts.getAddressName(event.poolAddress), '{0}/{1}'.format(event.coin1Amount, event.coin2Amount), '{0}/{1}'.format(contracts.getAddressName(event.coin1Type), contracts.getAddressName(event.coin2Type)), 'Liquidity Withdrawal {0}'.format(contracts.getAddressName(event.poolAddress)), 'gains', eventDate, event.fiatType, event.coin1FiatValue + event.coin2FiatValue)
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
                        ti.costs += (searchEventTotalValue / searchEvent.amountNotAccounted) * event.amountNotAccounted
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
    for event in bankEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        # Withdrawal from Bank triggers realized xJewel rewards, make tax item and find cost basis
        if event.action == 'withdraw' and eventDate >= startDate and eventDate <= endDate:
            ti = TaxItem(event.txHash, 0, '', event.coinAmount, contracts.getAddressName(event.coinType), 'Bank Rewards {0}'.format(contracts.getAddressName(event.coinType)), 'income', eventDate, event.fiatType, event.fiatValue)
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
                        ti.costs += (jewelPrice * searchEvent.coinAmount) * (searchEvent.amountNotAccounted / searchEvent.coinAmount) * (searchEvent.xRate / event.xRate)
                        event.amountNotAccounted -= searchEvent.amountNotAccounted
                        searchEvent.amountNotAccounted = 0
                    else:
                        # deposit is larger than remaining cost basis we need to find so use part of it
                        ti.costs += ((jewelPrice * searchEvent.coinAmount) / searchEvent.amountNotAccounted) * event.amountNotAccounted * (searchEvent.xRate / event.xRate)
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
                ti = TaxItem(event.txHash, 0, '', event.coinAmount, contracts.getAddressName(event.coinType), '{0} Staking Reward'.format(contracts.getAddressName(event.coinType)), 'income', eventDate, event.fiatType, event.fiatValue)
                # Not really!
                ti.costs = event.coinAmount
                ti.amountNotAccounted = 0
                rewardGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.event))] = ti

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
        # Create basic income tax record for any airdrop
        if eventDate >= startDate and eventDate <= endDate:
            if event.tokenAmount % 1 > 0:
                desc = '{2} {0:.3f} {1}'.format(event.tokenAmount, contracts.getAddressName(event.tokenReceived), eventTitle)
            else:
                desc = '{2} {0} {1}'.format(int(event.tokenAmount), contracts.getAddressName(event.tokenReceived), eventTitle)
            ti = TaxItem(event.txHash, 0, '', event.tokenAmount, contracts.getAddressName(event.tokenReceived), desc, 'income', eventDate, event.fiatType, event.fiatValue)
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
        if event.rewardType == '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F' and eventDate >= startDate and eventDate <= endDate:
            if ''.join((eventDate.strftime('%d-%m-%Y'), event.rewardType)) in itemGroups:
                itemGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.rewardType))].proceeds += event.fiatValue
                # this is hacky, but I'm just gonna use it to keep track of total jewel since it is not needed
                itemGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.rewardType))].costs += event.rewardAmount
            else:
                ti = TaxItem(event.txHash, 0, '', event.rewardAmount, contracts.getAddressName(event.rewardType), 'Quest Jewel Rewards', 'income', eventDate, event.fiatType, event.fiatValue)
                # Not really!
                ti.costs = event.rewardAmount
                itemGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.rewardType))] = ti
    for k, v in itemGroups.items():
        v.description = 'Quest Jewel Rewards {:.3f}'.format(v.costs)
        v.rcvdAmount = v.costs
        # zero out costs because we were just using it to trace the sum of coin amount
        v.costs = 0
        v.amountNotAccounted = 0
        results.append(v)

    return results

# Generate Payment income Tax events
def buildPaymentRecords(walletEvents, startDate, endDate):
    results = []
    # use dict to summarize payments by type/day
    itemGroups = {}
    for event in walletEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        # Create basic income tax record for any wallet deposit from a payment address
        if event.action == 'payment' and eventDate >= startDate and eventDate <= endDate:
            if ''.join((eventDate.strftime('%d-%m-%Y'), event.coinType)) in itemGroups:
                itemGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.coinType))].proceeds += event.fiatValue
                # this is hacky, but I'm just gonna use it to keep track of total jewel since it is not needed
                itemGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.coinType))].costs += event.coinAmount
            else:
                ti = TaxItem(event.txHash, 0, '', event.coinAmount, contracts.getAddressName(event.coinType), 'Payment', 'income', eventDate, event.fiatType, event.fiatValue)
                # Not really!
                ti.costs = event.coinAmount
                itemGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.coinType))] = ti
    for k, v in itemGroups.items():
        v.description += ' {0:.3f} {1}'.format(v.costs, v.rcvdType)
        # zero out costs because we were just using it to trace the sum of coin amount
        v.costs = 0
        v.amountNotAccounted = 0
        results.append(v)

    return results