#!/usr/bin/env python3

import subprocess
import shlex
import time
import db
import logging

def main():
    logging.basicConfig(filename='../watch.log', level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    con = db.aConn()
    logging.info('Started report watcher.')
    while con.open:
        logging.debug('check for reports')
        with con.cursor() as cur:
            cur.execute("SELECT * FROM reports WHERE reportStatus=0 AND proc IS NULL")
            row = cur.fetchone()
        if row != None:
            logging.info('Starting report generation process for {0} {1} - {2} ({3})'.format(row[0], row[1], row[2], row[7]))
            with con.cursor() as cur2:
                logging.debug(cur2.mogrify("UPDATE reports SET proc=1 WHERE account=%s AND startDate=%s AND endDate=%s AND generatedTimestamp=%s", (row[0], row[1], row[2], row[3])))
                cur2.execute("UPDATE reports SET proc=1 WHERE account=%s AND startDate=%s AND endDate=%s", (row[0], row[1], row[2]))
            con.commit()
            logging.debug('kickoff proc')
            cmds = '../main.py {0} "{1}" "{2}" --costbasis {3}'.format(row[0], row[1], row[2], row[11])
            subprocess.Popen(shlex.split(cmds), start_new_session=True)
            logging.info('Started report generation process')
            time.sleep(1)
            logging.debug('done waiting 1s')
        else:
            logging.debug('No report records waiting')
        row = None
        time.sleep(2)
    con.close()

if __name__ == "__main__":
	main()