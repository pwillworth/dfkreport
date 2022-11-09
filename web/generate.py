#!/usr/bin/env python3
"""

 Copyright 2021 Paul Willworth <ioscode@gmail.com>

"""

import sys
import cgi
import urllib.parse
from datetime import timezone, datetime, date
from web3 import Web3
sys.path.append("../")
import transactions
import contracts
import db
import csvFormats
import pymysql
import pickle
import jsonpickle
import logging


def getResponseCSV(records, contentType, format):
    taxRecords = records['taxes']
    eventRecords = records['events']

    if contentType == 'transaction' or format in ['koinlyuniversal','coinledgeruniversal']:
        # translate output based on req format
        response = csvFormats.getHeaderRow(format)
        for record in eventRecords['tavern']:
            blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(csvFormats.getDateFormat(format))
            txFee = ''
            txFeeCurrency = ''
            if hasattr(record, 'fiatFeeValue'):
                txFee = record.fiatFeeValue
                txFeeCurrency = 'USD'
            if format in ['koinlyuniversal','coinledgeruniversal']:
                if record.event == 'sale' or record.event == 'hire':
                    sentAmount = ''
                    sentType = ''
                    rcvdAmount = record.coinCost
                    rcvdType = contracts.getAddressName(record.coinType)
                else:
                    sentAmount = record.coinCost
                    sentType = contracts.getAddressName(record.coinType)
                    rcvdAmount = ''
                    rcvdType = ''

            label = csvFormats.getRecordLabel(format, 'tavern', record.event)
            if format == 'koinlyuniversal':
                response += ','.join((blockDateStr, str(sentAmount), sentType, str(rcvdAmount), rcvdType, str(txFee), txFeeCurrency, str(record.fiatAmount), record.fiatType, label, 'NFT {0} {1}'.format(record.itemID, record.event), record.txHash, '\n'))
            elif format == 'coinledgeruniversal':
                response += ','.join((blockDateStr, 'Defi Kingdoms', sentType, str(sentAmount), rcvdType, str(rcvdAmount), txFeeCurrency, str(txFee), label, 'NFT {0} {1}'.format(record.itemID, record.event), record.txHash, '\n'))
            else:
                response += ','.join(('tavern', blockDateStr, record.event, record.itemType, str(record.itemID), contracts.getAddressName(record.coinType), str(record.coinCost), '', str(record.fiatAmount), record.txHash, str(txFee), '\n'))
        for record in eventRecords['swaps']:
            blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(csvFormats.getDateFormat(format))
            txFee = ''
            txFeeCurrency = ''
            if hasattr(record, 'fiatFeeValue'):
                txFee = record.fiatFeeValue
                txFeeCurrency = 'USD'
            if format == 'koinlyuniversal':
                response += ','.join((blockDateStr, str(record.swapAmount), contracts.getAddressName(record.swapType), str(record.receiveAmount), contracts.getAddressName(record.receiveType), str(txFee), txFeeCurrency, str(record.fiatSwapValue), record.fiatType, '', 'swap', record.txHash, '\n'))
            elif format == 'coinledgeruniversal':
                response += ','.join((blockDateStr, 'Defi Kingdoms', contracts.getAddressName(record.swapType), str(record.swapAmount), contracts.getAddressName(record.receiveType), str(record.receiveAmount), txFeeCurrency, str(txFee), '', 'Trade', record.txHash, '\n'))
            else:
                response += ','.join(('trader', blockDateStr, 'swap', contracts.getAddressName(record.swapType), str(record.swapAmount), contracts.getAddressName(record.receiveType), str(record.receiveAmount), str(record.fiatSwapValue), str(record.fiatReceiveValue), record.txHash, str(txFee), '\n'))
        for record in eventRecords['liquidity']:
            blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(csvFormats.getDateFormat(format))
            txFee = ''
            txFeeCurrency = ''
            if hasattr(record, 'fiatFeeValue'):
                txFee = record.fiatFeeValue
                txFeeCurrency = 'USD'
            if format == 'koinlyuniversal':
                if record.action == 'withdraw':
                    response += ','.join((blockDateStr, '', '', str(record.coin1Amount), contracts.getAddressName(record.coin1Type), str(txFee), txFeeCurrency, str(record.coin1FiatValue), record.fiatType, '', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getAddressName(record.poolAddress)), record.txHash, '\n'))
                    response += ','.join((blockDateStr, '', '', str(record.coin2Amount), contracts.getAddressName(record.coin2Type), str(txFee), txFeeCurrency, str(record.coin1FiatValue), record.fiatType, '', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getAddressName(record.poolAddress)), record.txHash, '\n'))
                else:
                    response += ','.join((blockDateStr, str(record.coin1Amount), contracts.getAddressName(record.coin1Type), '', '', str(txFee), txFeeCurrency, str(record.coin1FiatValue), record.fiatType, '', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getAddressName(record.poolAddress)), record.txHash, '\n'))
                    response += ','.join((blockDateStr, str(record.coin2Amount), contracts.getAddressName(record.coin2Type), '', '', str(txFee), txFeeCurrency, str(record.coin1FiatValue), record.fiatType, '', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getAddressName(record.poolAddress)), record.txHash, '\n'))
            elif format == 'coinledgeruniversal':
                if record.action == 'withdraw':
                    response += ','.join((blockDateStr, 'Defi Kingdoms', '', '', contracts.getAddressName(record.coin1Type), str(record.coin1Amount), txFeeCurrency, str(txFee), 'Deposit', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getAddressName(record.poolAddress)), record.txHash, '\n'))
                    response += ','.join((blockDateStr, 'Defi Kingdoms', '', '', contracts.getAddressName(record.coin2Type), str(record.coin2Amount), txFeeCurrency, str(txFee), 'Deposit', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getAddressName(record.poolAddress)), record.txHash, '\n'))
                else:
                    response += ','.join((blockDateStr, 'Defi Kingdoms', contracts.getAddressName(record.coin1Type), str(record.coin1Amount), '', '', txFeeCurrency, str(txFee), 'Withdrawal', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getAddressName(record.poolAddress)), record.txHash, '\n'))
                    response += ','.join((blockDateStr, 'Defi Kingdoms', contracts.getAddressName(record.coin2Type), str(record.coin2Amount), '', '', txFeeCurrency, str(txFee), 'Withdrawal', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getAddressName(record.poolAddress)), record.txHash, '\n'))
            else:
                response += ','.join(('liquidity', blockDateStr, '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getAddressName(record.poolAddress)), contracts.getAddressName(record.coin1Type), str(record.coin1Amount), contracts.getAddressName(record.coin2Type), str(record.coin2Amount), str(record.coin1FiatValue), str(record.coin2FiatValue), record.txHash, str(txFee), '\n'))
        for record in eventRecords['gardens']:
            blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(csvFormats.getDateFormat(format))
            txFee = ''
            txFeeCurrency = ''
            if hasattr(record, 'fiatFeeValue'):
                txFee = record.fiatFeeValue
                txFeeCurrency = 'USD'
            if format in ['koinlyuniversal','coinledgeruniversal']:
                if record.event == 'deposit':
                    sentAmount = record.coinAmount
                    sentType = contracts.getAddressName(record.coinType)
                    rcvdAmount = ''
                    rcvdType = ''
                else:
                    sentAmount = ''
                    sentType = ''
                    rcvdAmount = record.coinAmount
                    rcvdType = contracts.getAddressName(record.coinType)
            label = csvFormats.getRecordLabel(format, 'tavern', record.event)
            if format == 'koinlyuniversal':
                response += ','.join((blockDateStr, str(sentAmount), sentType, str(rcvdAmount), rcvdType, str(txFee), txFeeCurrency, str(record.fiatValue), record.fiatType, label, record.event, record.txHash, '\n'))
            elif format == 'coinledgeruniversal':
                response += ','.join((blockDateStr, 'Defi Kingdoms', sentType, str(sentAmount), rcvdType, str(rcvdAmount), txFeeCurrency, str(txFee), label, record.event, record.txHash, '\n'))
            else:
                if 'Pangolin LP' in contracts.getAddressName(record.coinType):
                    location = 'Pangolin'
                elif 'Crystal LP' in contracts.getAddressName(record.coinType):
                    location = 'Crystalvale'
                else:
                    location = 'Serendale'
                response += ','.join((location, blockDateStr, record.event, contracts.getAddressName(record.coinType), str(record.coinAmount), '', '', str(record.fiatValue), '', record.txHash, str(txFee), '\n'))
        for record in eventRecords['bank']:
            blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(csvFormats.getDateFormat(format))
            txFee = ''
            txFeeCurrency = ''
            if hasattr(record, 'fiatFeeValue'):
                txFee = record.fiatFeeValue
                txFeeCurrency = 'USD'
            if format in ['koinlyuniversal','coinledgeruniversal']:
                if record.action == 'deposit':
                    sentAmount = record.coinAmount
                    sentType = contracts.getAddressName(record.coinType)
                    rcvdAmount = record.coinAmount / record.xRate
                    rcvdType = 'xJewel'
                else:
                    sentAmount = record.coinAmount / record.xRate
                    sentType = 'xJewel'
                    rcvdAmount = record.coinAmount
                    rcvdType = contracts.getAddressName(record.coinType)
            if format == 'koinlyuniversal':
                response += ','.join((blockDateStr, str(sentAmount), sentType, str(rcvdAmount), rcvdType, str(txFee), txFeeCurrency, str(record.fiatValue), record.fiatType, '', 'bank {0}'.format(record.action), record.txHash, '\n'))
            elif format == 'coinledgeruniversal':
                response += ','.join((blockDateStr, 'Defi Kingdoms', sentType, str(sentAmount), rcvdType, str(rcvdAmount), txFeeCurrency, str(txFee), '', 'bank {0}'.format(record.action), record.txHash, '\n'))
            else:
                response += ','.join(('bank', blockDateStr, record.action, 'xRate', str(record.xRate), contracts.getAddressName(record.coinType), str(record.coinAmount), '', str(record.fiatValue), record.txHash, str(txFee), '\n'))
        for record in eventRecords['alchemist']:
            blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(csvFormats.getDateFormat(format))
            txFee = ''
            txFeeCurrency = ''
            if hasattr(record, 'fiatFeeValue'):
                txFee = record.fiatFeeValue
                txFeeCurrency = 'USD'
            if format == 'koinlyuniversal':
                response += ','.join((blockDateStr, '', '"' + record.craftingCosts + '"', str(record.craftingAmount), contracts.getAddressName(record.craftingType), str(txFee), txFeeCurrency, str(record.fiatValue), record.fiatType, 'ignored', 'potion crafting', record.txHash, '\n'))
            elif format == 'coinledgeruniversal':
                response += ','.join((blockDateStr, 'Defi Kingdoms', '"' + record.craftingCosts + '"', '', contracts.getAddressName(record.craftingType), str(record.craftingAmount), txFeeCurrency, str(txFee), 'Deposit', 'potion crafting', record.txHash, '\n'))
            else:
                response += ','.join(('alchemist', blockDateStr, 'crafting', contracts.getAddressName(record.craftingType), str(record.craftingAmount), '"' + record.craftingCosts + '"', '', str(record.fiatValue), str(record.costsFiatValue), record.txHash, str(txFee), '\n'))
        for record in eventRecords['airdrops']:
            blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(csvFormats.getDateFormat(format))
            txFee = ''
            txFeeCurrency = ''
            if hasattr(record, 'fiatFeeValue'):
                txFee = record.fiatFeeValue
                txFeeCurrency = 'USD'
            if format == 'koinlyuniversal':
                response += ','.join((blockDateStr, '', '', str(record.tokenAmount), contracts.getAddressName(record.tokenReceived), str(txFee), txFeeCurrency, str(record.fiatValue), record.fiatType, 'airdrop', '', record.txHash, '\n'))
            elif format == 'coinledgeruniversal':
                response += ','.join((blockDateStr, 'Defi Kingdoms', '', '', contracts.getAddressName(record.tokenReceived), str(record.tokenAmount), txFeeCurrency, str(txFee), 'Airdrop', '', record.txHash, '\n'))
            else:
                response += ','.join(('airdrops', blockDateStr, '', contracts.getAddressName(record.tokenReceived), str(record.tokenAmount), '', '', str(record.fiatValue), '', record.txHash, str(txFee), '\n'))
        for record in eventRecords['quests']:
            blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(csvFormats.getDateFormat(format))
            txFee = ''
            txFeeCurrency = ''
            if hasattr(record, 'fiatFeeValue'):
                txFee = record.fiatFeeValue
                txFeeCurrency = 'USD'
            if format == 'koinlyuniversal':
                response += ','.join((blockDateStr, '', '', str(record.rewardAmount), contracts.getAddressName(record.rewardType), str(txFee), txFeeCurrency, str(record.fiatValue), record.fiatType, 'reward', 'quest', record.txHash, '\n'))
            elif format == 'coinledgeruniversal':
                response += ','.join((blockDateStr, '', '', contracts.getAddressName(record.rewardType), str(record.rewardAmount), txFeeCurrency, str(txFee), 'Staking', 'quest', record.txHash, '\n'))
            else:
                response += ','.join(('quest', blockDateStr, 'rewards', contracts.getAddressName(record.rewardType), str(record.rewardAmount), '', '', str(record.fiatValue), '', record.txHash, str(txFee), '\n'))
        for record in eventRecords['wallet']:
            blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(csvFormats.getDateFormat(format))
            txFee = ''
            txFeeCurrency = ''
            if hasattr(record, 'fiatFeeValue'):
                txFee = record.fiatFeeValue
                txFeeCurrency = 'USD'
            if format in ['koinlyuniversal','coinledgeruniversal']:
                if record.action == 'deposit':
                    sentAmount = ''
                    sentType = ''
                    rcvdAmount = record.coinAmount
                    rcvdType = contracts.getAddressName(record.coinType)
                else:
                    sentAmount = record.coinAmount
                    sentType = contracts.getAddressName(record.coinType)
                    rcvdAmount = ''
                    rcvdType = ''
            if format == 'koinlyuniversal':
                response += ','.join((blockDateStr, str(sentAmount), sentType, str(rcvdAmount), rcvdType, str(txFee), txFeeCurrency, str(record.fiatValue), record.fiatType, '', 'wallet transfer', record.txHash, '\n'))
            elif format == 'coinledgeruniversal':
                response += ','.join((blockDateStr, 'Defi Kingdoms', sentType, str(sentAmount), rcvdType, str(rcvdAmount), txFeeCurrency, str(txFee), record.action, 'wallet transfer', record.txHash, '\n'))
            else:
                response += ','.join(('wallet', blockDateStr, record.action, contracts.getAddressName(record.coinType), str(record.coinAmount), '', '', str(record.fiatValue), '', record.txHash, str(txFee), '\n'))
        if 'lending' in eventRecords:
            for record in eventRecords['lending']:
                blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(csvFormats.getDateFormat(format))
                txFee = ''
                txFeeCurrency = ''
                if hasattr(record, 'fiatFeeValue'):
                    txFee = record.fiatFeeValue
                    txFeeCurrency = 'USD'
                if format in ['koinlyuniversal','coinledgeruniversal']:
                    if record.event in ['redeem','borrow']:
                        sentAmount = ''
                        sentType = ''
                        rcvdAmount = record.coinAmount
                        rcvdType = contracts.getAddressName(record.coinType)
                    else:
                        sentAmount = record.coinAmount
                        sentType = contracts.getAddressName(record.coinType)
                        rcvdAmount = ''
                        rcvdType = ''
                if format == 'koinlyuniversal':
                    response += ','.join((blockDateStr, str(sentAmount), sentType, str(rcvdAmount), rcvdType, str(txFee), txFeeCurrency, str(record.fiatValue), record.fiatType, '', 'lending {0}'.format(record.event), record.txHash, '\n'))
                elif format == 'coinledgeruniversal':
                    response += ','.join((blockDateStr, sentType, str(sentAmount), rcvdType, str(rcvdAmount), txFeeCurrency, str(txFee), '', 'lending {0}'.format(record.event), record.txHash, '\n'))
                else:
                    response += ','.join(('lending', blockDateStr, record.event, contracts.getAddressName(record.coinType), str(record.coinAmount), '', '', str(record.fiatValue), '', record.txHash, str(txFee), '\n'))
    else:
        response = 'category,description,acquired date,sold date,proceeds,costs,gains,term,basis amt not accounted,txHash\n'

        for record in taxRecords:
            acquiredDateStr = ''
            soldDateStr = ''
            if record.acquiredDate != None:
                acquiredDateStr = record.acquiredDate.strftime('%Y-%m-%d')
            if record.soldDate != None:
                soldDateStr = record.soldDate.strftime('%Y-%m-%d')
            response += ','.join((record.category,record.description,acquiredDateStr,soldDateStr,str(record.proceeds),str(record.costs),str(record.get_gains()),record.term,str(record.amountNotAccounted), record.txHash, '\n'))

    return response

def getResponseJSON(results, contentType, eventGroup='all'):
    taxRecords = results['taxes']
    eventRecords = results['events']
    response = '{ "response" : {\n'
    response += '  "status" : "complete",\n   '
    if contentType == 'transaction':
        response += '  "event_records" : \n   '
        if eventGroup != 'all':
            response += '  {"' + eventGroup + '" : \n'
            response += jsonpickle.encode(eventRecords[eventGroup], make_refs=False)
            response += '  }'
        else:
            response += jsonpickle.encode(eventRecords, make_refs=False)
    else:
        response += '  "tax_records" : [\n   '
        for record in taxRecords:
            acquiredDateStr = ''
            soldDateStr = ''
            if record.acquiredDate != None:
                acquiredDateStr = record.acquiredDate.strftime('%Y-%m-%d')
            if record.soldDate != None:
                soldDateStr = record.soldDate.strftime('%Y-%m-%d')

            response += '  {\n'
            response += '  "category" : "{0}",\n'.format(record.category)
            response += '  "description" : "{0}",\n'.format(record.description)
            response += '  "acquiredDate" : "{0}",\n'.format(acquiredDateStr)
            response += '  "soldDate" : "{0}",\n'.format(soldDateStr)
            response += '  "proceeds" : "{0}",\n'.format(record.proceeds)
            response += '  "costs" : "{0}",\n'.format(record.costs)
            response += '  "gains" : "{0}",\n'.format(record.get_gains())
            response += '  "term"  : "{0}",\n'.format(record.term)
            if hasattr(record, 'txFees'):
                response += '  "txFees" : "{0}",\n'.format(record.txFees)
            response += '  "amountNotAccounted"  : "{0}"\n'.format(record.amountNotAccounted)
            response += '  }, \n'

        # trim off extra comma
        response = response[:-3]
        response += '  ],\n'
        response += '  "gasValue" : "{0}"\n'.format(results['events']['gas'])
    response += '  }\n}'

    if len(eventRecords) == 0:
        response = '{ "response" : "Error: No events found for that wallet and date range." }'

    return response

# Get an existing report record or create a new one and return it
def getReportStatus(wallet, startDate, endDate, costBasis, includedChains, otherOptions):
    reportRow = db.findReport(wallet, startDate, endDate)
    if reportRow != None:
        if (reportRow[11] == costBasis and reportRow[12] == includedChains) or reportRow[10] == 1:
            # if cost basis same or its different but report still running, just return existing
            return reportRow
        else:
            # wipe the old report and re-map for new options or transactions
            logging.debug('updating existing report row to regenerate')
            result = transactions.getTransactionCount(wallet)
            if len(result) == 3:
                generateTime = datetime.now(timezone.utc)
                totalTx = result[0] + result[1] + result[2]
                db.resetReport(wallet, startDate, endDate, int(datetime.timestamp(generateTime)), totalTx, costBasis, includedChains, reportRow[8], reportRow[9])
                return [reportRow[0], reportRow[1], reportRow[2], int(datetime.timestamp(generateTime)), totalTx]
            else:
                return 'Error: No Transactions for that wallet found'
    else:
        logging.debug('start new report row')
        result = transactions.getTransactionCount(wallet, includedChains)
        if len(result) == 3:
            generateTime = datetime.now(timezone.utc)
            totalTx = result[0] + result[1] + result[2]
            db.createReport(wallet, startDate, endDate, int(datetime.timestamp(generateTime)), totalTx, costBasis, includedChains, None, jsonpickle.dumps(otherOptions))
            report = db.findReport(wallet, startDate, endDate)
            logging.debug(str([report[0], report[1], report[2], report[3], report[4]]))
            return [report[0], report[1], report[2], report[3], report[4]]
        else:
            return 'Error: No Transactions for that wallet found'

logging.basicConfig(filename='../generate.log', level=logging.WARNING, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
# Extract query parameters
form = cgi.FieldStorage()

wallet = form.getfirst('walletAddress', '')
startDate = form.getfirst('startDate', '')
endDate = form.getfirst('endDate', '')
includeHarmony = form.getfirst('includeHarmony', 'on')
includeDFKChain = form.getfirst('includeDFKChain', 'on')
includeAvalanche = form.getfirst('includeAvalanche', 'false')
costBasis = form.getfirst('costBasis', 'fifo')
# can be set to csv, otherwise json response is returned
formatType = form.getfirst('formatType', '')
# can be tax or transaction, only used for CSV
contentType = form.getfirst('contentType', '')
# can by koinlyuniversal or anything else for default
csvFormat = form.getfirst('csvFormat', 'manual')
# can be any event group to return only that group of events instead of all
eventGroup = form.getfirst('eventGroup', 'all')
# Allow for specifying addresses that transfers to should be considered purchases and thus taxable events
purchaseAddresses = form.getfirst('purchaseAddresses', '')

failure = False
includedChains = 0

if formatType == 'csv':
	print('Content-type: text/csv')
	print('Content-disposition: attachment; filename="dfk-report.csv"\n')
else:
    print('Content-type: text/json\n')

try:
    tmpStart = datetime.strptime(startDate, '%Y-%m-%d').date()
    tmpEnd = datetime.strptime(endDate, '%Y-%m-%d').date()
    # incase a date past today is entered, save the report with end date only up to current day
    # that way if it is run again a later day it will trigger a new report and get additional data
    today = date.today()
    if tmpEnd > today:
        logging.debug('Adjusted saved end date from {0} to {1}'.format(endDate, today.strftime('%Y-%m-%d')))
        endDate = today.strftime('%Y-%m-%d')
except ValueError:
    response = '{ "response" : "Error: You must provide dates in the format YYYY-MM-DD" }'
    failure = True

if not Web3.isAddress(wallet):
    response = '{ "response" : "Error: That is not a valid address.  Make sure you enter the version that starts with 0x" }'
    failure = True
else:
    # Ensure consistent checksum version of address incase they enter lower case
    wallet = Web3.toChecksumAddress(wallet)
    if wallet in contracts.address_map:
        response = '{ "response" : "Error: That is not a valid address.  Make sure you enter the version that starts with 0x" }'
        failure = True

if costBasis not in ['fifo', 'lifo', 'hifo', 'acb']:
    response = '{ "response" : "Error: Invalid option specified for cost basis." }'
    failure = True

# Build up the bitwise integer of chains to be included
if includeHarmony == 'on':
    includedChains += 1
if includeAvalanche == 'on':
    includedChains += 2
if includeDFKChain == 'on':
    includedChains += 4
if includedChains < 1:
    response = '{ "response" : "Error: You have to select at least 1 blockchain to include." }'
    failure = True

addressList = []
otherOptions = db.ReportOptions()
if purchaseAddresses != '':
    purchaseAddresses = urllib.parse.unquote(purchaseAddresses)
    if ',' in purchaseAddresses:
        input = purchaseAddresses.split(',')
    else:
        input = purchaseAddresses.split()
    for address in input:
        address = address.strip()
        if Web3.isAddress(address):
            addressList.append(Web3.toChecksumAddress(address))
        elif len(address) == 0:
            continue
        else:
            response = ''.join(('{ "response" : "Error: You have an invalid address in the purchase address list ', address, '." }'))
            failure = True
    otherOptions['purchaseAddresses'] = addressList


if not failure:
    try:
        status = getReportStatus(wallet, startDate, endDate, costBasis, includedChains, otherOptions)
    except pymysql.err.OperationalError:
        logging.error('Responding DB unavailable report error.')
        status = "Site backend has become unavailable, but report should still be generating.  Click generate again in a minute to pick up where you left off."
    except Exception as err:
        # Failure can happen here if harmony api is completely down
        logging.error('responding report start failure for {0}'.format(str(err)))
        status = "Generation failed!  Harmony API could not be contacted!."
    if len(status) == 14:
        if status[5] == 2:
            # report is ready
            if contentType == '':
                response = '{ "response" : {\n  "status" : "complete",\n  "message" : "Report ready send contentType parameter as tax or transaction to get results."\n  }\n}'
            else:
                with open('../reports/{0}'.format(status[9]), 'rb') as file:
                    results = pickle.load(file)
                if formatType == 'csv':
                    response = getResponseCSV(results, contentType, csvFormat)
                else:
                    response = getResponseJSON(results, contentType, eventGroup)
        elif status[5] == 7:
            # too busy right now
            logging.warning('responding report too busy for {0}'.format(str(status)))
            db.deleteReport(status[0], status[1], status[2], status[8], status[9])
            response = ''.join(('{ \n', '  "response" : "Unfortunately too many people are generating reports right now.  Please try again later!"\n', '}'))
            logging.warning(response)
            failure = True
        elif status[5] == 8:
            # report has encountered some rpc failure
            logging.warning('responding report failure for {0}'.format(str(status)))
            db.deleteReport(status[0], status[1], status[2], status[8], status[9])
            response = ''.join(('{ \n', '  "response" : "Unfortunately report generation failed due to Blockchain API or RPC network congestion.  Please try again later and the report will continue where it left off in generation.  {0}"\n'.format(str(status[3])), '}'))
            logging.warning(response)
            failure = True
        elif status[5] == 9:
            # report has encountered some other failure
            logging.warning('responding report failure for {0}'.format(str(status)))
            db.deleteReport(status[0], status[1], status[2], status[8], status[9])
            response = ''.join(('{ \n', '  "response" : "Unfortunately report generation failed.  Please report this message to the site admin.  {0}"\n'.format(str(status[3])), '}'))
            logging.warning(response)
            failure = True
        elif startDate != status[1] or endDate != status[2]:
            # same account has different report running
            response = '{ \n  "response" : '
            response += '"There is already a report being generated for your account, change the date range to {0} - {1} and generate again to check the progress.  You can only generate one report at a time."'.format(status[1], status[2])
            response += '\n}'
            logging.warning(response)
            failure = True
        else:
            # report is not ready
            response = '{ "response" : {\n'
            if status[5] == 0:
                response += '  "status" : "fetchingtx",\n '
            elif status[5] == None:
                response += '  "status" : "initiated",\n '
            else:
                response += '  "status" : "generating",\n '
            response += '  "transactionsFetched" : {0},\n '.format(status[6])
            response += '  "transactionsComplete" : {0},\n '.format(status[7])
            response += '  "transactionsTotal" : {0},\n '.format(status[4])
            response += '  "startedOn" : {0}\n   '.format(status[3])
            response += '  }\n}'
    elif len(status) == 5:
        response = '{ "response" : {\n'
        response += '  "status" : "initiated",\n '
        response += '  "transactionsTotal" : {0}\n '.format(status[4])
        response += '  }\n}'
    else:
        response = ''.join(('{ \n', '  "response" : "{0}"\n'.format(status), '}'))
        failure = True

print(response)

if failure:
    sys.exit(500)
else:
    sys.exit(200)
