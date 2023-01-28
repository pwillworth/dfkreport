#!/usr/bin/env python3
import nets
import logging
import decimal
import os
from web3 import Web3
from datetime import timezone, datetime
import pickle
import prices


COGNIFACT_WALLET = '0x15Ca8d8d7048F694980C717369C55b53e4FbCAEe'
JEWEL_DFKCHAIN = '0xCCb93dABD71c8Dad03Fc4CE5559dC3D89F67a260'
CRYSTAL_DFKCHAIN = '0x04b9dA42306B023f3572e106B11D82aAd9D32EBb'
USDC_DFKCHAIN = '0x3AD9DFE640E1A9Cc1D9B0948620820D975c3803a'
KLAY_KLAYTN = '0x19Aac5f612f524B754CA7e7c41cbFa2E981A4432'
JEWEL_KLAYTN = '0x30C103f8f5A3A732DFe2dCE1Cc9446f545527b43'
JADE_KLAYTN = '0xB3F5867E277798b50ba7A71C0b24FDcA03045eDF'

def readCurrent():
    # check right spot so file can be accessed relatively regardles of execution source
    location = os.path.abspath(__file__)
    try:
        with open('{0}/balances.dat'.format('/'.join(location.split('/')[0:-1])), 'rb') as file:
            results = pickle.load(file)
    except Exception as err:
        logging.error('Balances lookup failure!: {0}'.format(str(err)))
    balance = 0
    if 'tokens' in results:
        for k, v in results['tokens'].items():
            balance += decimal.Decimal(v[1])
    if 'updatedAt' in results:
        updatedAt = results['updatedAt']
    return balance

# Return array of transactions on DFK Chain for the address
def getBalances(wallet):
    result = {}
    # Connect to w3
    w3d = Web3(Web3.HTTPProvider(nets.dfk_web3))
    if not w3d.isConnected():
        logging.critical('Error: Critical w3 connection failure for '.format(nets.dfk_web3))
        return 'Error: Blockchain connection failure.'

    with open('abi/ERC20.json', 'r') as f:
        ABI = f.read()

    jewelValue = 0.0
    crystalValue = 0.0
    # Get balances on DFKChain
    balanceJewel = w3d.eth.get_balance(wallet)
    if balanceJewel > 1:
        logging.info('Found Jewel balance for {0}: {1}'.format(wallet, Web3.fromWei(balanceJewel, 'ether')))
        jewelPrice = prices.priceLookup(datetime.now().timestamp(), JEWEL_DFKCHAIN, 'dfkchain')
        if jewelPrice > -1:
            logging.info(jewelPrice)
            jewelValue = Web3.fromWei(balanceJewel, 'ether') * decimal.Decimal(jewelPrice)
    ccontract = w3d.eth.contract(address=CRYSTAL_DFKCHAIN, abi=ABI)
    cbalance = ccontract.functions.balanceOf(wallet).call()
    if cbalance > 0:
        logging.info('Found Crystal balance for {0}: {1}'.format(wallet, Web3.fromWei(cbalance, 'ether')))
        crystalPrice = prices.priceLookup(datetime.now().timestamp(), CRYSTAL_DFKCHAIN, 'dfkchain')
        if crystalPrice > -1:
            crystalValue = Web3.fromWei(cbalance, 'ether') * decimal.Decimal(crystalPrice)
    dcontract = w3d.eth.contract(address=USDC_DFKCHAIN, abi=ABI)
    dbalance = dcontract.functions.balanceOf(wallet).call()
    if dbalance > 0:
        logging.info('Found USDC balance for {0}: {1}'.format(wallet, Web3.fromWei(dbalance, 'ether')))

    # Connect to w3
    w3k = Web3(Web3.HTTPProvider(nets.klaytn_web3))
    if not w3k.isConnected():
        logging.critical('Error: Critical w3 connection failure for '.format(nets.klaytn_web3))
        return 'Error: Blockchain connection failure.'
    # Get balances on Klaytn
    balanceKlay = w3k.eth.get_balance(wallet)
    if balanceKlay > 1:
        logging.info('Found Klay balance for {0}: {1}'.format(wallet, Web3.fromWei(balanceKlay, 'ether')))
        klayPrice = prices.priceLookup(datetime.now().timestamp(), KLAY_KLAYTN, 'klaytn')
        if klayPrice > -1:
            klayValue = Web3.fromWei(balanceKlay, 'ether') * decimal.Decimal(klayPrice)
    jcontract = w3k.eth.contract(address=JEWEL_KLAYTN, abi=ABI)
    jbalance = jcontract.functions.balanceOf(wallet).call()
    if jbalance > 0:
        logging.info('Found Jewel balance for {0}: {1}'.format(wallet, Web3.fromWei(jbalance, 'ether')))
        jewelPrice = prices.priceLookup(datetime.now().timestamp(), JEWEL_KLAYTN, 'klaytn')
        if jewelPrice > -1:
            jewelValueK = Web3.fromWei(jbalance, 'ether') * decimal.Decimal(jewelPrice)
    bcontract = w3k.eth.contract(address=JADE_KLAYTN, abi=ABI)
    bbalance = bcontract.functions.balanceOf(wallet).call()
    if bbalance > 0:
        logging.info('Found Jade balance for {0}: {1}'.format(wallet, Web3.fromWei(bbalance, 'ether')))
        jadePrice = prices.priceLookup(datetime.now().timestamp(), JADE_KLAYTN, 'klaytn')
        if jadePrice > -1:
            jadeValue = Web3.fromWei(bbalance, 'ether') * decimal.Decimal(jadePrice)

    result[JEWEL_DFKCHAIN] = [balanceJewel, jewelValue]
    result[CRYSTAL_DFKCHAIN] = [cbalance, crystalValue]
    result[USDC_DFKCHAIN] = [dbalance, Web3.fromWei(dbalance, 'ether')]
    result[KLAY_KLAYTN] = [balanceKlay, klayValue]
    result[JEWEL_KLAYTN] = [jbalance, jewelValueK]
    result[JADE_KLAYTN] = [bbalance, jadeValue]

    return result

def updateBalances():
    snapTime = datetime.now(timezone.utc)
    result = getBalances(COGNIFACT_WALLET)
    with open('balances.dat', 'wb') as f:
        pickle.dump({ 'updatedAt': snapTime, 'tokens': result }, f)

if __name__ == "__main__":
    logging.basicConfig(filename='balances.log', level=logging.INFO)
    updateBalances()
