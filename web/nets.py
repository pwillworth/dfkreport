#!/usr/bin/env python3
HARMONY=1
AVALANCHE=2
DFKCHAIN=4
KLAYTN=8
hmy_main = 'https://api.harmony.one'
avax_main = 'https://api.snowtrace.io'
avax_key = ''

hmy_web3 = 'https://api.harmony.one'
avax_web3 = 'https://api.avax.network/ext/bc/C/rpc'

dfk_main = 'https://subnet-explorer-api.avax.network/v1.1/53935'
dfk_web3 = 'https://subnets.avax.network/defi-kingdoms/dfk-chain/rpc'

klaytn_web3 = 'https://klaytn.rpc.defikingdoms.com'
klaytn_public_web3 = 'https://public-node-api.klaytnapi.com/v1/cypress'

covalent = 'https://api.covalenthq.com/v1'
bitquery = 'https://graphql.bitquery.io'
glacier = 'https://glacier-api.avax.network/v1'

def getNetworkList(includedChains):
    networks = ()
    if includedChains & HARMONY > 0:
        networks = networks + ('harmony',)
    if includedChains & DFKCHAIN > 0:
        networks = networks + ('dfkchain',)
    if includedChains & KLAYTN > 0:
        networks = networks + ('klaytn',)
    if includedChains & AVALANCHE > 0:
        networks = networks + ('avalanche',)
    return networks
