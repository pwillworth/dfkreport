#!/usr/bin/env python3
import os
import subprocess
import shlex
import time
import db
import settings
import logging

def main():
    logging.basicConfig(filename='watch.log', level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    con = db.aConn()
    logging.info('Started report watcher.')
    while True:
        if con != None and con.closed == 0:
            logging.debug('check for reports')
            with con.cursor() as cur:
                try:
                    cur.execute("SELECT account, startDate, endDate, generatedTimestamp, costBasis, includedChains, walletGroup, walletHash FROM reports WHERE reportStatus=0 AND proc IS NULL")
                    row = cur.fetchone()
                except Exception as err:
                    logging.error('report lookup db failure {0}'.format(str(err)))
                    row = None
            if row != None:
                try:
                    reportCount = db.getRunningReports()
                except Exception as err:
                    logging.error('db error looking up running reports {0}'.format(str(err)))
                    reportCount = 99999
                if reportCount < settings.MAX_REPORTS:
                    logging.info('starting main.py {0} "{1}" "{2}" --costbasis {3} --chains {4} --wallets {5}'.format(row[0], row[1], row[2], row[4], row[5], row[7]))
                    with con.cursor() as cur2:
                        logging.debug(cur2.mogrify("UPDATE reports SET proc=1 WHERE account=%s AND startDate=%s AND endDate=%s AND generatedTimestamp=%s", (row[0], row[1], row[2], row[3])))
                        cur2.execute("UPDATE reports SET proc=1 WHERE account=%s AND startDate=%s AND endDate=%s AND generatedTimestamp=%s", (row[0], row[1], row[2], row[3]))
                    con.commit()
                    logging.debug('kickoff proc')
                    cmds = './main.py {0} "{1}" "{2}" --costbasis {3} --chains {4} --wallets {5}'.format(row[0], row[1], row[2], row[4], row[5], row[7])
                    subprocess.Popen(shlex.split(cmds), start_new_session=True)
                    time.sleep(1)
                else:
                    db.updateReportError(row[0], row[1], row[2], row[7], 7)
                    logging.info('Update report too busy for {0}'.format(row[0]))
            else:
                logging.debug('No report records waiting')
        else:
            try:
                con = db.aConn()
            except Exception as err:
                logging.error('DB connection failure, will try again in next loop.'.format(str(err)))
        row = None
        time.sleep(2)
    con.close()

if __name__ == "__main__":
    # get in the right spot when running this so file paths can be managed relatively
    location = os.path.abspath(__file__)
    os.chdir('/'.join(location.split('/')[0:-1]))
    main()