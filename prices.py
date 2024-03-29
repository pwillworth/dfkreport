#!/usr/bin/env python3
# Price data resources
import requests
import os
from web3 import Web3
import json
import datetime
from datetime import timezone
import logging
import decimal
import db
import nets
import contracts

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
    '0x04b9dA42306B023f3572e106B11D82aAd9D32EBb': 'defi-kingdoms-crystal',
    '0x4f60a160D8C2DDdaAfe16FCC57566dB84D674BD6': 'defi-kingdoms',
    '0x60781C2586D68229fde47564546784ab3fACA982': 'pangolin',
    '0xfBDF0E31808d0aa7b9509AA6aBC9754E48C58852': 'ethereum',
    '0x7516EB8B8Edfa420f540a162335eACF3ea05a247': 'bitcoin',
    '0x97855Ba65aa7ed2F65Ed832a776537268158B78a': 'klay-token',
    '0xD17a41Cd199edF1093A9Be4404EaDe52Ec19698e': 'matic-network',
    '0x2Df041186C844F8a2e2b63F16145Bc6Ff7d23E25': 'fantom',
    '0xe4f05A66Ec68B54A58B17c22107b02e0232cC817': 'klay-token',
    '0x19Aac5f612f524B754CA7e7c41cbFa2E981A4432': 'klay-token',
    '0x30C103f8f5A3A732DFe2dCE1Cc9446f545527b43': 'defi-kingdoms', # jewel on klaytn
    '0xcd8fe44a29db9159db36f96570d7a4d91986f528': 'avalanche-2',
    '0x34d21b1e550D73cee41151c77F3c73359527a396': 'ethereum', #oETH on klaytn
    '0x16D0e1fBD024c600Ca0380A4C5D57Ee7a2eCBf9c': 'bitcoin' #oWBTC on klaytn
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

def getABI(contractName):
    location = os.path.abspath(__file__)
    with open('{0}/abi/{1}.json'.format('/'.join(location.split('/')[0:-1]), contractName), 'r') as f:
        ABI = f.read()
    return ABI

def getTokenInfo(w3, address):
    ABI = getABI('ERC20')
    contract = w3.eth.contract(address=address, abi=ABI)
    try:
        symbol = contract.functions.symbol().call()
        decimals = contract.functions.decimals().call()
        name = contract.functions.name().call()
    except Exception as err:
        logging.error('Failed to get token info for {0}'.format(address))
        return ['NA', 18, 'NA']

    return [symbol, decimals, name]

class PriceData():
    def __init__(self, fiatType='usd'):
        self.fiatType = fiatType

    today_prices = {}
    price_cache = {}
    price_cache_date = ''

    def priceLookup(self, timestamp, token, network, fiatType='usd'):
        lookupDate = datetime.date.fromtimestamp(timestamp).strftime('%d-%m-%Y')
        if network == 'harmony':
            goldValues = contracts.HARMONY_GOLD_VALUES
        elif network == 'klaytn':
            goldValues = contracts.KLAYTN_GOLD_VALUES
        else:
            goldValues = contracts.DFKCHAIN_GOLD_VALUES
        # if token is in map, switch to gecko token name instead
        if token in token_map:
            token = token_map[token]
        # Calculate based on gold price if convertible to gold
        if token in goldValues and goldValues[token] > 0:
            return decimal.Decimal(self.getPrice(contracts.GOLD_TOKENS[network], lookupDate, fiatType) * goldValues[token])
        else:
            return decimal.Decimal(self.getPrice(token, lookupDate, fiatType))

    # Date format DD-MM-YYYY for da gecko api
    def fetchPriceData(self, token, date):
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
            result = self.fetchItemPrice(token)
        return result

    # Get price of stuff from DFK dex contract for stuff that is not listed on CoinGecko or for coins before they were there
    def fetchItemPrice(self, token):
        price = None

        # last ditch effort, try to find a current price pair data with jewel and base on jewel to USD
        if token in self.today_prices:
            price = self.today_prices[token]
        else:
            # Use through token address for right Jewel address incase looking up crystalvale crystal or xJewel
            logging.info('getting current price from dex.')
            # TODO Improve item price storage to track network so we dont have to ignore tokens with dup address across networks
            # doing a mostly ok workaround for now that ignored token addresses that have gold values since those wouldnt show up here anyway
            if token in contracts.KLAYTN_TOKENS and (token not in contracts.KLAYTN_GOLD_VALUES or contracts.KLAYTN_GOLD_VALUES[token] == 0):
                price = self.getCurrentPrice(token, contracts.JEWEL_ADDRESSES['klaytn'], 'klaytn')
            elif token in contracts.DFKCHAIN_TOKENS and (token not in contracts.DFKCHAIN_GOLD_VALUES or contracts.DFKCHAIN_GOLD_VALUES[token] == 0):
                price = self.getCurrentPrice(token, contracts.JEWEL_ADDRESSES['dfkchain'], 'dfkchain')
            elif token in contracts.HARMONY_TOKENS and (token not in contracts.HARMONY_GOLD_VALUES or contracts.HARMONY_GOLD_VALUES[token] == 0):
                price = self.getCurrentPrice(token, contracts.JEWEL_ADDRESSES['harmony'], 'harmony')
            else:
                price = 0

            if price >= 0:
                db.savePriceData(datetime.datetime.now().strftime('%d-%m-%Y'), token, '{ "usd" : %s }' % price, '{ "usd" : 0.0 }', '{ "usd" : 0.0 }')

        if price >= 0:
            self.today_prices[token] = price
            result = json.loads('{ "usd" : %s }' % price)
        else:
            result = json.loads('{ "usd" : 0.0 }')

        return result

    def getPrice(self, token, date, fiatType='usd'):
        # clear cache when we rollover to next day in update process to save memory
        if date != self.price_cache_date:
            self.price_cache = {}
        if "{0}|{1}".format(token, date) in self.price_cache:
            prices = self.price_cache["{0}|{1}".format(token, date)]
        else:
            row = db.findPriceData(date, token)
            if row != None:
                logging.debug('Found existing price to use in database')
                prices = json.loads(row[2])
            else:
                prices = self.fetchPriceData(token, date)
            self.price_cache["{0}|{1}".format(token, date)] = prices
            self.price_cache_date = date

        if fiatType in prices:
            return prices[fiatType]
        else:
            logging.error('Failed to lookup a price for {0} on {1}: {2}'.format(token, date, prices))
            return -1

    # Return USD price of token based on its pair to throughToken to 1USDC
    def getCurrentPrice(self, token, throughToken, network):
        # use the current gaias tears for lookup because the logs still emit the old address for some reason
        if token == '0x58E63A9bbb2047cd9Ba7E6bB4490C238d271c278':
            token = '0x79fE1fCF16Cc0F7E28b4d7B97387452E3084b6dA'
        ABI = getABI('UniswapV2Router02')
        if network == 'dfkchain':
            w3 = Web3(Web3.HTTPProvider(nets.dfk_web3))
            contract = w3.eth.contract(address='0x3C351E1afdd1b1BC44e931E12D4E05D6125eaeCa', abi=ABI)
            addrUSDC = '0x3AD9DFE640E1A9Cc1D9B0948620820D975c3803a'
            usdcDecimals = 18
        elif network == 'klaytn':
            w3 = Web3(Web3.HTTPProvider(nets.klaytn_web3))
            contract = w3.eth.contract(address='0x9e987E5E9aB872598f601BE4aCC5ac23F484845E', abi=ABI)
            addrUSDC = '0xceE8FAF64bB97a73bb51E115Aa89C17FfA8dD167'
            usdcDecimals = 6
        elif network == 'harmony':
            w3 = Web3(Web3.HTTPProvider(nets.hmy_web3))
            contract = w3.eth.contract(address='0x24ad62502d1C652Cc7684081169D04896aC20f30', abi=ABI)
            addrUSDC = '0x985458E523dB3d53125813eD68c274899e9DfAb4'
            usdcDecimals = 6
        else:
            return -1

        if token in contracts.alternate_pair_through_tokens[network]:
            throughToken = contracts.alternate_pair_through_tokens[network][token]

        tokenDecimals = getTokenInfo(w3, token)[1]
        throughTokenDecimals = getTokenInfo(w3, throughToken)[1]
        # Sometimes 8 decimal tokens will try to get looked up, so skip those
        if tokenDecimals in decimal_units and throughTokenDecimals in decimal_units:
            tokenOne = 1 if tokenDecimals == 0 else Web3.to_wei(1, decimal_units[tokenDecimals])
            throughTokenOne = Web3.to_wei(1, decimal_units[throughTokenDecimals])
        else:
            return -1

        price = -1
        try:
            token0Amount = contract.functions.getAmountsOut(tokenOne, [token, throughToken]).call()
            if throughToken == addrUSDC:
                # If through token is USD, we don't need to get through token to USDC
                price = contracts.valueFromWei(token0Amount[1], throughToken, network)
            else:
                # Use coin gecko price of through token if available
                throughPrice = -1
                if throughToken in token_map:
                    throughPrice = self.priceLookup(datetime.datetime.timestamp(datetime.datetime.now(timezone.utc)), throughToken, network)
                if throughPrice > -1:
                    token1Amount = [1, Web3.to_wei(throughPrice, decimal_units[usdcDecimals])]
                else:
                    token1Amount = contract.functions.getAmountsOut(throughTokenOne, [throughToken, addrUSDC]).call()
                # USD price by multiplying value in through token by through token value in USDC
                price = contracts.valueFromWei(token0Amount[1], throughToken, network) * contracts.valueFromWei(token1Amount[1], addrUSDC, network)
        except Exception as err:
            logging.error('Price lookup failed for {1}: {0}'.format(err, token))

        return price
