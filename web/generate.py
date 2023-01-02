#!/usr/bin/env python3
"""

 Copyright 2022 Paul Willworth <ioscode@gmail.com>

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
            if len(result) == 4:
                generateTime = datetime.now(timezone.utc)
                totalTx = result[0] + result[1] + result[2] + result[3]
                db.resetReport(wallet, startDate, endDate, int(datetime.timestamp(generateTime)), totalTx, costBasis, includedChains, reportRow[8], reportRow[9])
                return [reportRow[0], reportRow[1], reportRow[2], int(datetime.timestamp(generateTime)), totalTx]
            else:
                return 'Error: No Transactions for that wallet found'
    else:
        logging.debug('start new report row')
        result = transactions.getTransactionCount(wallet, includedChains)
        if len(result) == 4:
            generateTime = datetime.now(timezone.utc)
            totalTx = result[0] + result[1] + result[2] + result[3]
            db.createReport(wallet, startDate, endDate, int(datetime.timestamp(generateTime)), totalTx, costBasis, includedChains, None, jsonpickle.dumps(otherOptions))
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
includeHarmony = form.getfirst('includeHarmony', 'on')
includeDFKChain = form.getfirst('includeDFKChain', 'on')
includeAvalanche = form.getfirst('includeAvalanche', 'false')
includeKlaytn = form.getfirst('includeKlaytn', 'on')
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
if includeKlaytn == 'on':
    includedChains += 8
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
        # Failure can happen here if api is completely down
        logging.error('responding report start failure for {0}'.format(str(err)))
        status = "Generation failed!  Blockchain API could not be contacted!."
    if len(status) == 14:
        if status[5] == 2:
            # report is ready
            if contentType == '':
                response = '{ "response" : {\n  "status" : "complete",\n  "message" : "Report ready send contentType parameter as tax or transaction to get results."\n  }\n}'
            else:
                with open('../reports/{0}'.format(status[9]), 'rb') as file:
                    results = pickle.load(file)
                if formatType == 'csv':
                    logging.info('Getting response CSV')
                    response = csvFormats.getResponseCSV(results, contentType, csvFormat)
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
            # prevent status from showing a little over 100% when more tx than count which
            # is often the case with additional tx coming in not counted by total count method
            txComplete = status[7]
            if txComplete > status[4]:
                txComplete = status[4]
            response = '{ "response" : {\n'
            if status[5] == 0:
                response += '  "status" : "fetchingtx",\n '
            elif status[5] == None:
                response += '  "status" : "initiated",\n '
            else:
                response += '  "status" : "generating",\n '
            response += '  "transactionsFetched" : {0},\n '.format(status[6])
            response += '  "transactionsComplete" : {0},\n '.format(txComplete)
            response += '  "transactionsTotal" : {0},\n '.format(status[4])
            response += '  "startedOn" : {0}\n   '.format(status[3])
            response += '  }\n}'
    elif len(status) == 5:
        logging.info('Waiting for initiated report to be picked up by main.')
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
