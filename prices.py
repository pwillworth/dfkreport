#!/usr/bin/env python3
# Price data resources
import requests
import sys
from web3 import Web3
import json
import datetime
import logging
import decimal
import db
import contracts
import nets

token_map = {
    '0xcF664087a5bB0237a0BAd6742852ec6c8d69A27a': 'harmony',
    '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F': 'defi-kingdoms',
    '0x985458E523dB3d53125813eD68c274899e9DfAb4': 'usd-coin',
    '0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664': 'usd-coin',
    '0x3C2B8Be99c50593081EAA2A724F0B8285F5aba8f': 'tether',
    '0x3095c7557bCb296ccc6e363DE01b760bA031F2d9': 'bitcoin',
    '0xdc54046c0451f9269FEe1840aeC808D36015697d': 'bitcoin',
    '0x6983D1E6DEf3690C4d616b13597A09e6193EA013': 'ethereum',
    '0xFbdd194376de19a88118e84E279b977f165d01b8': 'matic-network',
    '0x735aBE48e8782948a37C7765ECb76b98CdE97B0F': 'fantom',
    '0xCf1709Ad76A79d5a60210F23e81cE2460542A836': 'tranquil-finance',
    '0x22D62b19b7039333ad773b7185BB61294F3AdC19': 'tranquil-staked-one',
    '0x892D81221484F690C0a97d3DD18B9144A3ECDFB7': 'cosmic-universe-magic-token',
    '0xb1f6E61E1e113625593a22fa6aa94F8052bc39E0': 'binancecoin',
    '0xCCb93dABD71c8Dad03Fc4CE5559dC3D89F67a260': 'defi-kingdoms',
    '0xB57B60DeBDB0b8172bb6316a9164bd3C695F133a': 'avalanche-2',
    '0x3AD9DFE640E1A9Cc1D9B0948620820D975c3803a': 'usd-coin',
    '0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7': 'avalanche-2',
    '0xb12c13e66AdE1F72f71834f2FC5082Db8C091358': 'avalanche-2',
    '0x4f60a160D8C2DDdaAfe16FCC57566dB84D674BD6': 'defi-kingdoms',
    '0x60781C2586D68229fde47564546784ab3fACA982': 'pangolin'
}

decimal_units = {
    0: 'noether',
    1: 'wei',
    3: 'kwei',
    6: 'mwei',
    9: 'gwei',
    12: 'micro',
    15: 'milli',
    18: 'ether',
    21: 'kether',
    24: 'mether',
    27: 'gether',
    30: 'tether',
}

today_prices = {}

def priceLookup(timestamp, token, fiatType='usd'):
    lookupDate = datetime.date.fromtimestamp(timestamp).strftime('%d-%m-%Y')
    # if token is in map, switch to gecko token name instead
    if token in token_map:
        token = token_map[token]
    # Calculate based on gold price if convertible to gold
    if token in contracts.gold_values and contracts.gold_values[token] > 0:
        return decimal.Decimal(getPrice('0x3a4EDcf3312f44EF027acfd8c21382a5259936e7', lookupDate, fiatType) * contracts.gold_values[token])
    else:
        return decimal.Decimal(getPrice(token, lookupDate, fiatType))

# Date format DD-MM-YYYY for da gecko api
def fetchPriceData(token, date):
    realDate = datetime.datetime.strptime(date, '%d-%m-%Y')
    prices = None
    # Coin Gecko only has prices from October 20th 2021 forward for JEWEL
    if (realDate > datetime.datetime.strptime('19-10-2021', '%d-%m-%Y') or token != 'defi-kingdoms') and token[0] != '0':
        gecko_uri = "https://api.coingecko.com/api/v3/coins/{0}/history?date={1}&localization=false".format(token, date)
        r = requests.get(gecko_uri)
        if r.status_code == 200:
            result = r.json()
            try:
                prices = result['market_data']['current_price']
                marketcap = result['market_data']['market_cap']
                volume = result['market_data']['total_volume']
            except Exception as err:
                result = "Error: failed to get prices no market data {0}".format(r.text)
                logging.error(result + '\n')
            if prices != None:
                db.savePriceData(date, token, json.dumps(prices), json.dumps(marketcap), json.dumps(volume))
                logging.info('Saved a new price for {0} on {1} from coin gecko'.format(token, date))
                result = prices
        else:
            result = "Error: failed to get prices - {0}".format(r.text)
            logging.error(result + '\n')
    else:
        # Lookup up price in DFK contract for some stuff
        result = fetchItemPrice(token, date)
    return result

# Get price of stuff from DFK dex contract for stuff that is not listed on CoinGecko or for coins before they were there
def fetchItemPrice(token, date):
    logging.info('Failed to lookup a price for {0} on {1}, trying dexscreener price'.format(token, date))
    # First check if we can get price history from dexscreener before using today price
    r = None
    price = None
    pairAddress = None
    jewelPrice = 0
    if token in contracts.serendale_pairs:
        pairAddress = contracts.serendale_pairs[token]
    elif token in contracts.serendale_jewel_pairs:
        pairAddress = contracts.serendale_jewel_pairs[token]
        jewelPrice = getPrice('defi-kingdoms', date)

    if pairAddress != None:
        dateTimestamp = datetime.datetime.strptime(date, '%d-%m-%Y').timestamp()
        ds_uri = "https://io5.dexscreener.io/u/chart/bars/harmony/{0}?from={1}&to={2}&res=1440&cb=2".format(pairAddress, int((dateTimestamp-86400) * (10 ** 3)), int(dateTimestamp * (10 ** 3)))
        try:
            r = requests.get(ds_uri)
        except Exception as err:
            logging.error('Dexscreener price fetch failure: {0}'.format(str(err)))

    if r != None and r.status_code == 200:
        result = r.json()
        try:
            if token in contracts.serendale_pairs:
                price = result['bars'][0]['closeUsd']
            elif token in contracts.serendale_jewel_pairs:
                price = decimal.Decimal(jewelPrice) / decimal.Decimal(result['bars'][0]['close'])
        except Exception as err:
            result = "Error: failed to get historical price no market data {0} or error {1}".format(r.text, str(err))
            logging.error(result)
    else:
        if r != None:
            logging.warning('Dexscreener fetch failure {0} - {1}'.format(str(r.status_code), r.text))

    if price != None:
        logging.info('Found existing price to use in dexscreener')
        result = json.loads('{ "usd" : %s }' % price)
    else:
        # last ditch effort, try to find a current price pair data with jewel and base on jewel to USD
        logging.info('getting current price from dex.')
        if token in today_prices:
            price = today_prices[token]
        else:
            # Use through token address for right Jewel address incase looking up crystalvale crystal or xJewel
            if token in ['0x04b9dA42306B023f3572e106B11D82aAd9D32EBb', '0x77f2656d04E158f915bC22f07B779D94c1DC47Ff']:
                price = getCurrentPrice(token, '0xCCb93dABD71c8Dad03Fc4CE5559dC3D89F67a260')
            else:
                price = getCurrentPrice(token, '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F')
        if price >= 0:
            today_prices[token] = price
            result = json.loads('{ "usd" : %s }' % price)
            db.savePriceData(datetime.datetime.now().strftime('%d-%m-%Y'), token, '{ "usd" : %s }' % price, '{ "usd" : 0.0 }', '{ "usd" : 0.0 }')
        else:
            result = json.loads('{ "usd" : 0.0 }')

    return result

def getPrice(token, date, fiatType='usd'):
    row = db.findPriceData(date, token)
    if row != None:
        logging.debug('Found existing price to use in database')
        prices = json.loads(row[2])
    else:
        prices = fetchPriceData(token, date)

    if fiatType in prices:
        return prices[fiatType]
    else:
        logging.error('Failed to lookup a price for {0} on {1}: {2}'.format(token, date, prices))
        return -1

# Return USD price of token based on its pair to throughToken to 1USDC
def getCurrentPrice(token, throughToken):
    if token in ['0x04b9dA42306B023f3572e106B11D82aAd9D32EBb', '0x77f2656d04E158f915bC22f07B779D94c1DC47Ff']:
        w3 = Web3(Web3.HTTPProvider(nets.dfk_web3))
        ABI = contracts.getABI('UniswapV2Router02')
        contract = w3.eth.contract(address='0x3C351E1afdd1b1BC44e931E12D4E05D6125eaeCa', abi=ABI)
    else:
        w3 = Web3(Web3.HTTPProvider(nets.hmy_web3))
        ABI = contracts.getABI('UniswapV2Router02')
        contract = w3.eth.contract(address='0x24ad62502d1C652Cc7684081169D04896aC20f30', abi=ABI)

    tokenDecimals = getTokenInfo(w3, token)[1]
    throughTokenDecimals = getTokenInfo(w3, throughToken)[1]
    # Sometimes 8 decimal tokens will try to get looked up, so skip those
    if tokenDecimals in decimal_units and throughTokenDecimals in decimal_units:
        tokenOne = 1 if tokenDecimals == 0 else Web3.toWei(1, decimal_units[tokenDecimals])
        throughTokenOne = Web3.toWei(1, decimal_units[throughTokenDecimals])
    else:
        return -1

    price = -1
    try:
        token0Amount = contract.functions.getAmountsOut(tokenOne, [token, throughToken]).call()
        if token in ['0x04b9dA42306B023f3572e106B11D82aAd9D32EBb', '0x77f2656d04E158f915bC22f07B779D94c1DC47Ff']:
            # Just use daily jewel price for crystalvale for now until stable pair shows up
            token1Amount = [1, Web3.toWei(getPrice('defi-kingdoms', datetime.datetime.now().strftime('%d-%m-%Y')), 'mwei')]
        else:
            token1Amount = contract.functions.getAmountsOut(throughTokenOne, [throughToken, '0x985458E523dB3d53125813eD68c274899e9DfAb4']).call()
        price = contracts.valueFromWei(token0Amount[1], throughToken) * contracts.valueFromWei(token1Amount[1], '0x985458E523dB3d53125813eD68c274899e9DfAb4')
    except Exception as err:
        logging.error('Price lookup failed {0}'.format(err))

    return price

def getTokenInfo(w3, address):
    ABI = contracts.getABI('ERC20')
    contract = w3.eth.contract(address=address, abi=ABI)
    try:
        symbol = contract.functions.symbol().call()
        decimals = contract.functions.decimals().call()
        name = contract.functions.name().call()
    except Exception as err:
        logging.error('Failed to get token info for {0}'.format(address))
        return ['NA', 18, 'NA']

    return [symbol, decimals, name]


def main():
    logging.basicConfig(level=logging.INFO)
    # Initialize database and ensure price history is pre-populated
    startDate = datetime.datetime.strptime('01-01-2021', '%d-%m-%Y')
    endDate = datetime.datetime.strptime('15-12-2021', '%d-%m-%Y')
    result = fetchItemPrice('0x9678518e04Fe02FB30b55e2D0e554E26306d0892', '15-04-2022')
    sys.stdout.write(str(result))
    #sys.stdout.write(str(priceLookup(1648745572, '0x04b9dA42306B023f3572e106B11D82aAd9D32EBb')))
    #sys.stdout.write(str(getCurrentPrice(w3, '0x95d02C1Dc58F05A015275eB49E107137D9Ee81Dc', '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F')))
    #while startDate <= endDate:
    #    sys.stdout.write(getPrice('harmony', startDate.strftime('%d-%m-%Y'), 'usd'))
    #    sys.stdout.write(startDate)
    #    startDate += datetime.timedelta(days=1)
    #    time.sleep(10)


if __name__ == "__main__":
	main()