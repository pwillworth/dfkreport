#!/usr/bin/env python3
import pymysql
import dfkInfo
import logging
import records
import settings
import jsonpickle
import datetime
import os

def ReportOptions():
    return {
        'purchaseAddresses': []
    }

def aConn():
	conn = pymysql.connect(host = dfkInfo.DB_HOST,
	db= dfkInfo.DB_NAME,
	user = dfkInfo.DB_USER,
	passwd = dfkInfo.DB_PASS)
	conn.autocommit(True)
	return conn

def findPriceData(date, token):
    try:
        con = aConn()
        cur = con.cursor()
        cur.execute("SELECT * FROM prices WHERE date=%s AND token=%s", (date, token))
        row = cur.fetchone()
        con.close()
    except Exception as err:
        logging.error('DB failure looking up prices {0}'.format(str(err)))
        row = None

    return row

def savePriceData(date, token, price, liquid, volume):
    try:
        con = aConn()
        cur = con.cursor()
        cur.execute("INSERT INTO prices VALUES (%s, %s, %s, %s, %s)", (date, token, price, liquid, volume))
        con.commit()
        con.close()
    except Exception as err:
        # incase DB is down, it's ok we just wont cache
        logging.error('db error saving price data {0}'.format(str(err)))

def findTransaction(txHash, account):
    try:
        con = aConn()
        cur = con.cursor()
        cur.execute("SELECT * FROM transactions WHERE txHash=%s AND account=%s", (txHash, account))
        row = cur.fetchone()
        con.close()
    except Exception as err:
        # if db is unavailable we can just continue
        logging.error('Error finding tx {0}'.format(str(err)))
        row = None

    return row

def saveTransaction(tx, timestamp, type, events, wallet, network, gasUsed, gasValue):
    try:
        con = aConn()
        cur = con.cursor()
    except Exception as err:
        logging.error('Failed to save tx {0}'.format(str(err)))
        con = None
    if con != None and con.open:
        try:
            cur.execute("INSERT INTO transactions VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (tx, timestamp, type, events, wallet, network, gasUsed, gasValue))
            con.commit()
        except Exception as err:
            logging.error('Unexpected Error {0} caching transaction {1} - '.format(err, tx))
        con.close()
    else:
        logging.info('Skipping tx save due to previous db failure.')

# Look up and return any transaction events where wallet was the seller
def getTavernSales(wallet, startDate, endDate):
    sales = []
    startStamp = int(datetime.datetime(startDate.year, startDate.month, startDate.day).timestamp())
    endStamp = int(datetime.datetime(endDate.year, endDate.month, endDate.day).timestamp() + 86400)
    try:
        con = aConn()
        cur = con.cursor()
    except Exception as err:
        logging.error('DB error trying to look up tavern sales. {0}'.format(str(err)))
    if con != None and con.open:
        cur.execute("SELECT * FROM transactions WHERE account=%s and eventType='tavern' and blockTimestamp>=%s and blockTimestamp<%s", (wallet, startStamp, endStamp))
        row = cur.fetchone()
        while row != None:
            r = jsonpickle.decode(row[3])
            if type(r) is records.TavernTransaction and r.seller == wallet:
                r.txHash = row[0]
                sales.append(r)
            row = cur.fetchone()

        con.close()
    else:
        logging.info('Skipping sales lookup due to db conn failure.')
    return sales

# Look up and return any transaction events where wallet was paid through Jewel contract
def getWalletPayments(wallet):
    payments = []
    try:
        con = aConn()
        cur = con.cursor()
    except Exception as err:
        logging.error('DB error trying to look up wallet payments. {0}'.format(str(err)))
    if con != None and con.open:
        cur.execute("SELECT * FROM transactions WHERE account=%s and eventType='airdrops'", (wallet))
        row = cur.fetchone()
        while row != None:
            r = jsonpickle.decode(row[3])
            if type(r) is list:
                for item in r:
                    if type(item) is records.AirdropTransaction and hasattr(item, 'address') and item.address == '0x6Ca68D6Df270a047b12Ba8405ec688B5dF42D50C':
                        payments.append(item)
            else:
                if type(item) is records.AirdropTransaction and hasattr(item, 'address') and item.address == '0x6Ca68D6Df270a047b12Ba8405ec688B5dF42D50C':
                    payments.append(item)
            row = cur.fetchone()

        con.close()
    else:
        logging.info('Skipping payments lookup due to db conn failure.')
    return payments

def findReport(wallet, startDate, endDate):
    con = aConn()
    cur = con.cursor()
    cur.execute("SELECT * FROM reports WHERE account=%s AND startDate=%s AND endDate=%s", (wallet, startDate, endDate))
    row = cur.fetchone()
    # Make sure they don't already have a report running for other range
    existRow = None
    if not settings.CONCURRENT_REPORTS:
        cur.execute("SELECT * FROM reports WHERE account=%s AND proc=1 AND (startDate!=%s OR endDate!=%s)", (wallet, startDate, endDate))
        existRow = cur.fetchone()
    con.close()
    if existRow != None:
        return existRow
    else:
        return row

def createReport(wallet, startDate, endDate, now, txCount, costBasis, includedChains, proc=None, moreOptions=None):
    con = aConn()
    cur = con.cursor()
    cur.execute("INSERT INTO reports VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (wallet, startDate, endDate, now, txCount, 0, 0, 0, '', '', proc, costBasis, includedChains, moreOptions))
    con.commit()
    con.close()

def resetReport(wallet, startDate, endDate, now, txCount, costBasis, includedChains, transactionFile, reportFile, moreOptions=None):
    con = aConn()
    cur = con.cursor()
    cur.execute("UPDATE reports SET generatedTimestamp=%s, transactions=%s, costBasis=%s, includedChains=%s, moreOptions=%s, reportStatus=0, transactionsFetched=0, transactionsComplete=0, reportContent='', proc=NULL WHERE account=%s AND startDate=%s AND endDate=%s", (now, txCount, costBasis, includedChains, moreOptions, wallet, startDate, endDate))
    con.commit()
    con.close()
    try:
        logging.debug('removing old report data from disk.')
        os.remove('../transactions/{0}'.format(transactionFile))
        os.remove('../reports/{0}'.format(reportFile))
    except Exception as err:
        logging.error('Failure attempting delete of report files for {0}. {1}/{2}'.format(wallet, transactionFile, reportFile))
        logging.error(err)

def completeTransactions(wallet, startDate, endDate, fileName):
    con = aConn()
    cur = con.cursor()
    cur.execute("UPDATE reports SET reportStatus=1, transactionsContent=%s WHERE account=%s and startDate=%s AND endDate=%s", (fileName, wallet, startDate, endDate))
    con.commit()
    con.close()

def completeReport(wallet, startDate, endDate, fileName):
    con = aConn()
    cur = con.cursor()
    cur.execute("UPDATE reports SET proc=0, reportStatus=2, reportContent=%s WHERE account=%s and startDate=%s AND endDate=%s", (fileName, wallet, startDate, endDate))
    con.commit()
    con.close()

def deleteReport(wallet, startDate, endDate, transactionFile, reportFile):
    con = aConn()
    cur = con.cursor()
    cur.execute("DELETE FROM reports WHERE account=%s and startDate=%s AND endDate=%s", (wallet, startDate, endDate))
    con.commit()
    con.close()
    try:
        logging.debug('removing old report data from disk.')
        os.remove('../transactions/{0}'.format(transactionFile))
        os.remove('../reports/{0}'.format(reportFile))
    except Exception as err:
        logging.error('Failure attempting delete of report files for {0}. {1}/{2}'.format(wallet, transactionFile, reportFile))
        logging.error(err)

def updateReportError(wallet, startDate, endDate, statusCode=9):
    con = aConn()
    cur = con.cursor()
    cur.execute("UPDATE reports SET proc=0, reportStatus=%s WHERE account=%s and startDate=%s AND endDate=%s", (statusCode, wallet, startDate, endDate))
    con.commit()
    con.close()

def updateReport(wallet, startDate, endDate, updateType, recordCount):
    logging.info('updated report {0} records {1} {2}'.format(wallet, updateType, recordCount))
    con = aConn()
    cur = con.cursor()
    if updateType == 'fetched':
        # sometimes the tx count is not quite right and fetched tx ends up being more, so update if so to avoid invalid progress percentages
        cur.execute("UPDATE reports SET reportStatus=0, transactionsFetched=%s, transactions=GREATEST(transactions, %s) WHERE account=%s and startDate=%s AND endDate=%s", (recordCount, recordCount, wallet, startDate, endDate))
    else:
        cur.execute("UPDATE reports SET reportStatus=1, transactionsComplete=%s WHERE account=%s and startDate=%s AND endDate=%s", (recordCount, wallet, startDate, endDate))
    con.commit()
    con.close()

def getRunningReports():
    con = aConn()
    cur = con.cursor()
    cur.execute("SELECT Count(*) FROM reports WHERE proc=1")
    row = cur.fetchone()
    con.close()
    return row[0]

def createDatabase():
    con = aConn()
    cur = con.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS prices (date VARCHAR(31), token VARCHAR(63), prices LONGTEXT, marketcap LONGTEXT, volume LONGTEXT, INDEX IX_price_date_token (date, token))')
    cur.execute('CREATE TABLE IF NOT EXISTS transactions (txHash VARCHAR(127), blockTimestamp INTEGER, eventType VARCHAR(15), events LONGTEXT, account VARCHAR(63), network VARCHAR(31), fee DOUBLE, feeValue DOUBLE, PRIMARY KEY (txHash, account), INDEX IX_tx_account (account), INDEX IX_tx_time (blockTimestamp), INDEX IX_tx_type (eventType))')
    cur.execute('CREATE TABLE IF NOT EXISTS reports (account VARCHAR(63), startDate VARCHAR(15), endDate VARCHAR(15), generatedTimestamp INTEGER, transactions INTEGER, reportStatus TINYINT, transactionsFetched INTEGER, transactionsComplete INTEGER, transactionsContent VARCHAR(63), reportContent VARCHAR(63), proc INTEGER, costBasis VARCHAR(7), includedChains INTEGER DEFAULT 3, moreOptions LONGTEXT, PRIMARY KEY (account, startDate, endDate), INDEX IX_rpt_status (reportStatus))')
    con.commit()
    con.close()

def main():
    # Initialize database
    createDatabase()
    con = aConn()
    cur = con.cursor()
    cur.execute("DELETE FROM reports")
    #cur.execute("DELETE FROM prices")
    cur.execute("DELETE FROM transactions")
    con.commit()
    con.close()


if __name__ == "__main__":
	main()