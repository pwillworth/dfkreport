from lib2to3.pgen2.token import AT
import unittest
from datetime import datetime
import decimal
import sys
sys.path.append("../../")
import records
import events
sys.path.append("../../web/")
import taxmap


class testTaxmap(unittest.TestCase):
	def setUp(self):
		self.aTimestamp = datetime.now().timestamp()
		self.yearStart = datetime(datetime.now().year, 1, 1).date()
		self.yearEnd = datetime(datetime.now().year, 12, 31).date()
		# Build an events map to use for testing tax mapping methods
		self.fifoMap = self.getEventMap()
		# make another copy of the event map for acb since build tax map manipulates the accounting
		self.acbMap = self.getEventMap()

	def getEventMap(self):
		# Build an events map to use for testing tax mapping methods
		em = records.EventsMap()
		self.aTimestamp = datetime.now().timestamp()
		self.yearStart = datetime(datetime.now().year, 1, 1).date()
		self.yearEnd = datetime(datetime.now().year, 12, 31).date()

		rw0 = records.walletActivity('0xITEST0', 'harmony', self.aTimestamp - 100, 'deposit', '0xCEXWALLET', 'one', 18020)
		rw0.fiatValue = decimal.Decimal(180)
		em['wallet'].append(rw0)

		rt0 = records.TraderTransaction('0xTEST0', 'harmony', self.aTimestamp - 50, 'one', 'jewel', decimal.Decimal(9000), decimal.Decimal(98.66))
		rt0.fiatSwapValue = decimal.Decimal(701.10)
		rt0.fiatReceiveValue = decimal.Decimal(701.10)
		em['swaps'].append(rt0)

		rt1 = records.TraderTransaction('0xTEST1', 'harmony', self.aTimestamp, 'one', 'jewel', decimal.Decimal(9003), decimal.Decimal(50.9233))
		rt1.fiatSwapValue = decimal.Decimal(406.67)
		rt1.fiatReceiveValue = decimal.Decimal(406.67)
		em['swaps'].append(rt1)

		rt2 = records.TraderTransaction('0xTEST2', 'harmony', self.aTimestamp + 87000, 'jewel', 'USDC', decimal.Decimal(140.2), decimal.Decimal(1210.37345634))
		rt2.fiatSwapValue = decimal.Decimal(1210.37345634)
		rt2.fiatReceiveValue = decimal.Decimal(1210.37345634)
		em['swaps'].append(rt2)

		rw1 = records.walletActivity('0xTEST3', 'harmony', self.aTimestamp + 88000, 'withdraw', '0xPURCHASE', 'jewel', 18)
		rw1.fiatValue = decimal.Decimal(180)
		em['wallet'].append(rw1)

		rt1 = records.TavernTransaction('0xHTEST1', 'harmony', 'hero', 1, 'purchase', self.aTimestamp, 'jewel', decimal.Decimal(50.5))
		rt1.fiatAmount = decimal.Decimal(487.3456)
		rt1.seller = '0xSOMEONE'
		em['tavern'].append(rt1)

		rt2 = records.TavernTransaction('0xHTEST2', 'harmony', 'hero', 1, 'sale', self.aTimestamp, 'jewel', decimal.Decimal(44))
		rt2.fiatAmount = decimal.Decimal(403.12)
		rt2.seller = '0xME'
		em['tavern'].append(rt2)

		return em

	def test_buildSwapRecords(self):
		# act
		taxRecords = taxmap.buildSwapRecords(self.fifoMap['swaps'], self.yearStart, self.yearEnd, self.fifoMap['wallet'], self.fifoMap['airdrops'], self.fifoMap['gardens'], self.fifoMap['quests'], self.fifoMap['tavern'], self.fifoMap['lending'], 'fifo', ['0xPURCHASE'])
		acbTaxRecords = taxmap.buildSwapRecords(self.acbMap['swaps'], self.yearStart, self.yearEnd, self.acbMap['wallet'], self.acbMap['airdrops'], self.acbMap['gardens'], self.acbMap['quests'], self.acbMap['tavern'], self.acbMap['lending'], 'acb', ['0xPURCHASE'])

		#assert
		self.assertTrue(len(taxRecords)==5, "Incorrect number of tax records generated")
		oneSwap = taxmap.TaxItem('',0,'',0,'','','',None)
		jewelSwap = taxmap.TaxItem('',0,'',0,'','','',None)
		jewelPurchase = taxmap.TaxItem('',0,'',0,'','','',None)
		for tr in taxRecords:
			if tr.txHash == '0xTEST1':
				oneSwap = tr
			elif tr.txHash == '0xTEST2':
				jewelSwap = tr
			elif tr.txHash == '0xTEST3':
				jewelPurchase = tr
		self.assertIn("Sold 9003", oneSwap.description, "Incorrect description for swap record.")
		self.assertEqual(jewelSwap.amountNotAccounted, 0, "Cost basis not fully accounted")
		self.assertEqual(jewelSwap.category, "gains", "Incorrect tax category")
		self.assertEqual(jewelSwap.term, "short", "Incorrect gains term")
		self.assertEqual(jewelSwap.acquiredDate, datetime.fromtimestamp(self.aTimestamp).date(), "Acquired date not correctly set")
		# validate purchase address list function
		self.assertEqual(jewelPurchase.category, "gains", "Incorrect tax category")
		self.assertEqual(jewelPurchase.acquiredDate, datetime.fromtimestamp(self.aTimestamp).date(), "Acquired date not correctly set")
		self.assertIn("Paid for", jewelPurchase.description, "Incorrect description for purchase record.")
		# validate adjusted cost basis
		for tr in acbTaxRecords:
			if tr.txHash == '0xTEST2':
				jewelSwap = tr

		self.assertEqual('{0:.2f}'.format(jewelSwap.costs), '1038.28', "Incorrect Adjust Cost Basis detected.")


	def test_buildTavernRecords(self):
		# act
		taxRecords = taxmap.buildTavernRecords(self.fifoMap['tavern'], self.yearStart, self.yearEnd)

		# assert
		self.assertEqual(len(taxRecords), 1, "Incorrect number of tax records generated")
		heroSale = taxmap.TaxItem('',0,'',0,'','','',None)
		for tr in taxRecords:
			if tr.txHash == '0xHTEST2':
				heroSale = tr
		self.assertIn("Sold hero 1", heroSale.description, "Incorrect description for hero sale")
		self.assertEqual(heroSale.amountNotAccounted, 0, "Cost basis not fully accounted")
		self.assertEqual(heroSale.category, "gains", "Incorrect tax category")
		self.assertEqual(heroSale.term, "short", "Incorrect gains term")
		self.assertEqual(heroSale.acquiredDate, datetime.fromtimestamp(self.aTimestamp).date(), "Acquired date not correctly set")


if __name__ == '__main__':
	unittest.main()
