#!/usr/bin/env python3
import events
import contracts
import datetime
import logging
import db

# Record for final tax report data
class TaxItem:
    def __init__(self, description, category, soldDate, proceeds=0, acquiredDate=None, costs=0, term="short"):
        self.description = description
        # gains, income, or expenses
        self.category = category
        self.acquiredDate = acquiredDate
        self.soldDate = soldDate
        self.proceeds = proceeds
        self.costs = costs
        self.term = term
        self.amountNotAccounted = proceeds
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
def buildTaxMap(txns, account, startDate, endDate, costBasis):
    # Generate map of all events from transaction list
    logging.info('Start Event map build')
    eventMap = events.checkTransactions(txns, account, startDate, endDate)
    # Have to look up Tavern sales events because they are not associated direct to wallet
    eventMap['tavern'] += db.getTavernSales(account, startDate, endDate)
    # Map the events into tax records
    logging.info('Start Tax mapping {0}'.format(account))
    # temporarily dedupe this list until I can find root cause
    cleanTavern = []
    for rec in eventMap['tavern']:
        if rec not in cleanTavern:
            cleanTavern.append(rec)
        else:
            logging.info('eliminated duplicate event {1} {0} on {2}'.format(rec.itemID, rec.event, str(rec.timestamp)))
    eventMap['tavern'] = cleanTavern
    tavernData = buildTavernRecords(eventMap['tavern'], startDate, endDate)
    swapData = buildSwapRecords(eventMap['swaps'], startDate, endDate, eventMap['wallet'], costBasis)
    liquidityData = buildLiquidityRecords(eventMap['liquidity'], startDate, endDate)
    bankData = buildBankRecords(eventMap['bank'], startDate, endDate)
    gardensData = buildGardensRecords(eventMap['gardens'], startDate, endDate)
    questData = buildQuestRecords(eventMap['quests'], startDate, endDate)
    airdropData = buildAirdropRecords(eventMap['airdrops'], startDate, endDate)
    # pop out all events not in date range
    eventMap['tavern'] = [x for x in eventMap['tavern'] if inReportRange(x, startDate, endDate)]
    eventMap['swaps'] = [x for x in eventMap['swaps'] if inReportRange(x, startDate, endDate)]
    eventMap['wallet'] = [x for x in eventMap['wallet'] if inReportRange(x, startDate, endDate)]
    eventMap['liquidity'] = [x for x in eventMap['liquidity'] if inReportRange(x, startDate, endDate)]
    eventMap['bank'] = [x for x in eventMap['bank'] if inReportRange(x, startDate, endDate)]
    eventMap['gardens'] = [x for x in eventMap['gardens'] if inReportRange(x, startDate, endDate)]
    eventMap['quests'] = [x for x in eventMap['quests'] if inReportRange(x, startDate, endDate)]
    eventMap['airdrops'] = [x for x in eventMap['airdrops'] if inReportRange(x, startDate, endDate)]
    # Return all tax records combined and events
    return {
        'taxes': tavernData + swapData + liquidityData + bankData + gardensData + questData + airdropData,
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

# Generate Trader Auction House Tax records from the events
def buildTavernRecords(tavernEvents, startDate, endDate):
    results = []
    heroExpenses = {}
    # Grab a list of all hero purchases and hires to list as expenses
    for event in tavernEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        if (event.event in ['purchase','hire','summon','crystal','meditate','levelup']) and eventDate >= startDate and eventDate <= endDate:
            if event.itemID in heroExpenses:
                if event.event in heroExpenses[event.itemID].description:
                    heroExpenses[event.itemID].description = heroExpenses[event.itemID].description.replace(event.event, '{0}+'.format(event.event))
                else:
                    heroExpenses[event.itemID].description += ''.join((',', event.event))
                heroExpenses[event.itemID].costs += event.fiatAmount
                if eventDate < heroExpenses[event.itemID].acquiredDate:
                    heroExpenses[event.itemID].acquiredDate = eventDate
            else:
                ti = TaxItem('Hero {0} {1}'.format(event.itemID, event.event), 'expenses', None, 0, eventDate, event.fiatAmount)
                heroExpenses[event.itemID] = ti

    for event in tavernEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        # Create a tax record for any sale event in the requested range
        if event.event == 'sale' and eventDate >= startDate and eventDate <= endDate:
            ti = TaxItem('Sold Hero {0}'.format(event.itemID), 'gains', eventDate, event.fiatAmount)
            ti.amountNotAccounted = 1
            # Check hero cost data so gains can be calculated
            for k, v in heroExpenses.items():
                if k == event.itemID and v.acquiredDate <= eventDate:
                    ti.acquiredDate = v.acquiredDate
                    ti.costs = v.costs
                    ti.amountNotAccounted = 0
                    if ti.soldDate - ti.acquiredDate > 365:
                        ti.term = "long"
                    del heroExpenses[k]
            results.append(ti)

    for k, v in heroExpenses.items():
        results.append(v)
    return results

def buildSwapRecords(swapEvents, startDate, endDate, walletEvents, costBasis):
    results = []
    for event in swapEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        if eventDate >= startDate and eventDate <= endDate:
            swapType = event.swapType
            receiveType = event.receiveType
            if swapType in contracts.address_map:
                swapType = contracts.address_map[swapType]
            if receiveType in contracts.address_map:
                receiveType = contracts.address_map[receiveType]
            ti = TaxItem('Sold {0:.3f} {1} for {2:.3f} {3}'.format(event.swapAmount, swapType, event.receiveAmount, receiveType), 'gains', eventDate, event.fiatSwapValue)
            # Check all transactions for prior time when sold token was received to calc gains
            cbList = costBasisSort(swapEvents, costBasis)
            for searchEvent in cbList:
                searchEventDate = datetime.date.fromtimestamp(searchEvent.timestamp)
                if searchEvent.receiveType == event.swapType and searchEvent.timestamp < event.timestamp and event.swapAmountNotAccounted > 0 and searchEvent.receiveAmountNotAccounted > 0:
                    # setting date here although it could get overwritten later if multiple recieves are used
                    # to account for single swap (likely)
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
            # Also run through direct wallet transactions to try and fill remaining gaps in received value accounting
            # This works assuming the asset was purchased on same day it was transferred in, TODO: maybe add to disclaimer/FAQ
            if event.swapAmountNotAccounted > 0:
                for walletEvent in walletEvents:
                    walletEventDate = datetime.date.fromtimestamp(walletEvent.timestamp)
                    if walletEvent.action == 'deposit' and event.swapType == walletEvent.coinType and walletEvent.amountNotAccounted > 0 and walletEvent.timestamp < event.timestamp and event.swapAmountNotAccounted > 0:
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
            poolAddress = event.poolAddress
            if poolAddress in contracts.address_map:
                poolAddress = contracts.address_map[poolAddress]
            ti = TaxItem('Liquidity Withdrawal {0}'.format(poolAddress), 'gains', eventDate, event.coin1FiatValue + event.coin2FiatValue)
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
            coinType = event.coinType
            if coinType in contracts.address_map:
                coinType = contracts.address_map[coinType]
            ti = TaxItem('Bank Rewards {0}'.format(coinType), 'income', eventDate, event.fiatValue)
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
            if ''.join((eventDate.strftime('%d-%m-%Y'), event.event)) in rewardGroups:
                rewardGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.event))].proceeds += event.fiatValue
                # this is hacky, but I'm just gonna use it to keep track of total jewel since it is not needed
                rewardGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.event))].costs += event.coinAmount
            else:
                ti = TaxItem('Gardens Staking Reward', 'income', eventDate, event.fiatValue)
                # Not really!
                ti.costs = event.coinAmount
                ti.amountNotAccounted = 0
                rewardGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.event))] = ti

    for k, v in rewardGroups.items():
        v.description = 'Gardens Staking Reward {:.3f}'.format(v.costs)
        v.costs = 0
        results.append(v)
    return results

# Generate Airdrop Tax events
def buildAirdropRecords(airdropEvents, startDate, endDate):
    results = []
    for event in airdropEvents:
        eventDate = datetime.date.fromtimestamp(event.timestamp)
        # Create basic income tax record for any airdrop
        if eventDate >= startDate and eventDate <= endDate:
            ti = TaxItem('Airdrop {0} {1}'.format(event.tokenAmount, event.tokenReceived), 'income', eventDate, event.fiatValue)
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
                ti = TaxItem('Quest Jewel Rewards', 'income', eventDate, event.fiatValue)
                # Not really!
                ti.costs = event.rewardAmount
                itemGroups[''.join((eventDate.strftime('%d-%m-%Y'), event.rewardType))] = ti
    for k, v in itemGroups.items():
        v.description = 'Quest Jewel Rewards {:.3f}'.format(v.costs)
        # zero out costs because we were just using it to trace the sum of coin amount
        v.costs = 0
        results.append(v)

    return results