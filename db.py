#!/usr/bin/env python3
import pymysql
import dfkInfo
import logging
import records
import jsonpickle
import datetime
import os

def aConn():
	conn = pymysql.connect(host = dfkInfo.DB_HOST,
	db= dfkInfo.DB_NAME,
	user = dfkInfo.DB_USER,
	passwd = dfkInfo.DB_PASS)
	conn.autocommit(True)
	return conn

def findPriceData(date, token):
    con = aConn()
    cur = con.cursor()
    cur.execute("SELECT * FROM prices WHERE date=%s AND token=%s", (date, token))
    row = cur.fetchone()
    con.close()

    return row

def savePriceData(date, token, price, liquid, volume):
    con = aConn()
    cur = con.cursor()
    cur.execute("INSERT INTO prices VALUES (%s, %s, %s, %s, %s)", (date, token, price, liquid, volume))
    con.commit()
    con.close()

def findTransaction(txHash, account):
    con = aConn()
    cur = con.cursor()
    cur.execute("SELECT * FROM transactions WHERE txHash=%s AND account=%s", (txHash, account))
    row = cur.fetchone()
    con.close()

    return row

def saveTransaction(tx, timestamp, type, events, wallet):
    con = aConn()
    cur = con.cursor()
    cur.execute("INSERT INTO transactions VALUES (%s, %s, %s, %s, %s)", (tx, timestamp, type, events, wallet))
    con.commit()
    con.close()

# Look up and return any transaction events where wallet was the seller
def getTavernSales(wallet, startDate, endDate):
    sales = []
    startStamp = int(datetime.datetime(startDate.year, startDate.month, startDate.day).timestamp())
    endStamp = int(datetime.datetime(endDate.year, endDate.month, endDate.day).timestamp() + 86400)
    con = aConn()
    cur = con.cursor()
    cur.execute("SELECT * FROM transactions WHERE account=%s and eventType='tavern' and blockTimestamp>=%s and blockTimestamp<%s", (wallet, startStamp, endStamp))
    row = cur.fetchone()
    while row != None:
        r = jsonpickle.decode(row[3])
        if type(r) is records.TavernTransaction and r.seller == wallet:
            sales.append(r)
        row = cur.fetchone()

    con.close()
    return sales

def findReport(wallet, startDate, endDate):
    con = aConn()
    cur = con.cursor()
    cur.execute("SELECT * FROM reports WHERE account=%s AND startDate=%s AND endDate=%s", (wallet, startDate, endDate))
    row = cur.fetchone()
    con.close()

    return row

def createReport(wallet, startDate, endDate, now, txCount, costBasis, proc=None):
    con = aConn()
    cur = con.cursor()
    cur.execute("INSERT INTO reports VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (wallet, startDate, endDate, now, txCount, 0, 0, 0, '', '', proc, costBasis))
    con.commit()
    con.close()

def resetReport(wallet, startDate, endDate, now, txCount, costBasis, transactionFile, reportFile):
    con = aConn()
    cur = con.cursor()
    cur.execute("UPDATE reports SET generatedTimestamp=%s, transactions=%s, costBasis=%s, reportStatus=0, transactionsFetched=0, transactionsComplete=0, reportContent='', proc=NULL WHERE account=%s AND startDate=%s AND endDate=%s", (now, txCount, costBasis, wallet, startDate, endDate))
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

def deleteReport(wallet, startDate, endDate):
    con = aConn()
    cur = con.cursor()
    cur.execute("DELETE FROM reports WHERE account=%s and startDate=%s AND endDate=%s", (wallet, startDate, endDate))
    con.commit()
    con.close()

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
        cur.execute("UPDATE reports SET reportStatus=0, transactionsFetched=%s WHERE account=%s and startDate=%s AND endDate=%s", (recordCount, wallet, startDate, endDate))
    else:
        cur.execute("UPDATE reports SET reportStatus=1, transactionsComplete=%s WHERE account=%s and startDate=%s AND endDate=%s", (recordCount, wallet, startDate, endDate))
    con.commit()
    con.close()

def createDatabase():
    con = aConn()
    cur = con.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS prices (date VARCHAR(31), token VARCHAR(63), prices LONGTEXT, marketcap LONGTEXT, volume LONGTEXT, INDEX IX_price_date_token (date, token))')
    cur.execute('CREATE TABLE IF NOT EXISTS transactions (txHash VARCHAR(127), blockTimestamp INTEGER, eventType VARCHAR(15), events LONGTEXT, account VARCHAR(63), PRIMARY KEY (txHash, account), INDEX IX_tx_account (account), INDEX IX_tx_time (blockTimestamp))')
    cur.execute('CREATE TABLE IF NOT EXISTS reports (account VARCHAR(63), startDate VARCHAR(15), endDate VARCHAR(15), generatedTimestamp INTEGER, transactions INTEGER, reportStatus TINYINT, transactionsFetched INTEGER, transactionsComplete INTEGER, transactionsContent VARCHAR(63), reportContent VARCHAR(63), proc INTEGER, costBasis VARCHAR(7), PRIMARY KEY (account, startDate, endDate), INDEX IX_rpt_status (reportStatus))')
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