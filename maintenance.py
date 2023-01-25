#!/usr/bin/env python3
# Maintenace module to periodically clear old generated report data
import db
import settings
from datetime import datetime, timezone, timedelta
import logging
import logging.handlers
import os

# Delete saved reports and their data files older than a timestamp
def cleanReports(beforeTimestamp):
    cleanCount = 0
    nowstamp = int(datetime.now(timezone.utc).timestamp())
    con = db.aConn()
    cur = con.cursor()
    cur.execute("SELECT reports.account, startDate, endDate, transactionsContent, reportContent, walletHash FROM reports LEFT JOIN members on reports.account = members.account WHERE proc=0 and reports.generatedTimestamp < %s AND (members.expiresTimestamp < %s OR members.expiresTimestamp IS NULL)", (beforeTimestamp,nowstamp))
    row = cur.fetchone()
    while row != None:
        db.deleteReport(row[0], row[1], row[2], row[5], row[3], row[4])
        cleanCount += 1
        row = cur.fetchone()
    con.close()
    logging.info('Cleaned up {0} old reports'.format(cleanCount))

# Delete saved transaction data for any account that has not run a report recently enough to still be saved
def cleanTransactions():
    accounts = []
    cleanAccounts = []
    nowstamp = int(datetime.now(timezone.utc).timestamp())
    con = db.aConn()
    # Get list of accounts with active reports
    with con.cursor() as cur:
        cur.execute("SELECT account FROM reports")
        row = cur.fetchone()
        while row != None:
            accounts.append(row[0])
            row = cur.fetchone()
    logging.info('{0} accounts have active reports: {1}'.format(len(accounts), str(accounts)))
    # Get list of accounts that have saved transaction data excluding tavern type so we dont bother with accts that have only activity from sales crawler
    with con.cursor() as cur2:
        cur2.execute("SELECT DISTINCT account FROM transactions WHERE eventType != 'tavern'")
        row = cur2.fetchone()
        while row != None:
            if row[0] not in accounts:
                cleanAccounts.append(row[0])
            row = cur2.fetchone()
    logging.info('{0} accounts have saved transactions'.format(len(cleanAccounts)))
    # clean tx data for inactive accounts except tavern sale/hires populated by block crawler
    with con.cursor() as cur3:
        for account in cleanAccounts:
            cur3.execute("SELECT expiresTimestamp FROM members WHERE account=%s", (account,))
            row3 = cur3.fetchone()
            if row3 == None or row3[0] == None or row3[0] < nowstamp:
                cur3.execute("DELETE FROM transactions WHERE account=%s and (eventType != 'tavern' or fee != 0)", (account,))
                logging.info('Cleaned {0} transactions for account {1}'.format(cur3.rowcount, account))
    
    con.close()


def main():
    # get in the right spot when running this so file paths can be managed relatively
    os.chdir(settings.WEB_ROOT)
    handler = logging.handlers.RotatingFileHandler('../maintenance.log', maxBytes=33554432, backupCount=10)
    logging.basicConfig(handlers=[handler], level=logging.INFO, format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # clean up old reports
    maxAgeDate = datetime.now() - timedelta(days=settings.MAX_REPORT_AGE_DAYS)
    logging.warning('Cleaning report records older than {0}'.format(maxAgeDate.isoformat()))
    cleanReports(datetime.timestamp(maxAgeDate))
    cleanTransactions()


if __name__ == "__main__":
	main()
