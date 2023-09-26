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
            response += '  "amountNotAccounted"  : "{0}",\n'.format(record.amountNotAccounted)
            response += '  "costBasisItems"  : {0}\n'.format(jsonpickle.encode(record.costBasisItems, make_refs=False))
            response += '  }, \n'

        # trim off extra comma
        response = response[:-3]
        response += '  ],\n'
        response += '  "gasValue" : "{0}"\n'.format(results['events']['gas'])
    response += '  }\n}'

    if len(eventRecords) == 0:
        response = '{ "response" : "Error: No events found for that wallet and date range." }'

    return response

def getReportData(formatType, contentType, csvFormat, eventGroup, wallets, startDate, endDate, costBasis, includedChains, moreOptions):
    failure = False

    if costBasis not in ['fifo', 'lifo', 'hifo', 'acb']:
        response = { "response" : "Error: Invalid option specified for cost basis." }
        failure = True


    if not failure:
        # report is ready
        if contentType == '':
            response = '{ "response" : {\n  "status" : "complete",\n  "message" : "Report ready send contentType parameter as tax or transaction to get results."\n  }\n}'
        else:
            results = {}
            results = taxmap.buildTaxMap(wallets, startDate, endDate, costBasis, includedChains, moreOptions, contentType, eventGroup, formatType)

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

def getTokensReport(wallets, startDate, endDate, includedChains):
    swapData = []
    tradeData = []
    networks = taxmap.getNetworkList(includedChains)
    for wallet in wallets:
        swapData += db.getEventData(wallet, 'swaps', networks)
        tradeData += db.getEventData(wallet, 'trades', networks)
    tokensRecords = taxmap.buildSwapRecords(swapData+tradeData, startDate, endDate, [], [], [], [], [], [], 'fifo', [])
    response = getResponseJSON({'taxes': tokensRecords, 'events': taxmap.EventsMap() }, 'tax')
    return response

def getCraftingReport(wallets, startDate, endDate, includedChains):
    swapData = []
    tradeData = []
    craftData = []
    airdropData = []
    networks = taxmap.getNetworkList(includedChains)
    for wallet in wallets:
        swapData += db.getEventData(wallet, 'swaps', networks)
        tradeData += db.getEventData(wallet, 'trades', networks)
        craftData += db.getEventData(wallet, 'alchemist', networks)
        airdropData += db.getEventData(wallet, 'airdrops', networks)
    craftingRecords = taxmap.buildCraftingRecords(swapData+tradeData, startDate, endDate, craftData, airdropData)
    response = getResponseJSON({'taxes': craftingRecords, 'events': taxmap.EventsMap() }, 'tax')
    return response

def getDuelsReport(wallets, startDate, endDate, includedChains):
    tavernData = []
    airdropData = []
    networks = taxmap.getNetworkList(includedChains)
    for wallet in wallets:
        tavernData += db.getEventData(wallet, 'tavern', networks)
        airdropData += db.getEventData(wallet, 'airdrops', networks)
    logging.info('taver {0} airdrop {1}'.format(len(tavernData), len(airdropData)))

    duelsRecords = taxmap.EventsMap()
    logging.info(str(airdropData[10].__dict__))
    logging.info(str(tavernData[2345].__dict__))
    airdropData = [x for x in airdropData if (taxmap.inReportRange(x, startDate, endDate))]
    tavernData = [x for x in tavernData if (taxmap.inReportRange(x, startDate, endDate))]
    logging.info('t {0} airdrop {1}'.format(len(duelsRecords['tavern']), len(duelsRecords['airdrops'])))
    duelsRecords['airdrops'] = [x for x in airdropData if (x.address in ['0x0000000000000000000000000000000000000000','0x89789a580fdE00319493BdCdB6C65959DAB1e517','0xb0f423BCB1F4396781e21ad9E0BC151d29Ac020C'])]
    duelsRecords['tavern'] = [x for x in tavernData if (x.event in ['pvpfee','pvpreward'])]
    response = getResponseJSON({'taxes': [], 'events': duelsRecords }, 'transaction')
    logging.info('taverevm {0} airdrop {1}'.format(len(duelsRecords['tavern']), len(duelsRecords['airdrops'])))
    return response

def getNFTReport(wallets, startDate, endDate, includedChains):
    tavernData = []
    networks = taxmap.getNetworkList(includedChains)
    for wallet in wallets:
        tavernData += db.getEventData(wallet, 'tavern', networks)
    tavernRecords = taxmap.buildTavernRecords(tavernData, startDate, endDate)
    response = getResponseJSON({'taxes': tavernRecords, 'events': taxmap.EventsMap() }, 'tax')
    return response

def getPetsReport(wallets, startDate, endDate, includedChains):
    failure = False
