#!/usr/bin/env python3
"""

 Copyright 2023 Paul Willworth <ioscode@gmail.com>

"""

from datetime import timezone, datetime, date
from web3 import Web3
import jsonpickle
import logging
import db
import nets


# Get existing wallet group records or create a new one and return rows
def getWalletStatus(account, includedChains, wallets, triggerUpdate='false'):
    walletRows = []
    lastUpdateValue = 0
    for wallet in wallets:
        for network in nets.getNetworkList(includedChains):
            if triggerUpdate == 'true':
                db.forceWalletUpdate(wallet, network)
                lastUpdateValue = None
            reportRow = db.findWalletStatus(wallet, network)
            if reportRow != None:
                walletRows.append(reportRow)
            else:
                logging.debug('start new wallet row')
                db.createWalletStatus(wallet, network, account)
                walletRows.append([wallet, network, None, 0, None, 0, lastUpdateValue, None, None, None, account])
    return walletRows

def generation(account, loginState, wallet, startDate, endDate, includeHarmony, includeDFKChain, includeAvalanche, includeKlaytn, triggerUpdate='false'):
    failure = False
    includedChains = 0
    walletGroup = ''
    wallets = []

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

    if not failure:
        # allow non-connected users to run on wallet address entry
        if account == '':
            account = wallet
        else:
            account = Web3.to_checksum_address(account)

        generateTime = datetime.now(timezone.utc)
        minDate = int(datetime.timestamp(generateTime))

        status = getWalletStatus(account, includedChains, wallets, triggerUpdate)
        for item in status:
            if item[5] != None and item[6] != None:
                minDate = min(minDate, max(item[5], item[6]))
            else:
                minDate = 0

        if datetime.fromtimestamp(minDate) <= datetime(tmpEnd.year, tmpEnd.month, tmpEnd.day):
            response = '{ "response" : {\n'
            response += '  "status" : "generating",\n   '
            response += '  "wallet_records" : \n   '
            response += jsonpickle.encode(status, make_refs=False)
            response += '  }\n}'
        else:
            # report is ready
            response = ''.join(('{ "response" : {\n  "status" : "complete",\n  "message" : "Report data satisfies critieria, post to view with contentType parameter as tax or transaction to get results."\n  }\n}'))

    return response
