# -*- coding: utf-8 -*-
from logzero import logger
import time
import random
import calendar
import pymqi
from mysql import connector
from chaoslib.types import Configuration

# import simplejson as json


__all__ = ["probe_mysql", "probe_mq"]


def probe_mq(
        mgr: str,
        channel: str,
        queue_name: str,
        host: str = None,
        port: str = None,
        action: str = "put_get",
        number_of_messages: int = 1,
        configuration: Configuration = None
) -> int:
    """
    Probe to test MQ via putting and getting random messages
        "probes": [
            {
                "type": "probe",
                "name": "Check the a MQ is running",
                "tolerance": 0,
                "provider": {
                    "type": "python",
                    "module": "ibmcloud.middleware.probes",
                    "func": "probe_mq",
                    "arguments": {
                        "mgr": "HAEXAMPLE",
                        "channel": "HAQMCH",
                        "queue_name":"EXAMPLE.QUEUE",
                        "action": "put"
                        "number_of_messages": 1
                    }
                }
            }
        ]
    attr mgr str: queue manager name
    attr channel str: channel name
    attr host str: host name IP or Hostname
    attr port str: Port number to be passed as string
    attr queue_name str : Queue name it must be created before running this test
    attr action str: put/get/put_get
    attr number_of_messages int: number of messages to be sent
    :return: number of errors
    """
    _host = None
    _port = None
    if configuration is None:
        _host = host
        _port = port
    else:
        _host = configuration['mq_host'] if host is None else host
        _port = configuration['mq_port'] if port is None else port
    qmgr = pymqi.connect(mgr, channel, '%s(%s)' % (_host, _port))
    if action == "put" or action == "put_get":
        putq = pymqi.Queue(qmgr, queue_name)
        for _ in range(number_of_messages):
            putq.put('Hello from Python!')
        putq.close()

    if action == "get" or action == "put_get":
        getq = pymqi.Queue(qmgr, 'EXAMPLE.QUEUE')
        for _ in range(number_of_messages):
            getq.get()
        getq.close()
    return 0


def probe_mysql(host: str,
                user: str,
                password: str,
                iteration: int = 10,
                retries: int = 1) -> int:
    """
    Probe Mysql instance via sending insertion and selection
        "probes": [
            {
                "type": "probe",
                "name": "Check the a mq is running",
                "tolerance": 0,
                "provider": {
                    "type": "python",
                    "module": "ibmcloud.middleware.probes",
                    "func": "probe_mq",
                    "arguments": {
                        "host": "<IP/Host>",
                        "user": "<username>",
                        "password": "<password>",
                        "iteration": 10
                    }
                }
            }
        ]
    attr host str: IP/Host name
    attr user str: username for mysql
    attr password str : password for mysql
    attr iteration int : number of records to be inserted to and deleted
    attr retries int: number of retries
    :return: number of errors
    """
    errors = 0
    connection_retry = 0
    while connection_retry < retries:
        try:
            mysqldb = connector.connect(host=host, user=user, password=password)
            dbcursor = mysqldb.cursor()
            dbcursor.execute("CREATE DATABASE IF NOT EXISTS chaostest")
            dbcursor.execute("USE chaostest")
            dbcursor.execute(
                "CREATE TABLE IF NOT EXISTS test(ID int NOT NULL, name VARCHAR(255), address VARCHAR(255), "
                "PRIMARY KEY(ID))")
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
        # delete_sql = "Delete from test where ID = %s"

        for _ in range(iteration):
            i = random.randint(0, calendar.timegm(time.gmtime()))
            time.sleep(0.2)
            try:
                dbcursor.execute(insert_sql, (i, "name" + str(i), "address" + str(i)))
                mysqldb.commit()
            except Exception as e:
                logger.error("Error with Insertion : %s", e)
                errors = errors + 1
            try:
                dbcursor.execute(select_sql, (i,))
                dbcursor.fetchall()
            except Exception as e:
                logger.error("Error with select : %s", e)
                errors = errors + 1
            #    with open('de-attach-volume-ha-proxy.csv', 'a') as fd:
    #        line = str(connection_retry) + ", "+ str(errors) + '\n'
    #        fd.write(line)
    return errors
