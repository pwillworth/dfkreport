#!/usr/bin/env python3
"""

 Copyright 2022 Paul Willworth <ioscode@gmail.com>

"""

import urllib.parse
from datetime import timezone, datetime, date
from web3 import Web3
import jsonpickle
import logging
import transactions
import db


# Get an existing report record or create a new one and return it
def getReportStatus(account, startDate, endDate, costBasis, includedChains, otherOptions, wallets, group):
    log = logging.getLogger('dfkreport.generate')
    walletHash = db.getWalletHash(wallets)
    reportRow = db.findReport(account, startDate, endDate, walletHash)
    if reportRow != None:
        if reportRow[10] == None:
            # If watcher has not picked up report yet return partial for correct status
            return [reportRow[0], reportRow[1], reportRow[2], reportRow[3], reportRow[4]]
        elif (reportRow[11] == costBasis and reportRow[12] == includedChains) or reportRow[10] == 1:
            # if cost basis same or its different but report still running, just return existing
            return reportRow
        else:
            # wipe the old report and re-map for new options or transactions
            log.debug('updating existing report row to regenerate')
            result = transactions.getTransactionCount(wallets, includedChains)
            if type(result) is dict:
                generateTime = datetime.now(timezone.utc)
                totalTx = transactions.getTotalCount(result)
                db.resetReport(account, startDate, endDate, int(datetime.timestamp(generateTime)), totalTx, costBasis, includedChains, reportRow[8], reportRow[9], walletHash, jsonpickle.dumps(otherOptions), jsonpickle.dumps(result))
                return [reportRow[0], reportRow[1], reportRow[2], int(datetime.timestamp(generateTime)), totalTx]
            else:
                return result
    else:
        log.debug('start new report row')
        result = transactions.getTransactionCount(wallets, includedChains)
        if type(result) is dict:
            generateTime = datetime.now(timezone.utc)
            totalTx = transactions.getTotalCount(result)
            db.createReport(account, startDate, endDate, int(datetime.timestamp(generateTime)), totalTx, costBasis, includedChains, wallets, group, walletHash, None, jsonpickle.dumps(otherOptions), jsonpickle.dumps(result))
            report = db.findReport(account, startDate, endDate, walletHash)
            log.debug(str([report[0], report[1], report[2], report[3], report[4]]))
            return [report[0], report[1], report[2], report[3], report[4]]
        else:
            return result

def generation(account, loginState, wallet, startDate, endDate, includeHarmony, includeDFKChain, includeAvalanche, includeKlaytn, costBasis, eventGroup, purchaseAddresses):
    failure = False
    includedChains = 0
    walletGroup = ''
    wallets = []
    log = logging.getLogger('dfkreport.generate')

    try:
        tmpStart = datetime.strptime(startDate, '%Y-%m-%d').date()
        tmpEnd = datetime.strptime(endDate, '%Y-%m-%d').date()
        # incase a date past today is entered, save the report with end date only up to current day
        # that way if it is run again a later day it will trigger a new report and get additional data
        today = date.today()
        if tmpEnd > today:
            log.debug('Adjusted saved end date from {0} to {1}'.format(endDate, today.strftime('%Y-%m-%d')))
            endDate = today.strftime('%Y-%m-%d')
    except ValueError:
        response = '{ "response" : "Error: You must provide dates in the format YYYY-MM-DD" }'
        failure = True

    if not Web3.is_address(wallet):
        # If address not passed, check if it is one of users multi wallet groups
        if loginState > 0:
            wallets = db.getWalletGroup(account, wallet)
        if type(wallets) is list and len(wallets) > 0:
            walletGroup = wallet
        else:
            response = { "response" : "Error: {0} is not a valid address.  Make sure you enter the version that starts with 0x".format(wallet) }
            failure = True
    else:
        # Ensure consistent checksum version of address incase they enter lower case
        wallet = Web3.to_checksum_address(wallet)
        wallets = [wallet]

    if costBasis not in ['fifo', 'lifo', 'hifo', 'acb']:
        response = { "response" : "Error: Invalid option specified for cost basis." }
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
        response = { "response" : "Error: You have to select at least 1 blockchain to include." }
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
            if Web3.is_address(address):
                addressList.append(Web3.to_checksum_address(address))
            elif len(address) == 0:
                continue
            else:
                response = ''.join(('{ "response" : "Error: You have an invalid address in the purchase address list ', address, '." }'))
                failure = True
        otherOptions['purchaseAddresses'] = addressList


    if not failure:
        # allow non-connected users to run on wallet address entry
        if account == '':
            account = wallet
        try:
            status = getReportStatus(account, startDate, endDate, costBasis, includedChains, otherOptions, wallets, walletGroup)
        except Exception as err:
            # Failure can happen here if api is completely down
            log.error('responding report start failure for {0}'.format(str(err)))
            status = "Generation failed!  System error starting report, please report issue on github site issue tracker or contact admin!."

        if len(status) == 18:
            if status[5] == 2:
                # report is ready
                response = ''.join(('{ "response" : {\n  "contentFile" : "', status[9], '",\n  "status" : "complete",\n  "message" : "Report ready post to view.py with contentFile and send contentType parameter as tax or transaction to get results."\n  }\n}'))
            elif status[5] == 7:
                # too busy right now
                log.warning('responding report too busy for {0}'.format(str(status)))
                db.deleteReport(status[0], status[1], status[2], status[17], status[8], status[9])
                response = ''.join(('{ \n', '  "response" : "Unfortunately too many people are generating reports right now.  Please try again later!"\n', '}'))
                log.warning(response)
                failure = True
            elif status[5] == 8:
                # report has encountered some rpc failure
                log.warning('responding report failure for {0}'.format(str(status)))
                db.deleteReport(status[0], status[1], status[2], status[17], status[8], status[9])
                response = ''.join(('{ \n', '  "response" : "Unfortunately report generation failed due to Blockchain API or RPC network congestion.  Please try again later and the report will continue where it left off in generation.  {0}"\n'.format(str(status[3])), '}'))
                log.warning(response)
                failure = True
            elif status[5] == 9:
                # report has encountered some other failure
                log.warning('responding report failure for {0}'.format(str(status)))
                db.deleteReport(status[0], status[1], status[2], status[17], status[8], status[9])
                response = ''.join(('{ \n', '  "response" : "Unfortunately report generation failed.  Please report this message to the site admin.  {0}"\n'.format(str(status[3])), '}'))
                log.warning(response)
                failure = True
            elif startDate != status[1] or endDate != status[2]:
                # same account has different report running
                response = '{ \n  "response" : '
                response += '"There is already a report being generated for your account, change the date range to {0} - {1} and generate again to check the progress.  You can only generate one report at a time."'.format(status[1], status[2])
                response += '\n}'
                log.warning(response)
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
                log.info(str(status))
        elif len(status) == 5:
            log.info('Waiting for initiated report to be picked up by main.')
            response = '{ "response" : {\n'
            response += '  "status" : "initiated",\n '
            response += '  "transactionsTotal" : {0}\n '.format(status[4])
            response += '  }\n}'
        else:
            response = ''.join(('{ \n', '  "response" : "{0}"\n'.format(status), '}'))
            failure = True

    return response
