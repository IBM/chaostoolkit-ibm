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
            mydb = connector.connect(host = host, user = user, password = password)
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

    insert_sql = "INSERT INTO test (ID ,name, address) VALUES (%s ,%s, %s)"
    select_sql = "SELECT * FROM test where ID = %s"
    delete_sql = "Delete from table wher ID = %s"

    for i in range(iteration):
        try:
            mycursor.execute(insert_sql, (i,"name"+str(i), "address"+str(i)))
            mydb.commit()
        except Exception as e:
            logger.error("Error with Insertion : %s", e)
            errors = errors + 1

        time.sleep(1)        
        try:
            mycursor.execute(select_sql, (i, ))
            mycursor.fetchall()
        except Exception as e:
            logger.error("Error with select : %s", e)
            errors = errors + 1   

        try:
            mycursor.executee(delete_sql, (i, ))
            mycursor.execute()
        except Exception as e:
            logger.error("Error with Deletetion: %s", e)
            errors = errors +  1

    return errors
