"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
"""
import json
import os
import importlib
from configparser import ConfigParser
from urllib3.exceptions import ConnectionError, ConnectTimeoutError, HTTPError

from py2neo import Graph
from py2neo import ClientError, TransientError, DatabaseError

from ...constants import params as cs

# KMS Logger
kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(
            os.path.realpath(__file__)), '..', '..', 'config', 'configuration.ini'))

logger.info("=-------CONF PATH=%s", CONFIG_PATH)

# constants to store count of population
NODES_CREATED = 0
REL_CREATED = 0
TRIPLET = 3

# str constants for query stats
STR_NODES_CREATED = "nodes_created"
STR_REL_CREATED = "relationships_created"


class ErrorHandling(object): # pragma: no cover
    """
        class to handle neo4j errors
        neo4j py2neo major errors
        Refer:https://py2neo.org/v4/database.html#py2neo.database.DatabaseError
    """

    @classmethod
    def handle_error(cls, error):
        """
            class method classifies error and handles
            Args:
                error - py2neo error
            Returns:
                None
        """
        response = dict()
        resp_code = ""
        resp_msg = ""
        logger.info("Enter handle_error =%s", str(error))
        # isinstance(var, (classinfo1, classinfo2, classinfo3))
        if isinstance(error, (ClientError, TransientError, DatabaseError)):
            resp_code = cs.ResponseCode.CLIENT_ERROR
            resp_msg = error.message
            logger.error("py2neo error=%s", str(error))
        elif isinstance(error, (ConnectionError, ConnectTimeoutError, HTTPError)):
            resp_code = cs.ResponseCode.CONNECTION_ERROR
            resp_msg = cs.ResponseMsg.MSG_CONNECTION_ERROR
            logger.error("urllib3 HTTP error=%s", str(error))
        else:
            resp_code = cs.ResponseCode.INTERNAL_ERROR
            resp_msg = str(error)
            logger.error("Unknown error=%s", str(error))

        response[cs.resp_code] = resp_code
        response[cs.error_msg] = resp_msg
        logger.info("End handle_error =%s", str(response))
        return response


# neo4j database class
class Neo4jDB(object):
    """
        class function to read configuration file and connect to database
        server with credentials
        Args:
            None
        Returns:
            Neo4j graph database instance object
    """

    def __init__(self):
        try:
            global CONFIG_PATH
            read_config = ConfigParser()

            read_config.read(CONFIG_PATH)
            logger.debug("URL=(%s)" % read_config.get('database', 'url'))
            logger.debug("username=(%s)" % read_config.get('database', 'username'))
            logger.debug("password=(%s)" % read_config.get('database', 'password'))

            self.url = read_config.get('database', 'url')
            self.user = read_config.get('database', 'username')
            self.password = read_config.get('database', 'password')
            self.graph = Graph(self.url, auth=(self.user, self.password))
        except Exception as e:
            logger.exception("Init exception=%s", e)

    def run_query(self, querystr):
        """
            class method Executes cypher query in Neo4j graph database
            Args:
                querystr - str
            Returns:
                data - py2neo graph object
        """
        try:
            data = self.graph.run(querystr).data()
            return data, cs.ResponseCode.KER_INTERNAL_SUCCESS
        except Exception as e:
            logger.error("execute failed:", e)
            response = ErrorHandling.handle_error(e)
            logger.debug("error response : %s", response)
            return response, response[cs.resp_code]

    def __check_population_stats(self, stats_data): # pragma: no cover
        """
            class method parses cypher query statistics data and log important
            information
            Args:
                stats - list
            Returns:
                None
        """
        global NODES_CREATED, REL_CREATED
        no_of_nodes = 0
        no_of_rel = 0

        # TODO parse stats_data dictionary
        no_of_nodes = stats_data[STR_NODES_CREATED]
        no_of_rel = stats_data[STR_REL_CREATED]
        logger.debug("Each triplet nodes_created=%d rel_added=%d" % (no_of_nodes, no_of_rel))
        # check created node count for each triplet
        if no_of_nodes == 2:
            logger.info("New nodes created")
        elif (no_of_nodes > 0) and (no_of_nodes < 2):
            logger.info("Nodes exist")
        elif no_of_nodes == 0:
            logger.info("Check domain/range")

        # check created relationship count for each triplet
        if no_of_rel == 1:
            logger.info("New relation added")
        elif no_of_rel == 0:
            logger.info("Check relation")

        # add current created node , rel count for each triplet with global count for final response
        NODES_CREATED = NODES_CREATED + no_of_nodes
        REL_CREATED = REL_CREATED + no_of_rel

    def __get_population_resp(self, triplets): # pragma: no cover
        """
            class method to form final population response and status and
            returns as dictionary
            Args:
                triplets : list
            Returns:
                pop_resp : dict
        """
        global NODES_CREATED, REL_CREATED, TRIPLET

        len_triplets = len(triplets)
        pop_resp = dict()
        # fill the dictionary object with all population status
        pop_resp[cs.QueryStats.TOTAL_TRIPLETS] = len_triplets
        pop_resp[cs.QueryStats.TOTAL_NODES] = NODES_CREATED
        pop_resp[cs.QueryStats.TOTAL_RELATIONS] = REL_CREATED

        # log the count of nodes/relations
        logger.debug("Nodes Created {}".format(NODES_CREATED))
        logger.debug("Relationships Created {}".format(REL_CREATED))

        # check status of population
        if (len_triplets * TRIPLET) == (NODES_CREATED + REL_CREATED):
            logger.debug("Population count match")
            pop_resp[cs.QueryStats.POPU_STATUS] = cs.ResponseMsg.MSG_POPULATION_STATUS_OK
        else:
            pop_resp[cs.QueryStats.POPU_STATUS] = cs.ResponseMsg.MSG_POPULATION_STATUS_NOT_OK

        # clear the count of population status once we formed final response
        # for next set of query batch
        NODES_CREATED = 0
        REL_CREATED = 0

        logger.debug("popul final response=(%s)" % str(pop_resp))
        return pop_resp

    def execute(self, queries): # pragma: no cover
        """
            class method Executes cypher query in batch using transactions
            Args:
                queries - list
            Returns:
                response - json string
        """
        write_key = "MERGE"
        read_key = "MATCH"
        response = dict()
        data = []

        try:
            logger.info("Enter __execute_queries_as_batch")

            # create transaction
            tx = self.graph.begin()
            for query in queries:
                # execute cypher query
                query_res = tx.run(query)
                if write_key in query:
                    # pass query statistics and get the population count
                    data = dict(query_res.stats())
                    self.__check_population_stats(data)
                elif read_key in query:
                    data = query_res.data()
            # commit the transaction
            tx.commit()

            response[cs.resp_code] = cs.SUCCESS
            if read_key in query:
                response[cs.resp_data] = str(data)
            else:
                response[cs.resp_data] = self.__get_population_resp(queries)
            logger.debug("DB results=(%s)", str(data))
        except Exception as error:
            logger.exception("Exception in execute() return=(%s)", str(error))
            response = ErrorHandling.handle_error(error)
        finally:
            logger.debug("End execute() return=(%s)", json.dumps(response))
            return json.dumps(response)


if __name__ == "__main__": # pragma: no cover
    # logger configurtion
    logger.basicConfig(level=logger.DEBUG,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')
    obj = Neo4jDB()
    # test case for syntax error
    sample_query = ["MERGE(a:Model{name:WM3501H})"]
    result = obj.execute(sample_query)
    print(result)

    # test case for write & success
    sample_query = ["MERGE(a:Model{name:'WM9000H'}) MERGE(b:Product{name:'washer'}) MERGE(a)-[r:TypeOf]->(b)"]
    result = obj.execute(sample_query)
    print(result)

    # test case for read & success
    sample_query = ["MATCH(a:Model{name:'WM3501H'}) RETURN a"]
    result = obj.execute(sample_query)
    print(result)
