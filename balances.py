#!/usr/bin/env python3
import nets
import logging
import decimal
from web3 import Web3
from datetime import timezone, datetime
import pickle
import prices


COGNIFACT_WALLET = '0x15Ca8d8d7048F694980C717369C55b53e4FbCAEe'
JEWEL_DFKCHAIN = '0xCCb93dABD71c8Dad03Fc4CE5559dC3D89F67a260'
CRYSTAL_DFKCHAIN = '0x04b9dA42306B023f3572e106B11D82aAd9D32EBb'
USDC_DFKCHAIN = '0x3AD9DFE640E1A9Cc1D9B0948620820D975c3803a'

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

    result[JEWEL_DFKCHAIN] = [balanceJewel, jewelValue]
    result[CRYSTAL_DFKCHAIN] = [cbalance, crystalValue]
    result[USDC_DFKCHAIN] = [dbalance, Web3.fromWei(dbalance, 'ether')]

    return result


if __name__ == "__main__":
    logging.basicConfig(filename='balances.log', level=logging.INFO)
    snapTime = datetime.now(timezone.utc)
    result = getBalances(COGNIFACT_WALLET)
    with open('balances.dat', 'wb') as f:
        pickle.dump({ 'updatedAt': snapTime, 'tokens': result }, f)
