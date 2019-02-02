#!/user/bin/env python
import os
import sys
import sqlite3
import workflowCollector as wc

CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')

def main():

    config = wc.get_yamlconfig(CONFIG_FILE_PATH)
    if not config:
        sys.exit('Config file: {} not exist, exiting..'.format(CONFIG_FILE_PATH))
    dbPath = config.get(
        'workflow_status_db',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'workflow_status.sqlite')
        )

    conn = sqlite3.connect(dbPath)
    with conn:
        c = conn.cursor()
        for row in c.execute("SELECT * FROM workflowStatuses"):
            print('[ {0:^12} ]\t{1}'.format(row[1], row[0]))

if __name__ == "__main__":
    main()