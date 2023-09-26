#!/usr/bin/env python3
"""

 Copyright 2022 Paul Willworth <ioscode@gmail.com>

"""

import contracts
from datetime import timezone, datetime
import logging

COINLEDGER_ROW_HEADER=['Date (UTC)','Platform (Optional)','Asset Sent','Amount Sent','Asset Received','Amount Received','Fee Currency (Optional)','Fee Amount (Optional)','Type,Description (Optional)','TxHash (Optional)']
KOINLY_ROW_HEADER=['Date','Sent Amount','Sent Currency','Received Amount','Received Currency','Fee Amount','Fee Currency','Net Worth Amount','Net Worth Currency','Label,Description','TxHash']
TOKENTAX_ROW_HEADER=['Type','BuyAmount','BuyCurrency','SellAmount','SellCurrency','FeeAmount','FeeCurrency','Exchange','Group','Comment','Date']
TURBOTAX_ROW_HEADER=['Date','Type','Sent Asset','Sent Amount','Received Asset','Received Amount','Fee Asset','Fee Amount','Market Value Currency','Market Value','Description','Transaction Hash','Transaction ID']
DEFAULT_ROW_HEADER=['category','block date','event','type 1','type 1 amount','type 2','type 2 amount','type 1 fiat value','type 2 fiat value','txHash','tx fee fiat value']

COINLEDGER_DATE_FORMAT='%m/%d/%Y %H:%M:%S'
KOINLY_DATE_FORMAT='%Y-%m-%d %H:%M:%S %Z'
TOKENTAX_DATE_FORMAT='%m/%d/%Y %H:%M'
TURBOTAX_DATE_FORMAT='%Y-%m-%d %H:%M:%S'
DEFAULT_DATE_FORMAT='%Y-%m-%d %H:%M:%S %Z'

def coinledgerRecordLabel(type, event):
    if type == 'tavern':
        if event == 'sale' or event == 'hire':
            if event == 'sale':
                return 'gain on NFT sale'
            else:
                return 'Income'
        else:
            return 'Sale'
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

def tokentaxRecordLabel(type, event):
    if type == 'tavern':
        if event == 'sale' or event == 'hire':
            if event == 'sale':
                return 'Trade'
            else:
                return 'Income'
        else:
            return 'Spend'
    elif type == 'gardens':
        if event == 'staking-reward':
            return 'Income'
        else:
            return 'Deposit'

def turbotaxRecordLabel(type, event):
    if type == 'tavern':
        if event == 'sale' or event == 'hire':
            if event == 'sale':
                return 'Convert'
            else:
                return 'Income'
        else:
            return 'Sale'
    elif type == 'gardens':
        if event == 'staking-reward':
            return 'Interest'
        else:
            return 'Deposit'

# not used yet
def defaultRecordLabel(type, event):
    return '{0} {1}'.format(type, event)

def getHeaderRow(format):
    if format == 'koinlyuniversal':
        return KOINLY_ROW_HEADER
    elif format == 'coinledgeruniversal':
        return COINLEDGER_ROW_HEADER
    elif format == 'tokentax':
        return TOKENTAX_ROW_HEADER
    elif format == 'turbotax':
        return TURBOTAX_ROW_HEADER
    else:
        return DEFAULT_ROW_HEADER

def getDateFormat(format):
    if format == 'koinlyuniversal':
        return KOINLY_DATE_FORMAT
    elif format == 'coinledgeruniversal':
        return COINLEDGER_DATE_FORMAT
    elif format == 'tokentax':
        return TOKENTAX_DATE_FORMAT
    elif format == 'turbotax':
        return TURBOTAX_DATE_FORMAT
    else:
        return DEFAULT_DATE_FORMAT

def getRecordLabel(format, type, event):
    if format == 'koinlyuniversal':
        return koinlyRecordLabel(type, event)
    elif format == 'coinledgeruniversal':
        return coinledgerRecordLabel(type, event)
    elif format == 'tokentax':
        return tokentaxRecordLabel(type, event)
    elif format == 'turbotax':
        return turbotaxRecordLabel(type, event)
    else:
        return defaultRecordLabel(type, event)

def getResponseCSV(eventRecords, format):
    # translate output based on req format
    response = [getHeaderRow(format)]
    for record in eventRecords['tavern']:
        blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(getDateFormat(format))
        txFee = ''
        txFeeCurrency = ''
        if hasattr(record, 'fiatFeeValue'):
            txFee = record.fiatFeeValue
            txFeeCurrency = 'USD'
        if format in ['koinlyuniversal','coinledgeruniversal','tokentax','turbotax']:
            if record.event == 'sale' or record.event == 'hire':
                sentAmount = ''
                sentType = ''
                rcvdAmount = record.coinCost
                rcvdType = contracts.getTokenName(record.coinType, record.network)
            else:
                sentAmount = record.coinCost
                sentType = contracts.getTokenName(record.coinType, record.network)
                rcvdAmount = ''
                rcvdType = ''

        label = getRecordLabel(format, 'tavern', record.event)
        if format == 'koinlyuniversal':
            response.append([blockDateStr, str(sentAmount), sentType, str(rcvdAmount), rcvdType, str(txFee), txFeeCurrency, str(record.fiatAmount), record.fiatType, label, 'NFT {0} {1}'.format(record.itemID, record.event), record.txHash])
        elif format == 'coinledgeruniversal':
            response.append([blockDateStr, 'Defi Kingdoms', sentType, str(sentAmount), rcvdType, str(rcvdAmount), txFeeCurrency, str(txFee), label, 'NFT {0} {1}'.format(record.itemID, record.event), record.txHash])
        elif format == 'tokentax':
            response.append([label, str(rcvdAmount), rcvdType, str(sentAmount), sentType, str(txFee), txFeeCurrency, 'Defi Kingdoms', '', 'NFT {0} {1}'.format(record.itemID, record.event), blockDateStr])
        elif format == 'turbotax':
            response.append([blockDateStr, label, sentType, str(sentAmount), rcvdType, str(rcvdAmount), txFeeCurrency, str(txFee), record.fiatType, str(record.fiatAmount), 'NFT {0} {1}'.format(record.itemID, record.event), record.txHash])
        else:
            response.append(['tavern', blockDateStr, record.event, record.itemType, str(record.itemID), contracts.getTokenName(record.coinType, record.network), str(record.coinCost), '', str(record.fiatAmount), record.txHash, str(txFee)])

    for record in eventRecords['swaps']:
        blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(getDateFormat(format))
        txFee = ''
        txFeeCurrency = ''
        if hasattr(record, 'fiatFeeValue'):
            txFee = record.fiatFeeValue
            txFeeCurrency = 'USD'
        if format == 'koinlyuniversal':
            response.append([blockDateStr, str(record.swapAmount), contracts.getTokenName(record.swapType, record.network), str(record.receiveAmount), contracts.getTokenName(record.receiveType, record.network), str(txFee), txFeeCurrency, str(record.fiatSwapValue), record.fiatType, '', 'swap', record.txHash])
        elif format == 'coinledgeruniversal':
            response.append([blockDateStr, 'Defi Kingdoms', contracts.getTokenName(record.swapType, record.network), str(record.swapAmount), contracts.getTokenName(record.receiveType, record.network), str(record.receiveAmount), txFeeCurrency, str(txFee), '', 'Trade', record.txHash])
        elif format == 'tokentax':
            response.append(['Trade', str(record.receiveAmount), contracts.getTokenName(record.receiveType, record.network), str(record.swapAmount), contracts.getTokenName(record.swapType, record.network), str(txFee), txFeeCurrency, 'Defi Kingdoms', '', record.txHash, blockDateStr])
        elif format == 'turbotax':
            response.append([blockDateStr, 'Convert', contracts.getTokenName(record.swapType, record.network), str(record.swapAmount), contracts.getTokenName(record.receiveType, record.network), str(record.receiveAmount), txFeeCurrency, str(txFee), record.fiatType, str(record.fiatSwapValue), '', record.txHash])
        else:
            response.append(['trader', blockDateStr, 'swap', contracts.getTokenName(record.swapType, record.network), str(record.swapAmount), contracts.getTokenName(record.receiveType, record.network), str(record.receiveAmount), str(record.fiatSwapValue), str(record.fiatReceiveValue), record.txHash, str(txFee)])

    for record in eventRecords['trades']:
        blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(getDateFormat(format))
        txFee = ''
        txFeeCurrency = ''
        if hasattr(record, 'fiatFeeValue'):
            txFee = record.fiatFeeValue
            txFeeCurrency = 'USD'
        if format == 'koinlyuniversal':
            response.append([blockDateStr, str(record.swapAmount), contracts.getTokenName(record.swapType, record.network), str(record.receiveAmount), contracts.getTokenName(record.receiveType, record.network), str(txFee), txFeeCurrency, str(record.fiatSwapValue), record.fiatType, '', 'swap', record.txHash])
        elif format == 'coinledgeruniversal':
            response.append([blockDateStr, 'Defi Kingdoms', contracts.getTokenName(record.swapType, record.network), str(record.swapAmount), contracts.getTokenName(record.receiveType, record.network), str(record.receiveAmount), txFeeCurrency, str(txFee), '', 'Trade', record.txHash])
        elif format == 'tokentax':
            response.append(['Trade', str(record.receiveAmount), contracts.getTokenName(record.receiveType, record.network), str(record.swapAmount), contracts.getTokenName(record.swapType, record.network), str(txFee), txFeeCurrency, 'Defi Kingdoms', '', record.txHash, blockDateStr])
        elif format == 'turbotax':
            response.append([blockDateStr, 'Convert', contracts.getTokenName(record.swapType, record.network), str(record.swapAmount), contracts.getTokenName(record.receiveType, record.network), str(record.receiveAmount), txFeeCurrency, str(txFee), record.fiatType, str(record.fiatSwapValue), '', record.txHash])
        else:
            response.append(['bazaar', blockDateStr, 'trade', contracts.getTokenName(record.swapType, record.network), str(record.swapAmount), contracts.getTokenName(record.receiveType, record.network), str(record.receiveAmount), str(record.fiatSwapValue), str(record.fiatReceiveValue), record.txHash, str(txFee)])

    for record in eventRecords['liquidity']:
        blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(getDateFormat(format))
        txFee = ''
        txFeeCurrency = ''
        if hasattr(record, 'fiatFeeValue'):
            txFee = record.fiatFeeValue
            txFeeCurrency = 'USD'
        if format == 'koinlyuniversal':
            if record.action == 'withdraw':
                response.append([blockDateStr, '', '', str(record.coin1Amount), contracts.getTokenName(record.coin1Type, record.network), str(txFee), txFeeCurrency, str(record.coin1FiatValue), record.fiatType, '', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), record.txHash])
                response.append([blockDateStr, '', '', str(record.coin2Amount), contracts.getTokenName(record.coin2Type, record.network), str(txFee), txFeeCurrency, str(record.coin1FiatValue), record.fiatType, '', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), record.txHash])
            else:
                response.append([blockDateStr, str(record.coin1Amount), contracts.getTokenName(record.coin1Type, record.network), '', '', str(txFee), txFeeCurrency, str(record.coin1FiatValue), record.fiatType, '', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), record.txHash])
                response.append([blockDateStr, str(record.coin2Amount), contracts.getTokenName(record.coin2Type, record.network), '', '', str(txFee), txFeeCurrency, str(record.coin1FiatValue), record.fiatType, '', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), record.txHash])
        elif format == 'coinledgeruniversal':
            if record.action == 'withdraw':
                response.append([blockDateStr, 'Defi Kingdoms', '', '', contracts.getTokenName(record.coin1Type, record.network), str(record.coin1Amount), txFeeCurrency, str(txFee), 'Deposit', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), record.txHash])
                response.append([blockDateStr, 'Defi Kingdoms', '', '', contracts.getTokenName(record.coin2Type, record.network), str(record.coin2Amount), txFeeCurrency, str(txFee), 'Deposit', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), record.txHash])
            else:
                response.append([blockDateStr, 'Defi Kingdoms', contracts.getTokenName(record.coin1Type, record.network), str(record.coin1Amount), '', '', txFeeCurrency, str(txFee), 'Withdrawal', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), record.txHash])
                response.append([blockDateStr, 'Defi Kingdoms', contracts.getTokenName(record.coin2Type, record.network), str(record.coin2Amount), '', '', txFeeCurrency, str(txFee), 'Withdrawal', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), record.txHash])
        elif format == 'tokentax':
            if record.action == 'withdraw':
                response.append(['Withdrawal', str(record.coin1Amount), contracts.getTokenName(record.coin1Type, record.network), '', '', str(txFee), txFeeCurrency, 'Defi Kingdoms', '', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), blockDateStr])
                response.append(['Withdrawal', str(record.coin2Amount), contracts.getTokenName(record.coin2Type, record.network), '', '', str(txFee), txFeeCurrency, 'Defi Kingdoms', '', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), blockDateStr])
            else:
                response.append(['Deposit', '', '', str(record.coin1Amount), contracts.getTokenName(record.coin1Type, record.network), str(txFee), txFeeCurrency, 'Defi Kingdoms', '', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), blockDateStr])
                response.append(['Deposit', '', '', str(record.coin2Amount), contracts.getTokenName(record.coin2Type, record.network), str(txFee), txFeeCurrency, 'Defi Kingdoms', '', '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), blockDateStr])
        elif format == 'turbotax':
            if record.action == 'withdraw':
                response.append([blockDateStr, 'Liquidity Pool', '', '', contracts.getTokenName(record.coin1Type, record.network), str(record.coin1Amount), txFeeCurrency, str(txFee), record.fiatType, str(record.coin1FiatValue), '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), record.txHash])
                response.append([blockDateStr, 'Liquidity Pool', '', '', contracts.getTokenName(record.coin2Type, record.network), str(record.coin2Amount), txFeeCurrency, str(txFee), record.fiatType, str(record.coin1FiatValue), '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), record.txHash])
            else:
                response.append([blockDateStr, 'Liquidity Pool', contracts.getTokenName(record.coin1Type, record.network), str(record.coin1Amount), '', '', txFeeCurrency, str(txFee), record.fiatType, str(record.coin1FiatValue), '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), record.txHash])
                response.append([blockDateStr, 'Liquidity Pool', contracts.getTokenName(record.coin2Type, record.network), str(record.coin2Amount), '', '', txFeeCurrency, str(txFee), record.fiatType, str(record.coin1FiatValue), '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), record.txHash])
        else:
            response.append(['liquidity', blockDateStr, '{0} {1} to {2}'.format(record.action, record.poolAmount, contracts.getTokenName(record.poolAddress, record.network)), contracts.getTokenName(record.coin1Type, record.network), str(record.coin1Amount), contracts.getTokenName(record.coin2Type, record.network), str(record.coin2Amount), str(record.coin1FiatValue), str(record.coin2FiatValue), record.txHash, str(txFee)])

    for record in eventRecords['gardens']:
        blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(getDateFormat(format))
        txFee = ''
        txFeeCurrency = ''
        if hasattr(record, 'fiatFeeValue'):
            txFee = record.fiatFeeValue
            txFeeCurrency = 'USD'
        if format in ['koinlyuniversal','coinledgeruniversal','tokentax','turbotax']:
            if record.event == 'deposit':
                sentAmount = record.coinAmount
                sentType = contracts.getTokenName(record.coinType, record.network)
                rcvdAmount = ''
                rcvdType = ''
            else:
                sentAmount = ''
                sentType = ''
                rcvdAmount = record.coinAmount
                rcvdType = contracts.getTokenName(record.coinType, record.network)
        label = getRecordLabel(format, 'gardens', record.event)
        if format == 'koinlyuniversal':
            response.append([blockDateStr, str(sentAmount), sentType, str(rcvdAmount), rcvdType, str(txFee), txFeeCurrency, str(record.fiatValue), record.fiatType, label, record.event, record.txHash])
        elif format == 'coinledgeruniversal':
            response.append([blockDateStr, 'Defi Kingdoms', sentType, str(sentAmount), rcvdType, str(rcvdAmount), txFeeCurrency, str(txFee), label, record.event, record.txHash])
        elif format == 'tokentax':
            response.append([label, str(rcvdAmount), rcvdType, str(sentAmount), sentType, str(txFee), txFeeCurrency, 'Defi Kingdoms', '', record.event, blockDateStr])
        elif format == 'turbotax':
            response.append([blockDateStr, label, sentType, str(sentAmount), rcvdType, str(rcvdAmount), txFeeCurrency, str(txFee), record.fiatType, str(record.fiatValue), record.event, record.txHash])
        else:
            if 'Pangolin LP' in contracts.getTokenName(record.coinType, record.network):
                location = 'Pangolin'
            elif 'Crystal LP' in contracts.getTokenName(record.coinType, record.network):
                location = 'Crystalvale'
            else:
                location = 'Serendale'
            response.append([location, blockDateStr, record.event, contracts.getTokenName(record.coinType, record.network), str(record.coinAmount), '', '', str(record.fiatValue), '', record.txHash, str(txFee)])

    for record in eventRecords['bank']:
        blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(getDateFormat(format))
        txFee = ''
        txFeeCurrency = ''
        if hasattr(record, 'fiatFeeValue'):
            txFee = record.fiatFeeValue
            txFeeCurrency = 'USD'
        if format in ['koinlyuniversal','coinledgeruniversal','tokentax','turbotax']:
            if record.action == 'deposit':
                sentAmount = record.coinAmount
                sentType = contracts.getTokenName(record.coinType, record.network)
                if record.xRate > 0:
                    rcvdAmount = record.coinAmount / record.xRate
                else:
                    rcvdAmount = 0
                rcvdType = 'xJewel'
            elif record.action == 'claim':
                rcvdAmount = record.coinAmount
                rcvdType = contracts.getTokenName(record.coinType, record.network)
                sentAmount = 0
                sentType = ''
            else:
                if record.xRate > 0:
                    sentAmount = record.coinAmount / record.xRate
                    sentType = 'xJewel'
                else:
                    sentAmount = ''
                    sentType = ''
                rcvdAmount = record.coinAmount
                rcvdType = contracts.getTokenName(record.coinType, record.network)
        if format == 'koinlyuniversal':
            response.append([blockDateStr, str(sentAmount), sentType, str(rcvdAmount), rcvdType, str(txFee), txFeeCurrency, str(record.fiatValue), record.fiatType, '', 'bank {0}'.format(record.action), record.txHash])
        elif format == 'coinledgeruniversal':
            response.append([blockDateStr, 'Defi Kingdoms', sentType, str(sentAmount), rcvdType, str(rcvdAmount), txFeeCurrency, str(txFee), '', 'bank {0}'.format(record.action), record.txHash])
        elif format == 'tokentax':
            response.append(['Trade', str(rcvdAmount), rcvdType, str(sentAmount), sentType, str(txFee), txFeeCurrency, 'Defi Kingdoms', '', 'bank {0}'.format(record.action), blockDateStr])
        elif format == 'turbotax':
            response.append([blockDateStr, 'Staking', sentType, str(sentAmount), rcvdType, str(rcvdAmount), txFeeCurrency, str(txFee), record.fiatType, str(record.fiatValue), 'bank {0}'.format(record.action), record.txHash])
        else:
            response.append(['bank', blockDateStr, record.action, 'xRate', str(record.xRate), contracts.getTokenName(record.coinType, record.network), str(record.coinAmount), '', str(record.fiatValue), record.txHash, str(txFee)])

    for record in eventRecords['alchemist']:
        blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(getDateFormat(format))
        txFee = ''
        txFeeCurrency = ''
        if hasattr(record, 'fiatFeeValue'):
            txFee = record.fiatFeeValue
            txFeeCurrency = 'USD'
        if format == 'koinlyuniversal':
            response.append([blockDateStr, '', '"' + record.craftingCosts + '"', str(record.craftingAmount), contracts.getTokenName(record.craftingType, record.network), str(txFee), txFeeCurrency, str(record.fiatValue), record.fiatType, 'ignored', 'potion crafting', record.txHash])
        elif format == 'coinledgeruniversal':
            response.append([blockDateStr, 'Defi Kingdoms', '"' + record.craftingCosts + '"', '', contracts.getTokenName(record.craftingType, record.network), str(record.craftingAmount), txFeeCurrency, str(txFee), 'Deposit', 'potion crafting', record.txHash])
        elif format == 'tokentax':
            response.append(['Trade', str(record.craftingAmount), contracts.getTokenName(record.craftingType, record.network), '', '"' + record.craftingCosts + '"', str(txFee), txFeeCurrency, 'Defi Kingdoms', '', 'potion crafting', blockDateStr])
        elif format == 'turbotax':
            response.append([blockDateStr, 'Other', '"' + record.craftingCosts + '"', '', contracts.getTokenName(record.craftingType, record.network), str(record.craftingAmount), txFeeCurrency, str(txFee), record.fiatType, str(record.fiatValue), 'potion crafting', record.txHash])
        else:
            response.append(['alchemist', blockDateStr, 'crafting', contracts.getTokenName(record.craftingType, record.network), str(record.craftingAmount), '"' + record.craftingCosts + '"', '', str(record.fiatValue), str(record.costsFiatValue), record.txHash, str(txFee)])

    for record in eventRecords['airdrops']:
        blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(getDateFormat(format))
        txFee = ''
        txFeeCurrency = ''
        if hasattr(record, 'fiatFeeValue'):
            txFee = record.fiatFeeValue
            txFeeCurrency = 'USD'
        if format == 'koinlyuniversal':
            response.append([blockDateStr, '', '', str(record.tokenAmount), contracts.getTokenName(record.tokenReceived, record.network), str(txFee), txFeeCurrency, str(record.fiatValue), record.fiatType, 'airdrop', '', record.txHash])
        elif format == 'coinledgeruniversal':
            response.append([blockDateStr, 'Defi Kingdoms', '', '', contracts.getTokenName(record.tokenReceived, record.network), str(record.tokenAmount), txFeeCurrency, str(txFee), 'Airdrop', '', record.txHash])
        elif format == 'tokentax':
            response.append(['Income', str(record.tokenAmount), contracts.getTokenName(record.tokenReceived, record.network), '', '', str(txFee), txFeeCurrency, 'Defi Kingdoms', '', 'airdrop', blockDateStr])
        elif format == 'turbotax':
            response.append([blockDateStr, 'Airdrop', '', '', contracts.getTokenName(record.tokenReceived, record.network), str(record.tokenAmount), txFeeCurrency, str(txFee), record.fiatType, str(record.fiatValue), '', record.txHash])
        else:
            response.append(['airdrops', blockDateStr, '', contracts.getTokenName(record.tokenReceived, record.network), str(record.tokenAmount), '', '', str(record.fiatValue), '', record.txHash, str(txFee)])

    for record in eventRecords['quests']:
        blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(getDateFormat(format))
        txFee = ''
        txFeeCurrency = ''
        if hasattr(record, 'fiatFeeValue'):
            txFee = record.fiatFeeValue
            txFeeCurrency = 'USD'
        if format == 'koinlyuniversal':
            response.append([blockDateStr, '', '', str(record.rewardAmount), contracts.getTokenName(record.rewardType, record.network), str(txFee), txFeeCurrency, str(record.fiatValue), record.fiatType, 'reward', 'quest', record.txHash])
        elif format == 'coinledgeruniversal':
            response.append([blockDateStr, '', '', contracts.getTokenName(record.rewardType, record.network), str(record.rewardAmount), txFeeCurrency, str(txFee), 'Staking', 'quest', record.txHash])
        elif format == 'tokentax':
            response.append(['Income', str(record.rewardAmount), contracts.getTokenName(record.rewardType, record.network), '', '', str(txFee), txFeeCurrency, 'Defi Kingdoms', '', 'quest', blockDateStr])
        elif format == 'turbotax':
            response.append([blockDateStr, 'Staking', '', '', contracts.getTokenName(record.rewardType, record.network), str(record.rewardAmount), txFeeCurrency, str(txFee), record.fiatType, str(record.fiatValue), 'quest', record.txHash])
        else:
            response.append(['quest', blockDateStr, 'rewards', contracts.getTokenName(record.rewardType, record.network), str(record.rewardAmount), '', '', str(record.fiatValue), '', record.txHash, str(txFee)])

    for record in eventRecords['wallet']:
        blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(getDateFormat(format))
        txFee = ''
        txFeeCurrency = ''
        if hasattr(record, 'fiatFeeValue'):
            txFee = record.fiatFeeValue
            txFeeCurrency = 'USD'
        if format in ['koinlyuniversal','coinledgeruniversal','tokentax','turbotax']:
            if record.action == 'deposit':
                sentAmount = ''
                sentType = ''
                rcvdAmount = record.coinAmount
                rcvdType = contracts.getTokenName(record.coinType, record.network)
            else:
                sentAmount = record.coinAmount
                sentType = contracts.getTokenName(record.coinType, record.network)
                rcvdAmount = ''
                rcvdType = ''
        if format == 'koinlyuniversal':
            response.append([blockDateStr, str(sentAmount), sentType, str(rcvdAmount), rcvdType, str(txFee), txFeeCurrency, str(record.fiatValue), record.fiatType, '', 'wallet transfer', record.txHash])
        elif format == 'coinledgeruniversal':
            response.append([blockDateStr, 'Defi Kingdoms', sentType, str(sentAmount), rcvdType, str(rcvdAmount), txFeeCurrency, str(txFee), record.action, 'wallet transfer', record.txHash])
        elif format == 'tokentax':
            response.append([record.action, str(rcvdAmount), rcvdType, str(sentAmount), sentType, str(txFee), txFeeCurrency, 'Defi Kingdoms', '', 'wallet transfer', blockDateStr])
        elif format == 'turbotax':
            response.append([blockDateStr, 'Transfer', sentType, str(sentAmount), rcvdType, str(rcvdAmount), txFeeCurrency, str(txFee), record.fiatType, str(record.fiatValue), 'wallet transfer', record.txHash])
        else:
            response.append(['wallet', blockDateStr, record.action, contracts.getTokenName(record.coinType, record.network), str(record.coinAmount), '', '', str(record.fiatValue), '', record.txHash, str(txFee)])

    if 'lending' in eventRecords:
        for record in eventRecords['lending']:
            blockDateStr = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime(getDateFormat(format))
            txFee = ''
            txFeeCurrency = ''
            if hasattr(record, 'fiatFeeValue'):
                txFee = record.fiatFeeValue
                txFeeCurrency = 'USD'
            if format in ['koinlyuniversal','coinledgeruniversal','tokentax','turbotax']:
                if record.event in ['redeem','borrow']:
                    sentAmount = ''
                    sentType = ''
                    rcvdAmount = record.coinAmount
                    rcvdType = contracts.getTokenName(record.coinType, record.network)
                else:
                    sentAmount = record.coinAmount
                    sentType = contracts.getTokenName(record.coinType, record.network)
                    rcvdAmount = ''
                    rcvdType = ''
            if format == 'koinlyuniversal':
                response.append([blockDateStr, str(sentAmount), sentType, str(rcvdAmount), rcvdType, str(txFee), txFeeCurrency, str(record.fiatValue), record.fiatType, '', 'lending {0}'.format(record.event), record.txHash])
            elif format == 'coinledgeruniversal':
                response.append([blockDateStr, sentType, str(sentAmount), rcvdType, str(rcvdAmount), txFeeCurrency, str(txFee), '', 'lending {0}'.format(record.event), record.txHash])
            elif format == 'tokentax':
                response.append([record.event, str(rcvdAmount), rcvdType, str(sentAmount), sentType, str(txFee), txFeeCurrency, 'Defi Kingdoms', '', 'lending {0}'.format(record.event), blockDateStr])
            elif format == 'turbotax':
                response.append([blockDateStr, 'Other', sentType, str(sentAmount), rcvdType, str(rcvdAmount), txFeeCurrency, str(txFee), record.fiatType, str(record.fiatValue), 'lending {0}'.format(record.event), record.txHash])
            else:
                response.append(['lending', blockDateStr, record.event, contracts.getTokenName(record.coinType, record.network), str(record.coinAmount), '', '', str(record.fiatValue), '', record.txHash, str(txFee)])

    return response