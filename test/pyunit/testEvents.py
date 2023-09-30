import unittest
from unittest.mock import patch
import sys
from decimal import Decimal
import pickle
from web3 import Web3
sys.path.append("../../")
import records
import events
import prices
import nets
import base64


class testEvents(unittest.TestCase):
	def setUp(self):
		# appears we need a connection to process receipt, maybe TODO find a different way so this can be true unit test
		self.w3 = Web3(Web3.HTTPProvider(nets.hmy_web3))
		self.subject = base64.b85decode(b'FnBOVL^3xyVl*~0W@a{KL1s8PHbY@IH8WvkVl`o8GBPtVMP)fbK}G').decode('utf-8')
	
	@patch("prices.priceLookup")
	def test_extractSwapResults(self, mockMethod):
		# arrange
		pd = prices.PriceData()
		# load receipt for swap 5000 DFKGOLD for Jewel tx
		with open('swapReceipts/0x2e347d595069f2f1b08f3048d03b4570519265bda0a82479f0f5e73e7aa39c9a', 'rb') as rf:
			sr = pickle.load(rf)

		mockMethod.return_value = Decimal(0.01)

		# act
		result = events.extractSwapResults(self.w3, '0x2e347d595069f2f1b08f3048d03b4570519265bda0a82479f0f5e73e7aa39c9a', self.subject, '0x9014B937069918bd319f80e8B3BB4A2cf6FAA5F7', 1645305183, sr, 0, 'harmony', pd)

		# assert
		self.assertTrue(type(result) is records.TraderTransaction, "Wrong object type returned for swap")
		self.assertEqual(result.swapType, "0x3a4EDcf3312f44EF027acfd8c21382a5259936e7")
		self.assertEqual(result.receiveType, "0x72Cb10C6bfA5624dD07Ef608027E366bd690048F")
		self.assertEqual(int(result.fiatSwapValue), 50)


if __name__ == '__main__':
	unittest.main()

