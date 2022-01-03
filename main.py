#!/usr/bin/env python3
import transactions
import taxmap
import db
import datetime
import argparse
import uuid
import pickle
import logging
import traceback

def main():
    logging.basicConfig(filename='../main.log', level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logging.info('We got a report request')
    parser = argparse.ArgumentParser()
    parser.add_argument("wallet", help="The evm compatible wallet address to generate for")
    parser.add_argument("startDate", help="The starting date for the report")
    parser.add_argument("endDate", help="The ending date for the report")
    parser.add_argument("--costbasis", choices=['fifo','lifo','hifo'], help="Method for mapping cost basis to gains")
    args = parser.parse_args()
    if args.costbasis == None:
        costBasis = 'fifo'
    else:
        costBasis = args.costbasis

    txData = []

    # list of transactions if loaded from file if available, otherwise fetched
    reportInfo = db.findReport(args.wallet, args.startDate, args.endDate)
    if reportInfo != None and reportInfo[5] > 0:
        with open('../transactions/{0}'.format(reportInfo[8]), 'rb') as file:
            txData = pickle.load(file)
    else:
        # generate.py pre-generates report record, but if running outside of that, create one
        if reportInfo == None:
            generateTime = datetime.datetime.now()
            result = transactions.getTransactionCount(args.wallet)
            db.createReport(args.wallet, args.startDate, args.endDate, int(datetime.datetime.timestamp(generateTime)), result, costBasis)

        logging.info('Loading transactions list for {0}'.format(args.wallet))
        txData = transactions.getTransactionList(args.wallet, args.startDate, args.endDate)
        # The transactions are written to a file and record updated indicate fetching complete
        transactionsFile = uuid.uuid4().hex
        with open('../transactions/{0}'.format(transactionsFile), 'wb') as f:
            pickle.dump(txData, f)
        db.completeTransactions(args.wallet, args.startDate, args.endDate, transactionsFile)

    # With transaction list, we now generate the events and tax map
    logging.info('We are gonna get started now')
    try:
        reportData = taxmap.buildTaxMap(txData, args.wallet, datetime.datetime.strptime(args.startDate, '%Y-%m-%d').date(), datetime.datetime.strptime(args.endDate, '%Y-%m-%d').date(), costBasis)
    except Exception as err:
        logging.error('Unexpected Error {0} building tax map, setting report to failure.'.format(err))
        traceback.print_exc()
        db.updateReportError(args.wallet, args.startDate, args.endDate)
        return 1

    for item in reportData['taxes']:
        logging.debug(str(item.__dict__) + '\n')

    # The results are written to a file and record updated to notify completion
    reportFile = uuid.uuid4().hex
    with open('../reports/{0}'.format(reportFile), 'wb') as f:
        pickle.dump(reportData, f)
    db.completeReport(args.wallet, args.startDate, args.endDate, reportFile)

if __name__ == "__main__":
	main()
