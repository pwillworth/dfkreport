#!/usr/bin/env python3
import os
import subprocess
import shlex
import time
import db
import settings
from datetime import datetime, timezone
import logging

def main():
    logging.basicConfig(filename='watch.log', level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    con = db.aConn()
    logging.info('Started wallet watcher.')
    updateInterval = 86400
    pollInterval = 10
    row = None
    while True:
        if con != None and con.closed == 0:
            logging.debug('check for updates needed')
            with con.cursor() as cur:
                if row == None:
                    try:
                        checkTime = datetime.now(timezone.utc).timestamp()
                        if settings.WATCH_FORCE_UPDATE and settings.WATCH_DAILY_UPDATE:
                            cur.execute("SELECT address, lastOwner, network, proc, updateStatus, fromIP FROM walletstatus LEFT JOIN members ON walletstatus.lastOwner = members.account WHERE proc IS NULL AND (lastUpdateStart IS NULL OR (expiresTimestamp > %s AND lastUpdateStart < %s AND network != 'harmony'))", (checkTime, checkTime - updateInterval))
                        elif settings.WATCH_FORCE_UPDATE:
                            cur.execute("SELECT address, lastOwner, network, proc, updateStatus, fromIP FROM walletstatus WHERE proc IS NULL AND lastUpdateStart IS NULL")
                        elif settings.WATCH_DAILY_UPDATE:
                            cur.execute("SELECT address, lastOwner, network, proc, updateStatus, fromIP FROM walletstatus LEFT JOIN members ON walletstatus.lastOwner = members.account WHERE proc IS NULL AND (expiresTimestamp > %s AND lastUpdateStart < %s AND network != 'harmony')", (checkTime, checkTime - updateInterval))
                        else:
                            row = None
                        row = cur.fetchone()
                    except Exception as err:
                        logging.error('report lookup db failure {0}'.format(str(err)))
                        row = None
                if row != None:
                    try:
                        reportCount = db.getRunningUpdates()
                    except Exception as err:
                        logging.error('db error looking up running reports {0}'.format(str(err)))
                        reportCount = 99999
                    logging.info("update needed for {2} - {3}, running reports: {0} max reports: {1}".format(reportCount, settings.MAX_REPORTS, row[0], row[2]))
                    if reportCount < settings.MAX_REPORTS:
                        with con.cursor() as cur2:
                            # dont start yet if existing process running from same IP and network
                            cur2.execute("SELECT address FROM walletstatus WHERE proc=1 AND network=%s AND (fromIP=%s OR lastOwner=%s)", (row[2], row[5], row[1]))
                            row2 = cur2.fetchone()
                            if settings.CONCURRENT_REPORTS == False and row2 != None and row2[0] != None:
                                logging.info("Skipping {0} {1} update same user has update already running.".format(row[2], row[1]))
                                time.sleep(pollInterval)
                                row = cur.fetchone()
                                continue
                            logging.debug(cur2.mogrify("UPDATE walletstatus SET proc=1, lastUpdateStart=%s WHERE address=%s AND network=%s", (checkTime, row[0], row[2])))
                            cur2.execute("UPDATE walletstatus SET proc=1, lastUpdateStart=%s WHERE address=%s AND network=%s", (checkTime, row[0], row[2]))
                        con.commit()
                        logging.info('starting main.py {0} --network {1}'.format(row[0], row[2]))
                        cmds = './main.py {0} --network {1}'.format(row[0], row[2])
                        subprocess.Popen(shlex.split(cmds), start_new_session=True)
                        time.sleep(1)
                    elif settings.MAX_REPORTS > 1 and reportCount >= settings.MAX_REPORTS:
                        db.updateReportError(row[0], row[2], 7)
                        logging.info('Update report too busy for {0}'.format(row[0]))
                    else:
                        logging.warning('Minimal node ignoring report request.')
                else:
                    logging.info('No report records waiting')
        else:
            try:
                con = db.aConn()
            except Exception as err:
                logging.error('DB connection failure, will try again in next loop.'.format(str(err)))
        row = None
        time.sleep(pollInterval)
    con.close()

if __name__ == "__main__":
    # get in the right spot when running this so file paths can be managed relatively
    location = os.path.abspath(__file__)
    os.chdir('/'.join(location.split('/')[0:-1]))
    main()