#!/usr/bin/env python3
import transactions
import taxmap
import db
import settings
import datetime
import argparse
import uuid
import pickle
import jsonpickle
import logging
import logging.handlers
import traceback


def main():
    handler = logging.handlers.RotatingFileHandler('../main.log', maxBytes=33554432, backupCount=10)
    logging.basicConfig(handlers=[handler], level=logging.INFO, format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logging.info('We got a report request')
    parser = argparse.ArgumentParser()
    parser.add_argument("wallet", help="The evm compatible wallet address to generate for")
    parser.add_argument("startDate", help="The starting date for the report")
    parser.add_argument("endDate", help="The ending date for the report")
    parser.add_argument("--costbasis", choices=['fifo','lifo','hifo','acb'], help="Method for mapping cost basis to gains")
    parser.add_argument("--chains", choices=['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15'], help="Bitwise integer of blockchains to include 1=Harmony,2=Avax,4=DFKChain,8=Klaytn")
    parser.add_argument("--wallets", help="SHA1 hash of wallet address list for multi wallet report")
    args = parser.parse_args()
    if args.costbasis == None:
        costBasis = 'fifo'
    else:
        costBasis = args.costbasis
    if args.chains == None:
        includedChains = '15'
    else:
        includedChains = args.chains

    page_size = settings.TX_PAGE_SIZE
    txResult = []
    txData = []
    wallets = [args.wallet]
    if args.wallets == None:
        walletHash = db.getWalletHash(wallets)
    else:
        walletHash = args.wallets
    moreOptions = db.ReportOptions()

    # list of transactions if loaded from file if available, otherwise fetched
    reportInfo = db.findReport(args.wallet, args.startDate, args.endDate, walletHash)
    if reportInfo != None and reportInfo[5] > 0 and len(reportInfo[8]) > 0:
        logging.info('found old report with tx data, reusing for new one')
        includedChains = reportInfo[12]
        wallets = reportInfo[15]
        with open('../transactions/{0}'.format(reportInfo[8]), 'rb') as file:
            txData = pickle.load(file)
    else:
        # generate.py pre-generates report record, but if running outside of that, create one
        if reportInfo == None:
            generateTime = datetime.datetime.now()
            txResult = transactions.getTransactionCount(args.wallet, includedChains)
            if type(txResult) is not dict:
                logging.error('Unexpected Error {0} fetching transaction count, setting report to failure.'.format(err))
                db.updateReportError(args.wallet, args.startDate, args.endDate, walletHash, 8)
                return 1
            txTotal = transactions.getTotalCount(txResult)
            db.createReport(args.wallet, args.startDate, args.endDate, int(datetime.datetime.timestamp(generateTime)), txTotal, costBasis, includedChains, [args.wallet], 'system', walletHash, 1, None, jsonpickle.encode(txResult))
        else:
            includedChains = reportInfo[12]
            wallets = jsonpickle.decode(reportInfo[15])
            txResult = jsonpickle.decode(reportInfo[14])
            if type(txResult) is not dict:
                logging.error('Unexpected Error {0} fetching transaction count, setting report to failure.'.format(str(txResult)))
                db.updateReportError(args.wallet, args.startDate, args.endDate, walletHash, 8)
                return 1
            try:
                moreOptions = jsonpickle.loads(reportInfo[13])
            except Exception as err:
                logging.warning('Ignoring failure to load more options, probably old ui not setting it.')

        logging.info('Loading transactions list for {0}'.format(args.wallet))
        # Scale up default page size for very large accounts
        if reportInfo != None and reportInfo[4] > page_size*50:
            page_size = min(1000, page_size*5)
        try:
            txData = transactions.getTransactionList(args.wallet, wallets, args.startDate, args.endDate, txResult, page_size, includedChains)
        except Exception as err:
            logging.error('Unexpected Error {0} fetching transaction list, setting report to failure.'.format(err))
            traceback.print_exc()
            db.updateReportError(args.wallet, args.startDate, args.endDate, walletHash, 8)
            return 1
        # The transactions are written to a file and record updated indicate fetching complete
        transactionsFile = uuid.uuid4().hex
        with open('../transactions/{0}'.format(transactionsFile), 'wb') as f:
            pickle.dump(txData, f)
        try:
            db.completeTransactions(args.wallet, args.startDate, args.endDate, walletHash, transactionsFile)
        except Exception as err:
            logging.error('DB report update tx complete failure: {0}'.format(str(err)))

    # With transaction list, we now generate the events and tax map
    try:
        reportData = taxmap.buildTaxMap(txData, txResult, wallets, datetime.datetime.strptime(args.startDate, '%Y-%m-%d').date(), datetime.datetime.strptime(args.endDate, '%Y-%m-%d').date(), costBasis, includedChains, moreOptions)
    except Exception as err:
        logging.error('Unexpected Error {0} building tax map, setting report to failure.'.format(err))
        traceback.print_exc()
        # Set a different code when web3.exceptions.TransactionNotFound
        # so we can relay that it is about network rpc issue, try later
        if str(err) == "{'message': 'Relay attempts exhausted', 'code': -32050}":
            statusCode = 8
        elif "Bad Gateway for url" in str(err) or "Service Unavailable" in str(err) or "Max retries exceeded" in str(err):
            statusCode = 8
        else:
            statusCode = 9
        try:
            db.updateReportError(args.wallet, args.startDate, args.endDate, walletHash, statusCode)
        except Exception as err:
            logging.error('DB report update error failure: {0}'.format(str(err)))
        return 1

    for item in reportData['taxes']:
        logging.debug(str(item.__dict__) + '\n')

    # The results are written to a file and record updated to notify completion
    reportFile = uuid.uuid4().hex
    with open('../reports/{0}'.format(reportFile), 'wb') as f:
        pickle.dump(reportData, f)
    try:
        db.completeReport(args.wallet, args.startDate, args.endDate, walletHash, reportFile)
    except Exception as err:
        logging.error('DB report update complete failure: {0}'.format(str(err)))

if __name__ == "__main__":
	main()
