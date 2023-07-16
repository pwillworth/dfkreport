#!/usr/bin/env python3
import psycopg2
import decimal
import dfkInfo
import logging
import settings
import jsonpickle
import hashlib
from datetime import datetime, timezone
import time
import os
from web3 import Web3
from hexbytes import HexBytes
from eth_account.messages import encode_defunct
import random

def ReportOptions():
    return {
        'purchaseAddresses': []
    }

def aConn():
    conn = psycopg2.connect("sslmode=verify-full options=--cluster=caring-wasp-2917",
        host = dfkInfo.DB_HOST,
        port = "26257",
	    dbname= dfkInfo.DB_NAME,
	    user = dfkInfo.DB_USER,
	    password = dfkInfo.DB_PASS)
    conn.autocommit = True

    return conn

def dbInsertSafe(insertStr):
    newStr = ""
    if (insertStr != None):
        for i in range(len(str(insertStr))):
            if (str(insertStr)[i] == "'"):
                newStr = newStr + "'"
            newStr = newStr + str(insertStr)[i]
    return newStr

# get a unique value representing wallet list that can be used in a DB key
def getWalletHash(wallets):
    m = hashlib.sha1()
    for item in wallets:
        m.update(item.encode('utf-8'))
    return m.hexdigest()

def readBalance():
    con = aConn()
    with con.cursor() as cur:
        cur.execute('SELECT updateTime, balanceData FROM balances ORDER BY updateTime DESC LIMIT 1')
        row = cur.fetchone()
    con.close()
    balance = 0
    results = jsonpickle.loads(row[1])
    if 'tokens' in results:
        for k, v in results['tokens'].items():
            balance += decimal.Decimal(v[1])
    if 'updatedAt' in results:
        updatedAt = results['updatedAt']
    return balance

def getTransactions(account, network):
    try:
        con = aConn()
        cur = con.cursor()
        cur.execute("SELECT * FROM transactions WHERE account=%s AND network=%s", (account, network))
        rows = cur.fetchall()
        con.close()
    except Exception as err:
        # if db is unavailable we can just continue
        logging.error('Error getting txs {0}'.format(str(err)))
        rows = []

    return dict([[row[0], row] for row in rows])

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
        except Exception as err:
            logging.error('Unexpected Error {0} caching transaction {1} - '.format(err, tx))
        con.close()
    else:
        logging.info('Skipping tx save due to previous db failure.')

# For determining how much history we already have for a wallet cached
def getLastTransactionTimestamp(account, network):
    try:
        con = aConn()
        cur = con.cursor()
        # Dont include tavern transactions to find last tx cached because it may be from block crawler
        cur.execute("SELECT max(blockTimestamp) FROM transactions WHERE account=%s and network=%s and eventType != 'tavern'", (account, network))
        row = cur.fetchone()
        con.close()
    except Exception as err:
        # if db is unavailable we can just continue
        logging.error('Error finding tx {0}'.format(str(err)))
        row = None
    if row == None or row[0] == None:
        return 1648710000
    else:
        return row[0]

def findReport(account, startDate, endDate, walletHash):
    con = aConn()
    cur = con.cursor()
    cur.execute("SELECT account, startDate, endDate, generatedTimestamp, transactions, reportStatus, transactionsFetched, transactionsComplete, transactionsContent, reportContent, proc, costBasis, includedChains, moreOptions, txCounts, wallets, walletGroup, walletHash FROM reports WHERE account=%s AND startDate=%s AND endDate=%s AND walletHash=%s", (account, startDate, endDate, walletHash))
    row = cur.fetchone()
    # Make sure they don't already have a report running for other range
    existRow = None
    if not settings.CONCURRENT_REPORTS:
        cur.execute("SELECT account, startDate, endDate, generatedTimestamp, transactions, reportStatus, transactionsFetched, transactionsComplete, transactionsContent, reportContent, proc, costBasis, includedChains, moreOptions, txCounts, wallets, walletGroup, walletHash FROM reports WHERE account=%s AND proc=1 AND (startDate!=%s OR endDate!=%s OR walletHash!=%s)", (account, startDate, endDate, walletHash))
        existRow = cur.fetchone()
    con.close()
    if existRow != None:
        return existRow
    else:
        return row

def createReport(account, startDate, endDate, now, txCount, costBasis, includedChains, wallets, group, walletHash, proc=None, moreOptions=None, txCounts=[]):
    con = aConn()
    cur = con.cursor()
    cur.execute("INSERT INTO reports (account, startDate, endDate, generatedTimestamp, transactions, reportStatus, transactionsFetched, transactionsComplete, transactionsContent, reportContent, proc, costBasis, includedChains, moreOptions, txCounts, wallets, walletGroup, walletHash) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (account, startDate, endDate, now, txCount, 0, 0, 0, '', '', proc, costBasis, includedChains, moreOptions, txCounts, jsonpickle.encode(wallets), group, walletHash))
    con.close()

def resetReport(wallet, startDate, endDate, now, txCount, costBasis, includedChains, transactionFile, reportFile, walletHash, moreOptions=None, txCounts=[]):
    con = aConn()
    cur = con.cursor()
    cur.execute("UPDATE reports SET generatedTimestamp=%s, transactions=%s, costBasis=%s, includedChains=%s, moreOptions=%s, reportStatus=0, transactionsFetched=0, transactionsComplete=0, reportContent='', proc=NULL, txCounts=%s WHERE account=%s AND startDate=%s AND endDate=%s AND walletHash=%s", (now, txCount, costBasis, includedChains, moreOptions, txCounts, wallet, startDate, endDate, walletHash))
    con.close()
    try:
        logging.debug('removing old report data from disk.')
        os.remove('../transactions/{0}'.format(transactionFile))
        os.remove('../reports/{0}'.format(reportFile))
    except Exception as err:
        logging.error('Failure attempting delete of report files for {0}. {1}/{2}'.format(wallet, transactionFile, reportFile))
        logging.error(err)

def completeTransactions(wallet, startDate, endDate, walletHash, fileName):
    con = aConn()
    cur = con.cursor()
    cur.execute("UPDATE reports SET reportStatus=1, transactionsContent=%s WHERE account=%s and startDate=%s AND endDate=%s AND walletHash=%s", (fileName, wallet, startDate, endDate, walletHash))
    con.close()

def completeReport(wallet, startDate, endDate, walletHash, fileName):
    con = aConn()
    cur = con.cursor()
    cur.execute("UPDATE reports SET proc=0, reportStatus=2, reportContent=%s WHERE account=%s and startDate=%s AND endDate=%s AND walletHash=%s", (fileName, wallet, startDate, endDate, walletHash))
    con.close()

def deleteReport(wallet, startDate, endDate, walletHash, transactionFile, reportFile):
    con = aConn()
    cur = con.cursor()
    cur.execute("DELETE FROM reports WHERE account=%s and startDate=%s AND endDate=%s AND walletHash=%s", (wallet, startDate, endDate, walletHash))
    con.close()
    try:
        logging.debug('removing old report data from disk.')
        os.remove('../transactions/{0}'.format(transactionFile))
        os.remove('../reports/{0}'.format(reportFile))
    except Exception as err:
        logging.error('Failure attempting delete of report files for {0}. {1}/{2}'.format(wallet, transactionFile, reportFile))
        logging.error(err)

def updateReportError(wallet, startDate, endDate, walletHash, statusCode=9):
    con = aConn()
    cur = con.cursor()
    cur.execute("UPDATE reports SET proc=0, reportStatus=%s WHERE account=%s and startDate=%s AND endDate=%s AND walletHash=%s", (statusCode, wallet, startDate, endDate, walletHash))
    con.close()

def updateReport(wallet, startDate, endDate, walletHash, updateType, recordCount):
    con = aConn()
    cur = con.cursor()
    if updateType == 'fetched':
        # sometimes the tx count is not quite right and fetched tx ends up being more, so update if so to avoid invalid progress percentages
        cur.execute("UPDATE reports SET reportStatus=0, transactionsFetched=%s, transactions=GREATEST(transactions, %s) WHERE account=%s and startDate=%s AND endDate=%s AND walletHash=%s", (recordCount, recordCount, wallet, startDate, endDate, walletHash))
    else:
        cur.execute("UPDATE reports SET reportStatus=1, transactionsComplete=%s WHERE account=%s and startDate=%s AND endDate=%s AND walletHash=%s", (recordCount, wallet, startDate, endDate, walletHash))
    logging.info('updating report {0} records {1} {2} - found rpt {3}'.format(wallet, updateType, recordCount, cur.rowcount))
    con.close()

def getRunningReports():
    con = aConn()
    cur = con.cursor()
    cur.execute("SELECT Count(*) FROM reports WHERE proc=1")
    row = cur.fetchone()
    con.close()
    return row[0]

def getWalletGroup(account, group):
    results = []
    nowStamp = datetime.now(timezone.utc).timestamp()
    con = aConn()
    cur = con.cursor()
    cur.execute("SELECT wallets FROM groups INNER JOIN members ON groups.account = members.account WHERE members.expiresTimestamp > %s AND groups.account=%s AND groupName=%s", (nowStamp,account,group))
    row = cur.fetchone()
    if row != None:
        results = jsonpickle.decode(row[0])
    con.close()

    return results

def getMemberStatus(account):
    memberState = 0
    requestTime = datetime.now(timezone.utc).timestamp()
    expiresTimestamp = 0
    secondsLeft = 0
    con = aConn()
    with con.cursor() as cur:
        cur.execute('SELECT expiresTimestamp FROM members WHERE account=%s', (account,))
        row = cur.fetchone()
        if row[0] != None:
            expiresTimestamp = row[0]
            secondsLeft = expiresTimestamp - requestTime
        if expiresTimestamp != None and requestTime < expiresTimestamp:
            if secondsLeft > 0:
                memberState = 2
            else:
                memberState = 1
        else:
            memberState = 1
    con.close()
    return [memberState, secondsLeft, expiresTimestamp]

# look up a session id and see if it is valid
def checkSession(sid):
	con = aConn()
	cursor = con.cursor()
	cursor.execute('SELECT account, expires FROM sessions WHERE sid=%s', (sid))
	row = cursor.fetchone()
	if row == None:
		# no record
		result = ""
	else:
		if time.time() > row[1]:
			# session is expired, delete it
			result = ""
			tempSQL = "DELETE FROM tSessions WHERE sid='" + sid + "'"
			cursor.execute(tempSQL)
		else:
			# good session, return userid
			result = row[0]

	cursor.close()
	con.close()
	return result

def getSession(account, signature):
    result = 0
    #sessions persist up to 180 days
    duration = 15552000
    con = aConn()
    cur = con.cursor()
    cur.execute("SELECT nonce FROM members WHERE account = %s", (account,))
    row = cur.fetchone()
    if row != None:
        result = row[0]
    else:
        con.close()
        return 'Error: account does not exist'

    msg = 'Lilas Ledger login uses no transaction or gas fees.\n\nClick Sign to verify you own this wallet and login.\n\nIf you have cookies enabled, your session can persist for up to 6 months or until you logout.\n\nnonce: {0}'.format(result)
    w3 = Web3(Web3.HTTPProvider(""))
    message = encode_defunct(text=msg)
    address = w3.eth.account.recover_message(message, signature=HexBytes(signature))

    if address == account:
        # new session
        sidHash = str(time.time()) + account
        sid = hashlib.sha1(sidHash.encode()).hexdigest()
        updatestr = 'INSERT INTO sessions (sid, account, expires) VALUES (%s, %s, %s)'
        cur.execute(updatestr, (sid, account, time.time() + duration))
        # update login time and nonce for next login attempt
        generateTime = datetime.now(timezone.utc)
        updatestr = 'UPDATE members SET lastLogin=%s, nonce=%s WHERE account=%s'
        cur.execute(updatestr, (int(datetime.timestamp(generateTime)), random.randint(1,10000000), account))
        result = sid
    else:
        result = 'Error: authentication failed, bad signature'
    con.close()
    return result

def getAccountNonce(account):
    result = ''
    con = aConn()
    cur = con.cursor()
    cur.execute("SELECT nonce FROM members WHERE account = %s", (account,))
    row = cur.fetchone()
    if row != None:
        result = row[0]
    else:
        result = random.randint(1,10000000)
        generateTime = datetime.now(timezone.utc)
        cur.execute("INSERT INTO members (account, nonce, generatedTimestamp, expiresTimestamp) VALUES (%s, %s, %s, %s)", (account, result, int(datetime.timestamp(generateTime)), int(datetime.timestamp(generateTime))+86400))

    con.close()

    return result

def getReportList(account):
    result = []
    con = aConn()
    cur = con.cursor()
    cur.execute("SELECT CASE WHEN walletGroup = '' THEN account ELSE walletGroup END, startDate, endDate, generatedTimestamp, reportStatus, transactions, transactionsFetched, transactionsComplete, reportContent FROM reports WHERE account = %s ORDER BY generatedTimestamp DESC", (account,))
    row = cur.fetchone()
    while row != None:
        result.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]])
        row = cur.fetchone()
    con.close()

    return result

def getGroupList(account):
    results = []
    con = aConn()
    cur = con.cursor()
    cur.execute("SELECT account, groupName, wallets FROM groups WHERE account = %s ORDER BY generatedTimestamp DESC", (account,))
    row = cur.fetchone()
    while row != None:
        results.append([row[0], row[1], row[2]])
        row = cur.fetchone()
    con.close()

    return jsonpickle.encode(results)

def addGroupList(account, groupName, addressList):
    result = 0
    con = aConn()
    with con.cursor() as cur:
        cur.execute("SELECT account, groupName, wallets FROM groups WHERE account = %s AND wallets=%s", (account,jsonpickle.encode(addressList)))
        row = cur.fetchone()
        cur.execute("SELECT account, groupName, wallets FROM groups WHERE account = %s AND groupName=%s", (account,groupName))
        row2 = cur.fetchone()
        if row != None and row[0] != None:
            cur.execute("UPDATE groups SET groupName=%s, updatedTimestamp=UTC_TIMESTAMP() WHERE account=%s AND wallets=%s", (groupName, account, jsonpickle.encode(addressList)))
        elif row2 != None and row2[0] != None:
            cur.execute("UPDATE groups SET wallets=%s, updatedTimestamp=UTC_TIMESTAMP() WHERE account=%s AND groupName=%s", (jsonpickle.encode(addressList), account, groupName))
        else:
            cur.execute("INSERT INTO groups (account, groupName, wallets, generatedTimestamp) VALUES (%s, %s, %s, UTC_TIMESTAMP())", (account, groupName, jsonpickle.encode(addressList)))
        result = cur.rowcount
    con.close()

    return result

def removeGroupList(account, groupName):
    result = 0
    con = aConn()
    with con.cursor() as cur:
        cur.execute("DELETE FROM groups WHERE account=%s AND groupName=%s", (account, groupName))
        result = cur.rowcount
    con.close()

    return result

def createDatabase():
    con = aConn()
    cur = con.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS prices (date VARCHAR(31), token VARCHAR(63), prices STRING, marketcap STRING, volume STRING, INDEX IX_price_date_token (date, token))')
    cur.execute('CREATE TABLE IF NOT EXISTS transactions (txHash VARCHAR(127), blockTimestamp INTEGER, eventType VARCHAR(15), events STRING, account VARCHAR(63), network VARCHAR(31), fee FLOAT, feeValue FLOAT, PRIMARY KEY (txHash, account), INDEX IX_tx_account (account), INDEX IX_tx_time (blockTimestamp), INDEX IX_tx_type (eventType))')
    cur.execute('CREATE TABLE IF NOT EXISTS reports (account VARCHAR(63), startDate VARCHAR(15), endDate VARCHAR(15), generatedTimestamp INTEGER, transactions INTEGER, reportStatus INT2, transactionsFetched INTEGER, transactionsComplete INTEGER, transactionsContent VARCHAR(63), reportContent VARCHAR(63), proc INTEGER, costBasis VARCHAR(7), includedChains INTEGER DEFAULT 3, moreOptions STRING, txCounts VARCHAR(10230), wallets STRING, walletGroup VARCHAR(63), walletHash VARCHAR(63), PRIMARY KEY (account, startDate, endDate, walletHash), INDEX IX_rpt_status (reportStatus))')
    cur.execute('CREATE TABLE IF NOT EXISTS groups (account VARCHAR(63), groupName VARCHAR(255), wallets STRING, generatedTimestamp TIMESTAMP NOT NULL, updatedTimestamp TIMESTAMP, PRIMARY KEY (account, groupName))')
    cur.execute('CREATE TABLE IF NOT EXISTS members (account VARCHAR(63) PRIMARY KEY, nonce INTEGER, generatedTimestamp INTEGER, expiresTimestamp INTEGER, lastLogin INTEGER)')
    cur.execute('CREATE TABLE IF NOT EXISTS payments (account VARCHAR(63), generatedTimestamp TIMESTAMP NOT NULL, txHash VARCHAR(127), token VARCHAR(63), amount FLOAT, previousExpires INTEGER, newExpires INTEGER, network VARCHAR(31), PRIMARY KEY (network, txHash), INDEX IX_pay_account (account))')
    cur.execute('CREATE TABLE IF NOT EXISTS sessions (sid VARCHAR(40) NOT NULL PRIMARY KEY, account VARCHAR(63) NOT NULL, expires FLOAT, INDEX IX_session_account (account))')
    cur.execute('CREATE TABLE IF NOT EXISTS balances (updateTime TIMESTAMP PRIMARY KEY, balanceData STRING)')
    con.commit()
    con.close()

def main():
    # Initialize database
    createDatabase()
    con = aConn()
    cur = con.cursor()
    #cur.execute("DELETE FROM reports")
    #cur.execute("DELETE FROM prices")
    #cur.execute("DELETE FROM transactions")
    #con.commit()
    con.close()


if __name__ == "__main__":
	main()