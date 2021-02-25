# -*- coding: utf-8 -*-
from logzero import logger
from mysql import connector
import time
#import simplejson as json


__all__ = ["probe_mysql"]


def probe_mysql ( host: str,
                  user: str,
                  password: str,
                  iteration: int = 10) -> int:

    """
    Probe used to quickly test CRUD in a database
    """
    errors = 0
    while errors < 5:
        try:
            mydb = connector.connect(host = "host", user = user, password = password)
            break
        except:
            logger.warn(f"Failed to connect to DB  after %s tries", errors)
            errors = errors + 1
        time.sleep(5)
    if errors >= 5:
        logger.error(f"Failed to connect to DB  after %s tries", errors)
        return errors
    mycursor = mydb.cursor()
    mycursor.execute("CREATE DATABASE IF NOT EXISTS chaostest")
    mycursor.execute("USE chaostest")
    mycursor.execute("DROP table IF EXISTS test")
    mycursor.execute("CREATE TABLE IF NOT EXISTS test(ID int NOT NULL, name VARCHAR(255), address VARCHAR(255), PRIMARY KEY(ID))")

    sql = "INSERT INTO test (ID ,name, address) VALUES (%s ,%s, %s)"

    for i in range(iteration):
        val = (i,"name"+str(i), "address"+str(i))
        try:
            mycursor.execute(sql, val)
            mydb.commit()
        except:
            errors = errors + 1


    return errors
