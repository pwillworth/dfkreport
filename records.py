# Records objects

# Records for Capital Gains
class TavernTransaction:
    def __init__(self, txHash, itemType, itemID, event, timestamp, coinType, coinCost=0, fiatType='usd', fiatAmount=0, seller='', fiatFeeValue=0):
        self.txHash = txHash
        # hero or pet or land
        self.itemType = itemType
        self.itemID = itemID
        # purchase/sale/hire/summon/crystal/perished
        self.event = event
        self.timestamp = timestamp
        self.coinType = coinType
        self.coinCost = coinCost
        self.fiatType = fiatType
        self.fiatAmount = fiatAmount
        self.fiatFeeValue = fiatFeeValue
        # Wallet address of seller in transaction
        self.seller = seller

class TraderTransaction:
    def __init__(self, txHash, timestamp, swapType, receiveType, swapAmount=0, receiveAmount=0, fiatType='usd', fiatSwapValue=0, fiatReceiveValue=0, fiatFeeValue=0):
        self.txHash = txHash
        # timestamp of block when this transaction was done
        self.timestamp = timestamp
        # token type that was traded away
        self.swapType = swapType
        self.swapAmount = swapAmount
        # token type that was received
        self.receiveType = receiveType
        self.receiveAmount = receiveAmount
        # fiat equivalents of token values at the time
        self.fiatType = fiatType
        self.fiatSwapValue = fiatSwapValue
        self.fiatReceiveValue = fiatReceiveValue
        self.fiatFeeValue = fiatFeeValue
        # These are tracking fields for tracking amounts that have been allocated for tax records during mapping
        self.swapAmountNotAccounted = swapAmount
        self.receiveAmountNotAccounted = receiveAmount

class LiquidityTransaction:
    def __init__(self, txHash, timestamp, action, poolAddress, poolAmount, coin1Type, coin1Amount, coin2Type, coin2Amount, fiatType='usd', coin1FiatValue=0, coin2FiatValue=0, fiatFeeValue=0):
        self.txHash = txHash
        # timestamp of block when transaction was done
        self.timestamp = timestamp
        # deposit tokens or withdraw (LP tokens)
        self.action = action
        # which liquidity pool
        self.poolAddress = poolAddress
        # number of LP tokens
        self.poolAmount = poolAmount
        # coin 1 should be the native token (jewel/crystal)
        self.coin1Type = coin1Type
        self.coin1Amount = coin1Amount
        self.coin2Type = coin2Type
        self.coin2Amount = coin2Amount
        self.fiatType = fiatType
        self.coin1FiatValue = coin1FiatValue
        self.coin2FiatValue = coin2FiatValue
        self.fiatFeeValue = fiatFeeValue
        # Tracking for mapping amounts to tax records
        self.amountNotAccounted = poolAmount

# Records for Income
class GardenerTransaction:
    def __init__(self, txHash, timestamp, event, coinType, coinAmount=0, fiatType='usd', fiatValue=0, fiatFeeValue=0):
        self.txHash = txHash
        self.timestamp = timestamp
        # deposit, withdraw, staking-reward, staking-reward-locked
        self.event = event
        self.coinType = coinType
        self.coinAmount = coinAmount
        self.fiatType = fiatType
        self.fiatValue = fiatValue
        self.fiatFeeValue = fiatFeeValue
        self.amountNotAccounted = coinAmount

class BankTransaction:
    def __init__(self, txHash, timestamp, action, xRate, coinType, coinAmount=0, fiatType='usd', fiatValue=0, fiatFeeValue=0):
        self.txHash = txHash
        self.timestamp = timestamp
        # deposit or withdraw
        self.action = action
        # Bank xJewel/interest multiplier at the time
        self.xRate = xRate
        self.coinType = coinType
        self.coinAmount = coinAmount
        self.fiatType = fiatType
        self.fiatValue = fiatValue
        self.fiatFeeValue = fiatFeeValue
        # Just for tracking amounts that have been allocated to tax records during mapping
        self.amountNotAccounted = coinAmount / xRate

class AirdropTransaction:
    def __init__(self, txHash, timestamp, address, tokenReceived, tokenAmount=0, fiatType='usd', fiatValue=0, fiatFeeValue=0):
        self.txHash = txHash
        self.timestamp = timestamp
        self.address = address
        self.tokenReceived = tokenReceived
        self.tokenAmount = tokenAmount
        self.fiatType = fiatType
        self.fiatValue = fiatValue
        self.fiatFeeValue = fiatFeeValue
        # Just for tracking amounts that have been allocated to tax records during mapping
        self.amountNotAccounted = tokenAmount

class QuestTransaction:
    def __init__(self, txHash, timestamp, rewardType, rewardAmount=0, fiatType='usd', fiatValue=0, fiatFeeValue=0):
        self.txHash = txHash
        self.timestamp = timestamp
        # what did we get on the quest, address of it
        self.rewardType = rewardType
        self.rewardAmount = rewardAmount
        self.fiatType = fiatType
        self.fiatValue = fiatValue
        self.fiatFeeValue = fiatFeeValue
        self.amountNotAccounted = rewardAmount

class walletActivity:
    def __init__(self, txHash, timestamp, action, address, coinType, coinAmount=0, fiatType='usd', fiatValue=0, fiatFeeValue=0):
        self.txHash = txHash
        self.timestamp = timestamp
        # deposit/payment/withdraw/bridge/donation
        self.action = action
        self.address = address
        self.coinType = coinType
        self.coinAmount = coinAmount
        self.fiatType = fiatType
        self.fiatValue = fiatValue
        self.fiatFeeValue = fiatFeeValue
        # Just for tracking amounts that have been allocated to tax records during mapping
        self.amountNotAccounted = coinAmount

class AlchemistTransaction:
    def __init__(self, txHash, timestamp, craftingType, craftingAmount=0, fiatType='usd', fiatValue=0, craftingCosts=0, costsFiatValue=0, fiatFeeValue=0):
        self.txHash = txHash
        self.timestamp = timestamp
        # what did we craft with alchemist, address of it
        self.craftingType = craftingType
        # how many were crafted
        self.craftingAmount = craftingAmount
        self.fiatType = fiatType
        self.fiatValue = fiatValue
        self.fiatFeeValue = fiatFeeValue
        # list of ingredients and qty burned
        self.craftingCosts = craftingCosts
        # fiat value of those ingredients at the time
        self.costsFiatValue = costsFiatValue

class LendingTransaction:
    def __init__(self, txHash, timestamp, event, address, coinType, coinAmount=0, fiatType='usd', fiatValue=0, fiatFeeValue=0):
        self.txHash = txHash
        self.timestamp = timestamp
        # lend/redeem/borrow/repay/liquidate
        self.event = event
        self.address = address
        self.coinType = coinType
        self.coinAmount = coinAmount
        self.fiatType = fiatType
        self.fiatValue = fiatValue
        self.fiatFeeValue = fiatFeeValue
        self.amountNotAccounted = coinAmount
