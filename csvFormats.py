#!/usr/bin/env python3
"""

 Copyright 2022 Paul Willworth <ioscode@gmail.com>

"""

COINLEDGER_ROW_HEADER='Date (UTC),Platform (Optional),Asset Sent,Amount Sent,Asset Received,Amount Received,Fee Currency (Optional),Fee Amount (Optional),Type,Description (Optional),TxHash (Optional)\n'
KOINLY_ROW_HEADER='Date,Sent Amount,Sent Currency,Received Amount,Received Currency,Fee Amount,Fee Currency,Net Worth Amount,Net Worth Currency,Label,Description,TxHash\n'
DEFAULT_ROW_HEADER='category,block date,event,type 1,type 1 amount,type 2,type 2 amount,type 1 fiat value,type 2 fiat value,txHash,tx fee fiat value\n'

COINLEDGER_DATE_FORMAT='%m/%d/%Y %H:%M:%S'
KOINLY_DATE_FORMAT='%Y-%m-%d %H:%M:%S %Z'
DEFAULT_DATE_FORMAT='%Y-%m-%d %H:%M:%S %Z'

def coinledgerRecordLabel(type, event):
    if type == 'tavern':
        if event == 'sale' or event == 'hire':
            if event == 'sale':
                return 'gain on NFT sale'
            else:
                return 'Income'
        else:
            return 'expense of NFT investment'
    elif type == 'gardens':
        if event == 'staking-reward':
            return 'Staking'
        else:
            return 'Deposit'

def koinlyRecordLabel(type, event):
    if type == 'tavern':
        if event == 'sale' or event == 'hire':
            if event == 'sale':
                return 'realized gain'
            else:
                return 'income'
        else:
            return 'cost'
    elif type == 'gardens':
        if event == 'staking-reward':
            return 'reward'
        else:
            return 'ignored'

# not used yet
def defaultRecordLabel(type, event):
    return '{0} {1}'.format(type, event)

def getHeaderRow(format):
    if format == 'koinlyuniversal':
        return KOINLY_ROW_HEADER
    elif format == 'coinledgeruniversal':
        return COINLEDGER_ROW_HEADER
    else:
        return DEFAULT_ROW_HEADER

def getDateFormat(format):
    if format == 'koinlyuniversal':
        return KOINLY_DATE_FORMAT
    elif format == 'coinledgeruniversal':
        return COINLEDGER_DATE_FORMAT
    else:
        return DEFAULT_DATE_FORMAT

def getRecordLabel(format, type, event):
    if format == 'koinlyuniversal':
        return koinlyRecordLabel(type, event)
    elif format == 'coinledgeruniversal':
        return coinledgerRecordLabel(type, event)
    else:
        return defaultRecordLabel(type, event)
