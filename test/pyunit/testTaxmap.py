from lib2to3.pgen2.token import AT
import unittest
from datetime import datetime
import decimal
import sys
sys.path.append("../../")
import records
import taxmap
import events


class testTaxmap(unittest.TestCase):
	def setUp(self):
		# Build an events map to use for testing tax mapping methods
		self.em = events.EventsMap()
		self.aTimestamp = datetime.now().timestamp()
		self.yearStart = datetime(datetime.now().year, 1, 1).date()
		self.yearEnd = datetime(datetime.now().year, 12, 31).date()

		rt1 = records.TraderTransaction('0xTEST1', self.aTimestamp, 'one', 'jewel', decimal.Decimal(9003), decimal.Decimal(50.9233))
		rt1.fiatSwapValue = decimal.Decimal(406.67)
		rt1.fiatReceiveValue = decimal.Decimal(406.67)
		self.em['swaps'].append(rt1)

		rt2 = records.TraderTransaction('0xTEST2', self.aTimestamp + 87000, 'jewel', 'USDC', decimal.Decimal(32), decimal.Decimal(210.37345634))
		rt2.fiatSwapValue = decimal.Decimal(210.37345634)
		rt2.fiatReceiveValue = decimal.Decimal(210.37345634)
		self.em['swaps'].append(rt2)

		rw1 = records.walletActivity('0xTEST3', self.aTimestamp + 88000, 'withdraw', '0xPURCHASE', 'jewel', 18)
		rw1.fiatValue = decimal.Decimal(180)
		self.em['wallet'].append(rw1)

		rt1 = records.TavernTransaction('0xTEST1', 'hero', 1, 'purchase', self.aTimestamp, 'jewel', decimal.Decimal(50.5))
		rt1.fiatAmount = decimal.Decimal(487.3456)
		rt1.seller = '0xSOMEONE'
		self.em['tavern'].append(rt1)

		rt2 = records.TavernTransaction('0xTEST2', 'hero', 1, 'sale', self.aTimestamp, 'jewel', decimal.Decimal(44))
		rt2.fiatAmount = decimal.Decimal(403.12)
		rt2.seller = '0xME'
		self.em['tavern'].append(rt2)

	def test_buildSwapRecords(self):
		# act
		taxRecords = taxmap.buildSwapRecords(self.em['swaps'], self.yearStart, self.yearEnd, self.em['wallet'], self.em['airdrops'], self.em['gardens'], self.em['quests'], self.em['tavern'], self.em['lending'], 'fifo', ['0xPURCHASE'])

		#assert
		self.assertTrue(len(taxRecords)==3, "Incorrect number of tax records generated")
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


	def test_buildTavernRecords(self):
		# act
		taxRecords = taxmap.buildTavernRecords(self.em['tavern'], self.yearStart, self.yearEnd)

		# assert
		self.assertEqual(len(taxRecords), 2, "Incorrect number of tax records generated")
		heroPurchase = taxmap.TaxItem('',0,'',0,'','','',None)
		heroSale = taxmap.TaxItem('',0,'',0,'','','',None)
		for tr in taxRecords:
			if tr.txHash == '0xTEST1':
				heroPurchase = tr
			elif tr.txHash == '0xTEST2':
				heroSale = tr
		self.assertIn("Sold hero 1", heroSale.description, "Incorrect description for hero sale")
		self.assertEqual(heroSale.amountNotAccounted, 0, "Cost basis not fully accounted")
		self.assertEqual(heroSale.category, "gains", "Incorrect tax category")
		self.assertEqual(heroSale.term, "short", "Incorrect gains term")
		self.assertEqual(heroSale.acquiredDate, datetime.fromtimestamp(self.aTimestamp).date(), "Acquired date not correctly set")

		self.assertEqual(heroPurchase.category, "expenses", "Hero purchase not in expenses category")


if __name__ == '__main__':
	unittest.main()
