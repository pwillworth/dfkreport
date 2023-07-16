#!/usr/bin/env python3
import psycopg2
import dfkInfo
import logging

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

# Look up and return any transaction events where wallet was the seller
def getTavernSales(wallet, startDate, endDate):
    sales = []
    startStamp = int(datetime(startDate.year, startDate.month, startDate.day).timestamp())
    endStamp = int(datetime(endDate.year, endDate.month, endDate.day).timestamp() + 86400)
    try:
        con = aConn()
        cur = con.cursor()
    except Exception as err:
        logging.error('DB error trying to look up tavern sales. {0}'.format(str(err)))
    if con != None and con.open:
        cur.execute("SELECT * FROM transactions WHERE account=%s and network != 'dfkchain' and eventType='tavern' and blockTimestamp>=%s and blockTimestamp<%s", (wallet, startStamp, endStamp))
        row = cur.fetchone()
        while row != None:
            r = jsonpickle.decode(row[3])
            if type(r) is records.TavernTransaction and r.seller == wallet:
                r.txHash = row[0]
                r.network = row[5]
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