#!/usr/bin/env python3
# Maintenace module to periodically clear old generated report data
import db
import settings
import datetime
import logging
import logging.handlers
import os

def cleanReports(beforeTimestamp):
    con = db.aConn()
    cur = con.cursor()
    cur.execute("SELECT account, startDate, endDate, transactionsContent, reportContent FROM reports WHERE proc=0 and generatedTimestamp < %s", (beforeTimestamp,))
    row = cur.fetchone()
    while row != None:
        db.deleteReport(row[0], row[1], row[2], row[3], row[4])
        row = cur.fetchone()
    con.close()

def main():
    # get in the right spot when running this so file paths can be managed relatively
    os.chdir(settings.WEB_ROOT)
    handler = logging.handlers.RotatingFileHandler('../maintenance.log', maxBytes=33554432, backupCount=10)
    logging.basicConfig(handlers=[handler], level=logging.INFO, format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # clean up old reports
    maxAgeDate = datetime.datetime.now() - datetime.timedelta(days=settings.MAX_REPORT_AGE_DAYS)
    logging.warning('Cleaning report records older than {0}'.format(maxAgeDate.isoformat()))
    cleanReports(datetime.datetime.timestamp(maxAgeDate))


if __name__ == "__main__":
	main()
