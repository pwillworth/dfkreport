#!/usr/bin/env python3
"""

 Copyright 2021 Paul Willworth <ioscode@gmail.com>

"""

import sys
import cgi
import datetime
import json
from web3 import Web3
sys.path.append("../")
import transactions
import contracts
import db
import pickle
import jsonpickle
import logging


def getResponseCSV(records, contentType):
    taxRecords = records['taxes']
    eventRecords = records['events']

    if contentType == 'transaction':
        # using 9 kind of genericized column headings and fit each records fields in where it makes most sense
        response = 'category,block date,event,type 1,type 1 amount,type 2,type 2 amount,type 1 fiat value,type 2 fiat value\n'
        for record in eventRecords['tavern']:
            blockDateStr = datetime.datetime.fromtimestamp(record.timestamp).strftime("%Y-%m-%d %H:%m:%S %Z")
            response += ','.join(('tavern', blockDateStr, record.event, record.itemType, str(record.itemID), contracts.getAddressName(record.coinType), str(record.coinCost), '', str(record.fiatAmount),'\n'))
        for record in eventRecords['swaps']:
            blockDateStr = datetime.datetime.fromtimestamp(record.timestamp).strftime("%Y-%m-%d %H:%m:%S %Z")
            response += ','.join(('trader', blockDateStr, 'swap', contracts.getAddressName(record.swapType), str(record.swapAmount), contracts.getAddressName(record.receiveType), str(record.receiveAmount), str(record.fiatSwapValue), str(record.fiatReceiveValue),'\n'))
        for record in eventRecords['liquidity']:
            blockDateStr = datetime.datetime.fromtimestamp(record.timestamp).strftime("%Y-%m-%d %H:%m:%S %Z")
            response += ','.join(('liquidity', blockDateStr, '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getAddressName(record.poolAddress)), contracts.getAddressName(record.coin1Type), str(record.coin1Amount), contracts.getAddressName(record.coin2Type), str(record.coin2Amount), str(record.coin1FiatValue), str(record.coin2FiatValue),'\n'))
        for record in eventRecords['gardens']:
            blockDateStr = datetime.datetime.fromtimestamp(record.timestamp).strftime("%Y-%m-%d %H:%m:%S %Z")
            response += ','.join(('gardens', blockDateStr, record.event, contracts.getAddressName(record.coinType), str(record.coinAmount), '', '', str(record.fiatValue), '','\n'))
        for record in eventRecords['bank']:
            blockDateStr = datetime.datetime.fromtimestamp(record.timestamp).strftime("%Y-%m-%d %H:%m:%S %Z")
            response += ','.join(('bank', blockDateStr, record.action, 'xRate', str(record.xRate), contracts.getAddressName(record.coinType), str(record.coinAmount), '', str(record.fiatValue),'\n'))
        for record in eventRecords['alchemist']:
            blockDateStr = datetime.datetime.fromtimestamp(record.timestamp).strftime("%Y-%m-%d %H:%m:%S %Z")
            response += ','.join(('alchemist', blockDateStr, 'crafting', contracts.getAddressName(record.craftingType), str(record.craftingAmount), record.craftingCosts, '', str(record.fiatValue), str(record.costsFiatValue),'\n'))
        for record in eventRecords['airdrops']:
            blockDateStr = datetime.datetime.fromtimestamp(record.timestamp).strftime("%Y-%m-%d %H:%m:%S %Z")
            response += ','.join(('airdrops', blockDateStr, '', contracts.getAddressName(record.tokenReceived), str(record.tokenAmount), '', '', str(record.fiatValue), '','\n'))
        for record in eventRecords['quests']:
            blockDateStr = datetime.datetime.fromtimestamp(record.timestamp).strftime("%Y-%m-%d %H:%m:%S %Z")
            response += ','.join(('quest', blockDateStr, 'rewards', contracts.getAddressName(record.rewardType), str(record.rewardAmount), '', '', str(record.fiatValue), '','\n'))
        for record in eventRecords['wallet']:
            blockDateStr = datetime.datetime.fromtimestamp(record.timestamp).strftime("%Y-%m-%d %H:%m:%S %Z")
            response += ','.join(('wallet', blockDateStr, record.action, contracts.getAddressName(record.coinType), str(record.coinAmount), '', '', str(record.fiatValue), '','\n'))
    else:
        response = 'category,description,acquired date,sold date,proceeds,costs,gains,term,basis amt not accounted\n'

        for record in taxRecords:
            acquiredDateStr = ''
            soldDateStr = ''
            if record.acquiredDate != None:
                acquiredDateStr = record.acquiredDate.strftime('%Y-%m-%d')
            if record.soldDate != None:
                soldDateStr = record.soldDate.strftime('%Y-%m-%d')
            response += ','.join((record.category,record.description,acquiredDateStr,soldDateStr,str(record.proceeds),str(record.costs),str(record.get_gains()),record.term,str(record.amountNotAccounted), '\n'))

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
            response += '  "amountNotAccounted"  : "{0}"\n'.format(record.amountNotAccounted)
            response += '  }, \n'

        # trim off extra comma
        response = response[:-3]
        response += '  ]\n'
    response += '  }\n}'

    if (contentType == 'tax' and len(taxRecords) == 0) or (contentType != 'tax' and len(eventRecords) == 0):
        response = '{ "response" : "Error: No events found for that wallet and date range." }'

    return response

# Get an existing report record or create a new one and return it
def getReportStatus(wallet, startDate, endDate, costBasis):
    reportRow = db.findReport(wallet, startDate, endDate)
    if reportRow != None:
        if reportRow[11] == costBasis or reportRow[10] == 1:
            # if cost basis same or its different but report still running, just return existing
            return reportRow
        else:
            # wipe the old report and re-map for new options or transactions
            logging.debug('updating existing report row to regenerate')
            result = transactions.getTransactionCount(wallet)
            if type(result) is int:
                generateTime = datetime.datetime.now()
                db.resetReport(wallet, startDate, endDate, int(datetime.datetime.timestamp(generateTime)), result, costBasis, reportRow[8], reportRow[9])
                return [reportRow[0], reportRow[1], reportRow[2], int(datetime.datetime.timestamp(generateTime)), result]
            else:
                return 'Error: No Transactions for that wallet found'
    else:
        logging.debug('start new report row')
        result = transactions.getTransactionCount(wallet)
        if type(result) is int:
            generateTime = datetime.datetime.now()
            db.createReport(wallet, startDate, endDate, int(datetime.datetime.timestamp(generateTime)), result, costBasis)
            report = db.findReport(wallet, startDate, endDate)
            logging.debug(str([report[0], report[1], report[2], report[3], report[4]]))
            return [report[0], report[1], report[2], report[3], report[4]]
        else:
            return 'Error: No Transactions for that wallet found'

logging.basicConfig(filename='../generate.log', level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
# Extract query parameters
form = cgi.FieldStorage()

wallet = form.getfirst('walletAddress', '')
startDate = form.getfirst('startDate', '')
endDate = form.getfirst('endDate', '')
costBasis = form.getfirst('costBasis', 'fifo')
# can be set to csv, otherwise json response is returned
formatType = form.getfirst('formatType', '')
# can be tax or transaction, only used for CSV
contentType = form.getfirst('contentType', '')
# can be any event group to return only that group of events instead of all
eventGroup = form.getfirst('eventGroup', 'all')
failure = False

if formatType == 'csv':
	print('Content-type: text/csv')
	print('Content-disposition: attachment; filename="dfk-report.csv"\n')
else:
    print('Content-type: text/json\n')

try:
    tmpStart = datetime.datetime.strptime(startDate, '%Y-%m-%d').date()
    tmpEnd = datetime.datetime.strptime(endDate, '%Y-%m-%d').date()
    # incase a date past today is entered, save the report with end date only up to current day
    # that way if it is run again a later day it will trigger a new report and get additional data
    today = datetime.date.today()
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

if costBasis not in ['fifo', 'lifo', 'hifo']:
    response = '{ "response" : "Error: Invalid option specified for cost basis." }'
    failure = True

if not failure:
    try:
        status = getReportStatus(wallet, startDate, endDate, costBasis)
    except Exception as err:
        # Failure can happen here if harmony api is completely down
        logging.error('responding report failure for {0}'.format(str(err)))
        status = "Generation failed!  Harmony API could not be contacted!."
    if len(status) == 12:
        if status[5] == 2:
            # report is ready
            if contentType == '':
                response = '{ "response" : {\n  "status" : "complete",\n  "message" : "Report ready send contentType parameter as tax or transaction to get results."\n  }\n}'
            else:
                with open('../reports/{0}'.format(status[9]), 'rb') as file:
                    results = pickle.load(file)
                if formatType == 'csv':
                    response = getResponseCSV(results, contentType)
                else:
                    response = getResponseJSON(results, contentType, eventGroup)
        elif status[5] == 8:
            # report has encountered some rpc failure
            logging.warning('responding report failure for {0}'.format(str(status)))
            db.deleteReport(status[0], status[1], status[2], status[8], status[9])
            response = ''.join(('{ \n', '  "response" : "Unfortunately report generation failed due to Harmony RPC network congestion.  Please try again later and the report will continue where it left off in generation.  {0}"\n'.format(str(status[3])), '}'))
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
            if status[10] == None:
                # too busy right now
                logging.warning('responding report too busy for {0}'.format(str(status)))
                db.deleteReport(status[0], status[1], status[2], status[8], status[9])
                response = ''.join(('{ \n', '  "response" : "Unfortunately too many people are generating reports right now.  Please try again later!"\n', '}'))
                logging.warning(response)
                failure = True
            else:
                response = '{ "response" : {\n'
                if status[5] == 0:
                    response += '  "status" : "fetchingtx",\n '
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
