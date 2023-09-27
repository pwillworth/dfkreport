#!/usr/bin/env python3
import psycopg2
import dfkInfo
import logging
import hashlib

def ReportOptions():
    return {
        'purchaseAddresses': []
    }

def aConn():
    conn = psycopg2.connect("sslmode=verify-full sslrootcert=web/certs/root.crt options=--cluster=caring-wasp-2917",
        host = dfkInfo.DB_HOST,
        port = "26257",
	    dbname= dfkInfo.DB_NAME,
	    user = dfkInfo.DB_USER,
	    password = dfkInfo.DB_PASS)
    conn.autocommit = True

    return conn

# get a unique value representing wallet list that can be used in a DB key
def getWalletHash(wallets):
    m = hashlib.sha1()
    for item in wallets:
        m.update(item.encode('utf-8'))
    return m.hexdigest()

def completeTransactions(wallet, network):
    con = aConn()
    cur = con.cursor()
    cur.execute("UPDATE walletstatus SET updateStatus=1 WHERE address=%s and network=%s", (wallet, network))
    con.close()

def updateWalletStatus(wallet, network, updateType, recordCount, blockNumber=None, blockTimestamp=None):
    con = aConn()
    cur = con.cursor()
    if updateType == 'initiated':
        cur.execute("UPDATE walletstatus SET updateStatus=0, txUpdateTargetCount=%s WHERE address=%s and network=%s", (recordCount, wallet, network))
    elif updateType == 'fetched':
        # sometimes the tx count is not quite right and fetched tx ends up being more, so update if so to avoid invalid progress percentages
        cur.execute("UPDATE walletstatus SET updateStatus=0, txCount=%s WHERE address=%s and network=%s", (recordCount, wallet, network))
    else:
        cur.execute("UPDATE walletstatus SET updateStatus=1, txCount=%s, lastSavedBlock=%s, lastBlockTimestamp=%s WHERE address=%s AND network=%s", (recordCount, blockNumber, blockTimestamp, wallet, network))
    logging.info('updating report {0} {1} records {2} {3} - found rpt {4}'.format(wallet, network, updateType, recordCount, cur.rowcount))
    con.close()

def completeWalletUpdate(wallet, network, txCount):
    con = aConn()
    cur = con.cursor()
    cur.execute("UPDATE walletstatus SET proc=NULL, updateStatus=2, txCount=%s WHERE address=%s AND network=%s", (txCount, wallet, network))
    logging.info('updating report {0} {1} - found rpt {2}'.format(wallet, network, cur.rowcount))
    con.close()

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
        con.close()
    except Exception as err:
        # incase DB is down, it's ok we just wont cache
        logging.error('db error saving price data {0}'.format(str(err)))

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
    if con != None and not con.closed:
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

def getRunningUpdates():
    con = aConn()
    cur = con.cursor()
    cur.execute("SELECT Count(*) FROM walletstatus WHERE proc IS NOT NULL")
    row = cur.fetchone()
    con.close()
    return row[0]

def findReport(account, startDate, endDate, walletHash):
    con = aConn()
    existRow = None
    with con.cursor() as cur:
        cur.execute("SELECT account, startDate, endDate, generatedTimestamp, transactions, reportStatus, transactionsFetched, transactionsComplete, transactionsContent, reportContent, proc, costBasis, includedChains, moreOptions, txCounts, wallets, walletGroup, walletHash FROM reports WHERE account=%s AND startDate=%s AND endDate=%s AND walletHash=%s", (account, startDate, endDate, walletHash))
        row = cur.fetchone()
        cur.execute("SELECT account, startDate, endDate, generatedTimestamp, transactions, reportStatus, transactionsFetched, transactionsComplete, transactionsContent, reportContent, proc, costBasis, includedChains, moreOptions, txCounts, wallets, walletGroup, walletHash FROM reports WHERE account=%s AND proc=1 AND (startDate!=%s OR endDate!=%s OR walletHash!=%s)", (account, startDate, endDate, walletHash))
        existRow = cur.fetchone()
    con.close()
    if existRow != None:
        return existRow
    else:
        return row

def getReportTx(contentFile):
    con = aConn()
    with con.cursor() as cur:
        cur.execute('SELECT txData from reporttx WHERE id=%s', (contentFile,))
        result = cur.fetchone()
    con.close()
    return result

def updateReportError(wallet, network, statusCode=9):
    con = aConn()
    cur = con.cursor()
    cur.execute("UPDATE walletstatus SET proc=NULL, updateStatus=%s WHERE address=%s and network=%s", (statusCode, wallet, network))
    con.close()

def createDatabase():
    con = aConn()
    cur = con.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS prices (date VARCHAR(31), token VARCHAR(63), prices STRING, marketcap STRING, volume STRING, INDEX IX_price_date_token (date, token))')
    cur.execute('CREATE TABLE IF NOT EXISTS transactions (txHash VARCHAR(127), blockTimestamp INTEGER, eventType VARCHAR(15), events STRING, account VARCHAR(63), network VARCHAR(31), fee FLOAT, feeValue FLOAT, PRIMARY KEY (txHash, account), INDEX IX_tx_account_type (account, eventType), INDEX IX_account_network (account, network), INDEX IX_account_network_bts (account, network, blockTimestamp))')
    cur.execute('CREATE TABLE IF NOT EXISTS reports (account VARCHAR(63), startDate VARCHAR(15), endDate VARCHAR(15), generatedTimestamp INTEGER, transactions INTEGER, reportStatus INT2, transactionsFetched INTEGER, transactionsComplete INTEGER, transactionsContent VARCHAR(63), reportContent VARCHAR(63), proc INTEGER, costBasis VARCHAR(7), includedChains INTEGER DEFAULT 3, moreOptions STRING, txCounts VARCHAR(10230), wallets STRING, walletGroup VARCHAR(63), walletHash VARCHAR(63), PRIMARY KEY (account, startDate, endDate, walletHash), INDEX IX_rpt_status (reportStatus))')
    cur.execute('CREATE TABLE IF NOT EXISTS groups (account VARCHAR(63), groupName VARCHAR(255), wallets STRING, generatedTimestamp TIMESTAMP NOT NULL, updatedTimestamp TIMESTAMP, PRIMARY KEY (account, groupName))')
    cur.execute('CREATE TABLE IF NOT EXISTS members (account VARCHAR(63) PRIMARY KEY, nonce INTEGER, generatedTimestamp INTEGER, expiresTimestamp INTEGER, lastLogin INTEGER)')
    cur.execute('CREATE TABLE IF NOT EXISTS payments (account VARCHAR(63), generatedTimestamp TIMESTAMP NOT NULL, txHash VARCHAR(127), token VARCHAR(63), amount FLOAT, previousExpires INTEGER, newExpires INTEGER, network VARCHAR(31), PRIMARY KEY (network, txHash), INDEX IX_pay_account (account))')
    cur.execute('CREATE TABLE IF NOT EXISTS sessions (sid VARCHAR(40) NOT NULL PRIMARY KEY, account VARCHAR(63) NOT NULL, expires FLOAT, INDEX IX_session_account (account))')
    cur.execute('CREATE TABLE IF NOT EXISTS balances (updateTime TIMESTAMP PRIMARY KEY, balanceData STRING)')
    cur.execute('CREATE TABLE IF NOT EXISTS walletstatus (address VARCHAR(63), lastOwner VARCHAR(63), network VARCHAR(31), proc INTEGER, lastSavedBlock INTEGER, lastBlockTimestamp INTEGER, lastUpdateStart INTEGER, txUpdateStartCount INTEGER, txCount INTEGER, txUpdateTargetCount INTEGER, updateStatus INT2, PRIMARY KEY (address, network), INDEX IX_walletstatus_status (updateStatus))')
    con.commit()
    con.close()

def main():
    # Initialize database
    createDatabase()

if __name__ == "__main__":
	main()