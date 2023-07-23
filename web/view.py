#!/usr/bin/env python3
"""

 Copyright 2023 Paul Willworth <ioscode@gmail.com>

"""
from datetime import datetime
import jsonpickle
import logging
import db
import taxmap
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

def getReportData(contentFile, formatType, contentType, csvFormat, eventGroup):
    failure = False

    if contentFile == '':
        response = '{ "response" : "Error: content file id in contentFile parameter is required to view a report" }'
        failure = True

    if not failure:
        # report is ready
        if contentType == '':
            response = '{ "response" : {\n  "status" : "complete",\n  "message" : "Report ready send contentType parameter as tax or transaction to get results."\n  }\n}'
        else:
            results = {}
            con = db.aConn()
            with con.cursor() as cur:
                cur.execute('SELECT wallets, startDate, endDate, costBasis, moreOptions FROM reports WHERE reportContent=%s', (contentFile,))
                row = cur.fetchone()
            con.close()
            if row != None:
                results = taxmap.buildTaxMap(jsonpickle.loads(row[0]), datetime.strptime(row[1], '%Y-%m-%d').date(), datetime.strptime(row[2], '%Y-%m-%d').date(), row[3], jsonpickle.loads(row[4]), contentType, eventGroup)
            else:
                response = '{ "response" : "Error: failed to find completed report with that content id" }'

            if 'taxes' in results:
                if formatType == 'csv':
                    logging.info('Getting response CSV')
                    response = csvFormats.getResponseCSV(results, contentType, csvFormat)
                else:
                    response = getResponseJSON(results, contentType, eventGroup)
            else:
                response = '{ "response" : "Error: content file corrupted or empty.  You may need to regenerate the report" }'
                failure = True

    return response

