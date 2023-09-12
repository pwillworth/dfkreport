#!/usr/bin/env python3
import transactions
import events
import db
import settings
import datetime
import argparse
import uuid
import logging
import logging.handlers
import traceback


def main():
    handler = logging.handlers.RotatingFileHandler('main.log', maxBytes=33554432, backupCount=10)
    logging.basicConfig(handlers=[handler], level=logging.INFO, format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    parser = argparse.ArgumentParser()
    parser.add_argument("wallet", help="The evm compatible wallet address to generate for")
    parser.add_argument("--network", choices=['harmony','avalanche','dfkchain','klaytn'], help="network to get tx for")
    args = parser.parse_args()

    page_size = settings.TX_PAGE_SIZE
    txResult = []
    txData = []

    logging.info('new update request {0} {1}'.format(args.wallet, args.network))
    # Scale up default page size for very large accounts
    txCount = transactions.getTransactionCount(args.wallet, args.network)
    if txCount > page_size*50:
        page_size = min(1000, page_size*5)

    txData = transactions.getTransactionList(args.wallet, args.network, page_size)

    db.completeTransactions(args.wallet, args.network)

    # With transaction list, we now generate the events and tax map
    txSaved = events.checkTransactions(txData, args.wallet, args.network)

    db.completeWalletUpdate(args.wallet, args.network)


if __name__ == "__main__":
	main()
