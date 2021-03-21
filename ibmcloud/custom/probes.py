# -*- coding: utf-8 -*-
from logzero import logger
from mysql import connector
import time
import random
import calendar
#import simplejson as json


__all__ = ["probe_mysql"]


def probe_mysql ( host: str,
                  user: str,
                  password: str,
                  iteration: int = 10,
                  retries: int = 1) -> int:

    """
    Probe used to quickly test CRUD in a database
    """
    errors = 0
    connection_retry = 0
    while connection_retry < retries:
        try:
            mydb = connector.connect(host = host, user = user, password = password)
            mycursor = mydb.cursor()
            mycursor.execute("CREATE DATABASE IF NOT EXISTS chaostest")
            mycursor.execute("USE chaostest")
            mycursor.execute("CREATE TABLE IF NOT EXISTS test(ID int NOT NULL, name VARCHAR(255), address VARCHAR(255), PRIMARY KEY(ID))")            
            break
        except:
            logger.warn(f"Failed to connect to DB  after %s tries", errors)
            connection_retry = connection_retry + 1
            errors = errors + 1
        time.sleep(1)
        
    if connection_retry >= retries:
        logger.error(f"Failed to connect to DB  after %s tries", errors)
    else:
        insert_sql = "INSERT INTO test (ID ,name, address) values (%s, %s, %s)"
        select_sql = "SELECT * FROM test where ID = %s"
        #delete_sql = "Delete from test where ID = %s"

        for j in range(iteration):
            i = random.randint(0, calendar.timegm(time.gmtime()))
            time.sleep(0.2)
            try:
                mycursor.execute(insert_sql, (i,"name"+str(i), "address"+str(i)))
                mydb.commit()
            except Exception as e:
                logger.error("Error with Insertion : %s", e)
                errors = errors + 1
            try:
                mycursor.execute(select_sql, (i, ))
                mycursor.fetchall()
            except Exception as e:
                logger.error("Error with select : %s", e)
                errors = errors + 1   
#    with open('de-attach-volume-ha-proxy.csv', 'a') as fd:
#        line = str(connection_retry) + ", "+ str(errors) + '\n'
#        fd.write(line)
    return errors
