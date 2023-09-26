#!/usr/bin/env python3
import transactions
import events
import db
import settings
import argparse
import logging
import logging.handlers


def main():
    handler = logging.handlers.RotatingFileHandler('main.log', maxBytes=33554432, backupCount=10)
    logging.basicConfig(handlers=[handler], level=logging.INFO, format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    parser = argparse.ArgumentParser()
    parser.add_argument("wallet", help="The evm compatible wallet address to generate for")
    parser.add_argument("--network", choices=['harmony','avalanche','dfkchain','klaytn'], help="network to get tx for")
    args = parser.parse_args()

    page_size = settings.TX_PAGE_SIZE
    txData = []

    logging.info('new update request {0} {1}'.format(args.wallet, args.network))

    txCount = transactions.getTransactionCount(args.wallet, args.network)
    if type(txCount) is not str:
        db.updateWalletStatus(args.wallet, args.network, 'initiated', txCount)
        # Scale up default page size for very large accounts
        if txCount > page_size*50:
            page_size = min(1000, page_size*5)
    else:
        db.updateReportError(args.wallet, args.network)

    # Get list of transactions that need to be parsed
    try:
        txData = transactions.getTransactionList(args.wallet, args.network, page_size)
    except Exception as err:
        logging.error('Wallet update failure during tx listing: {0}'.format(err))
        db.updateReportError(args.wallet, args.network)

    db.completeTransactions(args.wallet, args.network)

    # With transaction list, we now generate and store event data
    try:
        txSaved = events.checkTransactions(txData, args.wallet, args.network, txCount)
    except Exception as err:
        logging.error('Wallet update failure during event parsing: {0}'.format(err))
        db.updateReportError(args.wallet, args.network)

    db.completeWalletUpdate(args.wallet, args.network, txSaved)


if __name__ == "__main__":
	main()
