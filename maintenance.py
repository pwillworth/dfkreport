#!/usr/bin/env python3
# Maintenace module to periodically clear old generated report data
import db
from datetime import datetime, timezone
import logging
import logging.handlers
import jsonpickle


def getActiveAccountWallets():
    wallets = []
    nowstamp = int(datetime.now(timezone.utc).timestamp())
    con = db.aConn()
    # assemble array of all wallet addresses in all wallet groups of active members
    with con.cursor() as cur:
        cur.execute("SELECT account FROM members WHERE expiresTimestamp > %s", (nowstamp,))
        row = cur.fetchone()
        while row != None:
            with con.cursor() as cur2:
                cur2.execute("SELECT wallets FROM groups WHERE account=%s", (row[0],))
                row2 = cur2.fetchone()
                while row2 != None:
                    wallets.append(jsonpickle.decode(row2[0]))
                    row2 = cur2.fetchone()
            row = cur.fetchone()
    con.close()
    return wallets

# Delete saved transaction data for any account that has not run a report recently enough to still be saved
def cleanTransactions():
    accounts = []
    cleanAccounts = []
    nowstamp = int(datetime.now(timezone.utc).timestamp())
    con = db.aConn()
    # Get list of accounts with active reports
    with con.cursor() as cur:
        cur.execute("SELECT DISTINCT account FROM reports")
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
    activeWallets = getActiveAccountWallets()
    with con.cursor() as cur3:
        for account in cleanAccounts:
            if account not in activeWallets:
                cur3.execute("DELETE FROM transactions WHERE account=%s and (eventType != 'tavern' or fee != 0)", (account,))
                logging.info('Cleaned {0} transactions for account {1}'.format(cur3.rowcount, account))
    
    con.close()


def main():
    # get in the right spot when running this so file paths can be managed relatively
    handler = logging.handlers.RotatingFileHandler('maintenance.log', maxBytes=33554432, backupCount=10)
    logging.basicConfig(handlers=[handler], level=logging.INFO, format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # clean up old tx
    cleanTransactions()


if __name__ == "__main__":
	main()
