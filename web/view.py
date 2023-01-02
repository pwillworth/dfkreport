#!/usr/bin/env python3
"""

 Copyright 2023 Paul Willworth <ioscode@gmail.com>

"""

import sys
import cgi
from web3 import Web3
import pickle
import jsonpickle
import logging
sys.path.append("../")
import contracts
import db
import csvFormats


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


logging.basicConfig(filename='../view.log', level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
# Extract query parameters
form = cgi.FieldStorage()

account = form.getfirst('account', '')
contentFile = form.getfirst('contentFile', '')
# can be set to csv, otherwise json response is returned
formatType = form.getfirst('formatType', '')
# can be tax or transaction, only used for CSV
contentType = form.getfirst('contentType', '')
# can by koinlyuniversal or anything else for default
csvFormat = form.getfirst('csvFormat', 'manual')
# can be any event group to return only that group of events instead of all
eventGroup = form.getfirst('eventGroup', 'all')

contentFile = db.dbInsertSafe(contentFile)

failure = False

if formatType == 'csv':
	print('Content-type: text/csv')
	print('Content-disposition: attachment; filename="dfk-report.csv"\n')
else:
    print('Content-type: text/json\n')

if not Web3.isAddress(account):
    response = '{ "response" : "Error: That is not a valid address.  Make sure you enter the version that starts with 0x" }'
    failure = True
else:
    # Ensure consistent checksum version of address incase they enter lower case
    wallet = Web3.toChecksumAddress(account)
    if wallet in contracts.address_map:
        response = '{ "response" : "Error: That is not a valid address.  Make sure you enter the version that starts with 0x" }'
        failure = True
if contentFile == '':
    response = '{ "response" : "Error: content file id in contentFile parameter is required to view a report" }'
    failure = True

if not failure:
    # report is ready
    if contentType == '':
        response = '{ "response" : {\n  "status" : "complete",\n  "message" : "Report ready send contentType parameter as tax or transaction to get results."\n  }\n}'
    else:
        results = None
        try:
            with open('../reports/{0}'.format(contentFile), 'rb') as file:
                results = pickle.load(file)
        except FileNotFoundError as err:
            response = '{ "response" : "Error: content file is invalid or no longer available.  You may need to regenerate the report" }'
            failure = True

        if 'taxes' in results:
            if formatType == 'csv':
                logging.info('Getting response CSV')
                response = csvFormats.getResponseCSV(results, contentType, csvFormat)
            else:
                response = getResponseJSON(results, contentType, eventGroup)
        else:
            response = '{ "response" : "Error: content file corrupted or empty.  You may need to regenerate the report" }'
            failure = True

print(response)

