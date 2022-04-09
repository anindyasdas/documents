"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
"""
from neo4j import GraphDatabase
import logging as logger
import os
from configparser import ConfigParser
import json

# default is 30 seconds
CONNECTION_TIMEOUT = 15

# default is 30 seconds
TRANSACTION_RETRY_TIME = 15

# in milliseconds;
TRANSACTION_TIMEOUT = 100

from constants import params as cs
from knowledge.graph.neo4j_db import ErrorHandling

CONFIG_PATH = os.path.join('config', 'configuration.ini')


class Neo4jConnection:

    def __init__(self):
        global CONFIG_PATH
        read_config = ConfigParser()

        read_config.read(CONFIG_PATH)
        logger.debug("URL=(%s)" % read_config.get('database', 'url'))
        logger.debug("username=(%s)" % read_config.get('database', 'username'))
        logger.debug("password=(%s)" % read_config.get('database', 'password'))

        self.url = read_config.get('database', 'url')
        self.user = read_config.get('database', 'username')
        self.pwd = read_config.get('database', 'password')
        self.__driver = None
        try:
            # https://neo4j.com/docs/driver-manual/4.1/client-applications/#driver-authentication
            # create connection to neo4j database driver
            self.__driver = GraphDatabase.driver(self.url, auth=(self.user, self.pwd),
                                                 connection_timeout=CONNECTION_TIMEOUT,
                                                 max_transaction_retry_time=TRANSACTION_RETRY_TIME)
        except Exception as e:
            logger.error("Connection failed:", e)

    def close(self):
        """
            close the neo4j driver connection
            Args:
                None
            Returns:
                None
        """
        if self.__driver is not None:
            self.__driver.close()

    def execute_query(self, queries):
        """
            close the neo4j driver connection
            Args:
                queries - list of cypher query
            Returns:
                response - json string
        """
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        write_key = "MERGE"
        read_key = "MATCH"
        response = dict()
        data = []
        try:
            # session creation
            session = self.__driver.session()
            # create transaction with timeout
            # Transactions that execute longer than the configured timeout
            # will be terminated by the database
            tx = session.begin_transaction(timeout=TRANSACTION_TIMEOUT)
            for query in queries:
                # execute cypher query
                query_res = tx.run(query)
                if write_key in query:
                    # get query statistics return data
                    # TODO parse stats response and create stats response for batch of queries
                    data = query_res.stats()
                elif read_key in query:
                    data = query_res.data()
            # commit the transaction
            tx.commit()
            response[cs.resp_code] = cs.SUCCESS
            response[cs.resp_data] = str(data)
            logger.debug("DB results=(%s)", str(data))
        except Exception as error:
            logger.error("Exception in execute() return=(%s)", str(error))
            response = ErrorHandling.handle_error(error)
        finally:
            logger.info("End execute() return=(%s)", json.dumps(response))
            # session close
            if session is not None:
                session.close()
        return json.dumps(response)


if __name__ == "__main__":
    obj = Neo4jConnection()
    print("Main started")
    sample_query = "MATCH (a:Model) return a.name"
    response = obj.execute_query(sample_query)
    print(str(response))

    # test case for syntax error
    sample_query = ["MERGE(a:Model{name:WM3501H})"]
    result = obj.execute_query(sample_query)
    print(result)