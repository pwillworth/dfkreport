#!/usr/bin/env python3
import psycopg2
import decimal
import dfkInfo
import logging
import records
import csvFormats
import jsonpickle
import hashlib
from datetime import datetime, timezone, date
import time
import os
from web3 import Web3
from hexbytes import HexBytes
from eth_account.messages import encode_defunct
import random
import csv
from io import StringIO


def ReportOptions():
    return {
        'purchaseAddresses': []
    }

def aConn():
    conn = psycopg2.connect("sslmode=verify-full sslrootcert=certs/root.crt options=--cluster=caring-wasp-2917",
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

def findWalletStatus(wallet, network):
    con = aConn()
    with con.cursor() as cur:
        cur.execute("SELECT address, network, proc, updateStatus, lastSavedBlock, lastBlockTimestamp, lastUpdateStart, txUpdateStartCount, txCount, txUpdateTargetCount, lastOwner FROM walletstatus WHERE address=%s AND network=%s", (wallet, network))
        row = cur.fetchone()

    con.close()
    return row

def createWalletStatus(wallet, network, account, fromIP):
    maxTS = 0
    con = aConn()
    with con.cursor() as cur:
        cur.execute("SELECT Max(blockTimestamp) FROM transactions WHERE account=%s AND network=%s AND eventType != 'tavern'", (wallet, network))
        row = cur.fetchone()
        if row != None and row[0] != None:
            maxTS = row[0]
        cur.execute("INSERT INTO walletstatus (address, lastOwner, network, lastSavedBlock, lastBlockTimestamp, lastUpdateStart, updateStatus, fromIP) VALUES (%s, %s, %s, 0, %s, 0, %s, %s)", (wallet, account, network, maxTS, 0, fromIP))
    con.close()

def forceWalletUpdate(wallet, network):
    con = aConn()
    with con.cursor() as cur:
        cur.execute("UPDATE walletstatus SET lastUpdateStart=NULL WHERE address=%s and network=%s", (wallet, network))
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

def getReportData(contentFile):
    con = aConn()
    with con.cursor() as cur:
        cur.execute('SELECT rData from reportdata WHERE id=%s', (contentFile,))
        result = cur.fetchone()
    con.close()
    return result

def getEventData(wallet, eventType, networks):
    events = []
    try:
        con = aConn()
        cur = con.cursor()
    except Exception as err:
        logging.error('DB error trying to look up event data. {0}'.format(str(err)))
    if con != None and not con.closed:
        cur.execute("SELECT * FROM transactions WHERE account=%s AND eventType=%s AND network IN %s", (wallet, eventType, networks))
        rows = cur.fetchmany(100)
        while len(rows) > 0:
            for row in rows:
                r = jsonpickle.decode(row[3])
                if type(r) is list:
                    for evt in r:
                        evt.txHash = row[0]
                        evt.network = row[5]
                        events.append(evt)
                else:
                    # cache records saved before feb 2022 did not have txHash property
                    r.txHash = row[0]
                    # cache records saved before dec 2022 did not have network property
                    r.network = row[5]
                    events.append(r)
            rows = cur.fetchmany(100)

        con.close()
    else:
        logging.info('Skipping data lookup due to db conn failure.')
    return events

def getEventDataCSV(wallets, networks, csvFormat, startDate, endDate):
    line = StringIO()
    writer = csv.writer(line)
    try:
        con = aConn()
        cur = con.cursor()
    except Exception as err:
        logging.error('DB error trying to look up event data. {0}'.format(str(err)))
    if con != None and not con.closed:
        cur.execute("SELECT * FROM transactions WHERE account IN %s AND network IN %s", (wallets, networks))
        rows = cur.fetchmany(500)
        while len(rows) > 0:
            events = records.EventsMap()
            for row in rows:
                # restrict to desired date range - TODO make index on blockTimestamp and add to query
                itemDate = date.fromtimestamp(row[1])
                if itemDate < startDate or itemDate > endDate or len(row[3]) < 2:
                    continue

                r = jsonpickle.decode(row[3])
                if type(r) is list:
                    for evt in r:
                        events[row[2]].append(evt)
                else:
                    events[row[2]].append(r)
            result = csvFormats.getResponseCSV(events, csvFormat)
            for cLine in result:
                writer.writerow(cLine)
                line.seek(0)
                yield line.read()
                line.truncate(0)
                line.seek(0)
            rows = cur.fetchmany(500)
        con.close()
    else:
        logging.info('Skipping data lookup due to db conn failure.')

def getWalletGroup(account, group=None):
    results = []
    nowStamp = datetime.now(timezone.utc).timestamp()
    con = aConn()
    with con.cursor() as cur:
        if group == None:
            cur.execute("SELECT wallets FROM groups INNER JOIN members ON groups.account = members.account WHERE members.expiresTimestamp > %s AND groups.account=%s", (nowStamp,account))
        else:
            cur.execute("SELECT wallets FROM groups INNER JOIN members ON groups.account = members.account WHERE members.expiresTimestamp > %s AND groups.account=%s AND groupName=%s", (nowStamp,account,group))
        row = cur.fetchone()
        while row != None:
            results += jsonpickle.decode(row[0])
            row = cur.fetchone()
    con.close()

    return list(set(results))

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
	cursor.execute('SELECT account, expires FROM sessions WHERE sid=%s', (sid,))
	row = cursor.fetchone()
	if row == None:
		# no record
		result = ""
	else:
		if time.time() > row[1]:
			# session is expired, delete it
			result = ""
			tempSQL = "DELETE FROM tSessions WHERE sid='{0}'".format(sid)
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

def getWalletUpdateList(wallets):
    result = []
    con = aConn()
    cur = con.cursor()
    cur.execute("SELECT address, network, proc, updateStatus, lastSavedBlock, lastBlockTimestamp, lastUpdateStart, txUpdateStartCount, txCount, txUpdateTargetCount, lastOwner FROM walletstatus WHERE address IN %s ORDER BY address, network", (wallets,))
    row = cur.fetchone()
    while row != None:
        result.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]])
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
        generateTime = datetime.now(timezone.utc)
        if row != None and row[0] != None:
            cur.execute("UPDATE groups SET groupName=%s, updatedTimestamp=%s WHERE account=%s AND wallets=%s", (groupName, generateTime, account, jsonpickle.encode(addressList)))
        elif row2 != None and row2[0] != None:
            cur.execute("UPDATE groups SET wallets=%s, updatedTimestamp=%s WHERE account=%s AND groupName=%s", (jsonpickle.encode(addressList), generateTime, account, groupName))
        else:
            cur.execute("INSERT INTO groups (account, groupName, wallets, generatedTimestamp) VALUES (%s, %s, %s, %s)", (account, groupName, jsonpickle.encode(addressList), generateTime))
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

def main():
    con = aConn()
    cur = con.cursor()
    #cur.execute("DELETE FROM reports")
    #cur.execute("DELETE FROM prices")
    #cur.execute("DELETE FROM transactions")
    #con.commit()
    con.close()


if __name__ == "__main__":
	main()