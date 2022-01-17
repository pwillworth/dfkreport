# Records objects

# Records for Capital Gains
class TavernTransaction:
    def __init__(self, itemType, itemID, event, timestamp, coinType, coinCost=0, fiatType='usd', fiatAmount=0, seller=''):
        # hero or pet
        self.itemType = itemType
        self.itemID = itemID
        # purchase/sale/hire/summon/crystal
        self.event = event
        self.timestamp = timestamp
        self.coinType = coinType
        self.coinCost = coinCost
        self.fiatType = fiatType
        self.fiatAmount = fiatAmount
        # Wallet address of seller in transaction
        self.seller = seller

class TraderTransaction:
    def __init__(self, timestamp, swapType, receiveType, swapAmount=0, receiveAmount=0, fiatType='usd', fiatSwapValue=0, fiatReceiveValue=0):
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
        # These are tracking fields for tracking amounts that have been allocated for tax records during mapping
        self.swapAmountNotAccounted = swapAmount
        self.receiveAmountNotAccounted = receiveAmount

class LiquidityTransaction:
    def __init__(self, timestamp, action, poolAddress, poolAmount, coin1Type, coin1Amount, coin2Type, coin2Amount, fiatType='usd', coin1FiatValue=0, coin2FiatValue=0):
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
        # Tracking for mapping amounts to tax records
        self.amountNotAccounted = poolAmount

# Records for Income
class GardenerTransaction:
    def __init__(self, timestamp, event, coinType, coinAmount=0, fiatType='usd', fiatValue=0):
        self.timestamp = timestamp
        # deposit, staking-reward, staking-reward-locked
        self.event = event
        self.coinType = coinType
        self.coinAmount = coinAmount
        self.fiatType = fiatType
        self.fiatValue = fiatValue

class BankTransaction:
    def __init__(self, timestamp, action, xRate, coinType, coinAmount=0, fiatType='usd', fiatValue=0):
        self.timestamp = timestamp
        # deposit or withdraw
        self.action = action
        # Bank xJewel/interest multiplier at the time
        self.xRate = xRate
        self.coinType = coinType
        self.coinAmount = coinAmount
        self.fiatType = fiatType
        self.fiatValue = fiatValue
        # Just for tracking amounts that have been allocated to tax records during mapping
        self.amountNotAccounted = coinAmount / xRate

class AirdropTransaction:
    def __init__(self, timestamp, tokenReceived, tokenAmount=0, fiatType='usd', fiatValue=0):
        self.timestamp = timestamp
        self.tokenReceived = tokenReceived
        self.tokenAmount = tokenAmount
        self.fiatType = fiatType
        self.fiatValue = fiatValue

class QuestTransaction:
    def __init__(self, timestamp, rewardType, rewardAmount=0, fiatType='usd', fiatValue=0):
        self.timestamp = timestamp
        # what did we get on the quest, address of it
        self.rewardType = rewardType
        self.rewardAmount = rewardAmount
        self.fiatType = fiatType
        self.fiatValue = fiatValue

class walletActivity:
    def __init__(self, timestamp, action, address, coinType, coinAmount=0, fiatType='usd', fiatValue=0):
        self.timestamp = timestamp
        # deposit or withdraw
        self.action = action
        self.address = address
        self.coinType = coinType
        self.coinAmount = coinAmount
        self.fiatType = fiatType
        self.fiatValue = fiatValue
        # Just for tracking amounts that have been allocated to tax records during mapping
        self.amountNotAccounted = coinAmount

class AlchemistTransaction:
    def __init__(self, timestamp, craftingType, craftingAmount=0, fiatType='usd', fiatValue=0, craftingCosts=0, costsFiatValue=0):
        self.timestamp = timestamp
        # what did we craft with alchemist, address of it
        self.craftingType = craftingType
        # how many were crafted
        self.craftingAmount = craftingAmount
        self.fiatType = fiatType
        self.fiatValue = fiatValue
        # list of ingredients and qty burned
        self.craftingCosts = craftingCosts
        # fiat value of those ingredients at the time
        self.costsFiatValue = costsFiatValue
