#!/usr/bin/env python3
# Price data resources
import requests
import sys
import json
import datetime
import logging
import decimal
import db
import contracts

token_map = {
    '0xcF664087a5bB0237a0BAd6742852ec6c8d69A27a': 'harmony',
    '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F': 'defi-kingdoms',
    '0x985458E523dB3d53125813eD68c274899e9DfAb4': 'usd-coin',
    '0x3C2B8Be99c50593081EAA2A724F0B8285F5aba8f': 'tether',
    '0x3095c7557bCb296ccc6e363DE01b760bA031F2d9': 'bitcoin',
    '0x6983D1E6DEf3690C4d616b13597A09e6193EA013': 'ethereum',
    '0xFbdd194376de19a88118e84E279b977f165d01b8': 'matic-network',
    '0x735aBE48e8782948a37C7765ECb76b98CdE97B0F': 'fantom',
    '0xCf1709Ad76A79d5a60210F23e81cE2460542A836': 'tranquil-finance',
    '0xb1f6E61E1e113625593a22fa6aa94F8052bc39E0': 'binancecoin',
    '0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7': 'avalanche-2',
    '0xb12c13e66AdE1F72f71834f2FC5082Db8C091358': 'avalanche-2',
    '0x4f60a160D8C2DDdaAfe16FCC57566dB84D674BD6': 'defi-kingdoms'
}

today_prices = {}

def priceLookup(timestamp, token, fiatType='usd'):
    lookupDate = datetime.date.fromtimestamp(timestamp).strftime('%d-%m-%Y')
    # if token is in map, switch to gecko token name instead
    if token in token_map:
        token = token_map[token]
    # Calculate based on gold price if convertible to gold
    if token in contracts.gold_values and contracts.gold_values[token] > 0:
        return decimal.Decimal(getPrice('0x3a4edcf3312f44ef027acfd8c21382a5259936e7', lookupDate, fiatType) * contracts.gold_values[token])
    else:
        return decimal.Decimal(getPrice(token, lookupDate, fiatType))

# Date format DD-MM-YYYY for da gecko api
def fetchPriceData(token, date):
    realDate = datetime.datetime.strptime(date, '%d-%m-%Y')
    # Coin Gecko only has prices from October 20th 2021 forward for JEWEL
    if (realDate > datetime.datetime.strptime('19-10-2021', '%d-%m-%Y') or token != 'defi-kingdoms') and token[0] != '0':
        gecko_uri = "https://api.coingecko.com/api/v3/coins/{0}/history?date={1}&localization=false".format(token, date)
        r = requests.get(gecko_uri)
        if r.status_code == 200:
            result = r.json()
            prices = result['market_data']['current_price']
            marketcap = result['market_data']['market_cap']
            volume = result['market_data']['total_volume']
            db.savePriceData(date, token, json.dumps(prices), json.dumps(marketcap), json.dumps(volume))
            logging.info('Saved a new price for {0} on {1} from coin gecko'.format(token, date))
            result = prices
        else:
            result = "Error: failed to get prices - {0}".format(r.text)
            logging.error(result + '\n')
    else:
        # Lookup up price in DFK graph for some stuff
        result = fetchItemPrice(token, date)
    return result

# Get price of stuff from DFK dex graph for stuff that is not listed on CoinGecko or for coins before they were there
def fetchItemPrice(token, date):
    # adjust for graphql inputs
    realDate = int(datetime.datetime.strptime(date, '%d-%m-%Y').timestamp())
    #### temporarily don't try to lookup from 12/19 forward because it will fail, graph empty
    #if realDate >= int(datetime.datetime.strptime('19-12-2021', '%d-%m-%Y').timestamp()):
    #    return json.loads('{ "usd" : 0.0 }')
    #####
    spreadDate = realDate + 86401
    graphToken = token
    if token == 'defi-kingdoms':
        graphToken = '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F'
    query = """query {
        tokenDayDatas(
            where: {date_gt: %d
                    date_lt: %d
                    token: "%s" } 
        ) 
        {
            priceUSD
            totalLiquidityUSD
            dailyVolumeUSD
        }
    }
    """
    data = query % (realDate, spreadDate, graphToken.lower())
    graph_uri = "http://graph3.defikingdoms.com/subgraphs/name/defikingdoms/dex"
    r = requests.post(graph_uri, json={'query': data})
    if r.status_code == 200:
        result = r.json()
        if len(result['data']['tokenDayDatas']) > 0:
            price = result['data']['tokenDayDatas'][0]['priceUSD']
            liquid = result['data']['tokenDayDatas'][0]['totalLiquidityUSD']
            volume = result['data']['tokenDayDatas'][0]['dailyVolumeUSD']
            db.savePriceData(date, token, '{ "usd" : %s }' % price, '{ "usd" : %s }' % liquid, '{ "usd" : %s }' % volume)
            logging.info('Saved a new price for {0} on {1} from DFK Graph'.format(token, date))
            result = json.loads('{ "usd" : %s }' % price)
        else:
            logging.info('Failed to lookup a price for {0} on {1}, trying current price'.format(token, date))
            # last ditch effort, try to find a current price pair data with jewel and base on jewel to USD
            # use cache for today prices since we dont save in db and we aren't hitting graph so much
            if token in today_prices:
                jewelPair = today_prices[token]
            else:
                jewelPair = fetchCurrentPrice(token, '0x72cb10c6bfa5624dd07ef608027e366bd690048f')
            price = 0
            if len(jewelPair) == 2:
                today_prices[token] = jewelPair
                jewelPrice = priceLookup(realDate, '0x72Cb10C6bfA5624dD07Ef608027E366bd690048F')
                logging.debug('got current price ' + str(jewelPair[1]))
                price = decimal.Decimal(jewelPair[1]) * jewelPrice
                result = json.loads('{ "usd" : %s }' % price)
            else:
                result = json.loads('{ "usd" : 0.0 }')
    else:
        result = "Error: failed to get prices - {0} {1}".format(str(r.status_code), r.text)
        logging.error(result)
        result = json.loads('{ "usd" : 0.0 }')
    return result

# Just get current prices on a pair
def fetchCurrentPrice(token0, token1):
    query = """query {
        pairs(
            where: {token0: "%s"
                    token1: "%s" } 
        ) 
        {
            id
            token0Price
            token1Price
        }
    }
    """
    data = query % (token0.lower(), token1.lower())
    graph_uri = "http://graph3.defikingdoms.com/subgraphs/name/defikingdoms/dex"
    r = requests.post(graph_uri, json={'query': data})
    if r.status_code == 200:
        result = r.json()
        if len(result['data']['pairs']) > 0:
            price0 = result['data']['pairs'][0]['token0Price']
            price1 = result['data']['pairs'][0]['token1Price']
            result = [price0, price1]
        else:
            # TODO: Update this to be able to fetch for Gold paired quest rewards
            logging.error('Failed to lookup a price for {0} / {1}'.format(token0, token1))
            result = []
    else:
        result = "Error: failed to get prices - {0} {1}".format(str(r.status_code), r.text)
        logging.error(result)
        result = []
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

def main():
    # Initialize database and ensure price history is pre-populated
    db.createDatabase()
    startDate = datetime.datetime.strptime('01-01-2021', '%d-%m-%Y')
    endDate = datetime.datetime.strptime('15-12-2021', '%d-%m-%Y')
    sys.stdout.write(str(getPrice('0x3a4edcf3312f44ef027acfd8c21382a5259936e7', endDate.strftime('%d-%m-%Y'))))
    #while startDate <= endDate:
    #    sys.stdout.write(getPrice('harmony', startDate.strftime('%d-%m-%Y'), 'usd'))
    #    sys.stdout.write(startDate)
    #    startDate += datetime.timedelta(days=1)
    #    time.sleep(10)


if __name__ == "__main__":
	main()