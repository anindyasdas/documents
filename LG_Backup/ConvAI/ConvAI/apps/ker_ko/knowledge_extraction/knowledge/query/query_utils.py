"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
"""
from threading import Thread
import importlib
from ...constants import params as cs
from .query_constants import QueryConstants

# KMS Logger
kms_logger = importlib.import_module('kms_logger').KMSLogger()
logger = kms_logger.create_console_logger(__name__)
RESULTS = {}


class QueryEngine(object):
    """
    class defines method to generate priority levels of queries
    """
    __instance = None

    @staticmethod
    def get_instance(searchmethod):
        """ Static access method to get the singleton instance"""
        if QueryEngine.__instance == None:
            QueryEngine(searchmethod)
        return QueryEngine.__instance

    def __init__(self, searchmethod):
        """ Virtually private constructor. """
        if QueryEngine.__instance != None:
            raise Exception("QueryEngine is not instantiable")
        else:
            QueryEngine.__instance = self
            self.search_method = searchmethod
            if self.search_method == QueryConstants.UNWIND_SEARCH:
                self.query_utils_engine = UnwindSearch()
            else:
                self.query_utils_engine = ListSearch()

    def get_priority_based_cond_query(self, knowledge_dict):
        """
           calls method based on priority and returns query
           Args:
               knowledge_dict - extracted knowledge using srl,const parser
           Returns:
               queries : dict
        """
        queries = {}

        # get priority levels queries as dict
        queries = self.query_utils_engine.get_priority_based_cond_query(knowledge_dict)
        return queries


class ListSearch(object):
    """
        class defines method to generate priority levels of list based search queries
    """

    def __init__(self):
        pass

    def get_priority_based_cond_query(self, knowledge_dict):
        """
           constructs queries list based search and return as dict
           Args:
               knowledge_dict - extracted knowledge using srl,const parser
           Returns:
               queries : dict
        """
        queries = dict()
        # forms 4 priority levels queries
        key, query = self.__priority_1(knowledge_dict)
        queries[key] = query
        key, query = self.__priority_2(knowledge_dict)
        queries[key] = query
        key, query = self.__priority_3(knowledge_dict)
        queries[key] = query
        key, query = self.__priority_4(knowledge_dict)
        queries[key] = query
        return queries

    def __priority_1(self, knowledge_dict):
        """
           constructs query for priority 1
           Args:
               knowledge_dict - extracted knowledge using srl,const parser
           Returns:
               priority : str
               query_results : dict
        """
        mod_prop = ""
        logger.info("1 dict=(%s)" % (str(knowledge_dict)))
        for key, value in knowledge_dict.items():
            temp = ""
            for i in range(len(value)):
                if value[i] not in QueryConstants.QUERY_STOP_WORDS:
                    temp = ("'%s' in b.%s" % (value[i], key))
                    if (key == cs.ENTITY) or (key == cs.VERB):
                        mod_prop = QueryConstants.LOGICAL_AND.join([mod_prop, temp])
                    elif (key == cs.PURPOSE) or (key == cs.CAUSE) or (key == cs.TEMPORAL):
                        mod_prop = QueryConstants.LOGICAL_OR.join([mod_prop, temp])
        mod_prop = QueryConstants.WHERE_COND + mod_prop
        return QueryConstants.PRIOR_1, mod_prop

    def __priority_2(self, knowledge_dict):
        """
           constructs query for priority 2
           Args:
               knowledge_dict - extracted knowledge using srl,const parser
           Returns:
               priority : str
               query_results : dict
        """
        mod_prop = ""
        logger.info("2 dict=(%s)" % (str(knowledge_dict)))
        for key, value in knowledge_dict.items():
            temp = ""
            for i in range(len(value)):
                if value[i] not in QueryConstants.QUERY_STOP_WORDS:
                    temp = ("'%s' in b.%s" % (value[i], key))
                    if key == cs.ENTITY or key == cs.VERB:
                        mod_prop = QueryConstants.LOGICAL_AND.join([mod_prop, temp])
        mod_prop = QueryConstants.WHERE_COND + mod_prop
        return QueryConstants.PRIOR_2, mod_prop

    def __priority_3(self, knowledge_dict):
        """
           constructs query for priority 3
           Args:
               knowledge_dict - extracted knowledge using srl,const parser
           Returns:
               priority : str
               query_results : dict
        """
        mod_prop = ""
        for key, value in knowledge_dict.items():
            temp = ""
            for i in range(len(value)):
                if value[i] not in QueryConstants.QUERY_STOP_WORDS:
                    temp = ("'%s' in b.%s" % (value[i], key))
                    if key == cs.ENTITY:
                        mod_prop = QueryConstants.LOGICAL_OR.join([mod_prop, temp])
        mod_prop = QueryConstants.WHERE_COND + mod_prop
        return QueryConstants.PRIOR_3, mod_prop

    def __priority_4(self, knowledge_dict):
        """
           constructs query for priority 4
           Args:
               knowledge_dict - extracted knowledge using srl,const parser
           Returns:
               priority : str
               query_results : dict
        """
        mod_prop = ""
        for key, value in knowledge_dict.items():
            temp = ""
            for i in range(len(value)):
                if value[i] not in QueryConstants.QUERY_STOP_WORDS:
                    temp = ("'%s' in b.%s" % (value[i], key))
                    mod_prop = QueryConstants.LOGICAL_OR.join([mod_prop, temp])
        mod_prop = QueryConstants.WHERE_COND + mod_prop
        return QueryConstants.PRIOR_4, mod_prop


class UnwindSearch(object):
    """
        class defines method to generate priority levels of unwind based search queries
    """

    def __init__(self):
        pass

    def get_priority_based_cond_query(self, knowledge_dict):
        """
           constructs queries list based search and return as dict
           Args:
               knowledge_dict - extracted knowledge using srl,const parser
           Returns:
               queries : dict
        """
        queries = dict()
        # forms 4 priority levels queries
        key, query = self.__priority_unwind_1(knowledge_dict)
        queries[key] = query
        key, query = self.__priority_unwind_2(knowledge_dict)
        queries[key] = query
        key, query = self.__priority_unwind_3(knowledge_dict)
        queries[key] = query
        key, query = self.__priority_unwind_4(knowledge_dict)
        queries[key] = query
        return queries

    def __priority_unwind_1(self, knowledge_dict):
        """
           constructs query for priority 1
           Args:
               knowledge_dict - extracted knowledge using srl,const parser
           Returns:
               priority : str
               query_results : dict
        """
        mod_prop = ""
        unwind_query = ""
        with_query = ""

        logger.info("1 dict=(%s)" % (str(knowledge_dict)))
        with_condn = ",".join("%s" % (key) for key, value in
                              knowledge_dict.items())
        with_query = QueryConstants.WITH_KEYWORD + with_condn

        for key, value in knowledge_dict.items():
            temp = ""
            unwind_condn = QueryConstants.UNWIND_QUERY % (key, key)
            unwind_query = ''.join([unwind_query, unwind_condn])
            for i in range(len(value)):
                if value[i] not in QueryConstants.QUERY_STOP_WORDS:
                    temp = (QueryConstants.CASE_INSENSITIVE % (key, value[i]))
                    if (key == cs.ENTITY) or (key == cs.VERB):
                        mod_prop = QueryConstants.LOGICAL_AND.join([mod_prop, temp])
                    elif (key == cs.PURPOSE) or (key == cs.CAUSE) or (key == cs.TEMPORAL):
                        mod_prop = QueryConstants.LOGICAL_OR.join([mod_prop, temp])

        mod_prop = unwind_query + with_query + QueryConstants.WHERE_SUBSTR_COND + mod_prop
        return QueryConstants.PRIOR_1, mod_prop

    def __priority_unwind_2(self, knowledge_dict):
        """
           constructs query for priority 2
           Args:
               knowledge_dict - extracted knowledge using srl,const parser
           Returns:
               priority : str
               query_results : dict
        """
        mod_prop = ""
        unwind_query = ""
        with_query = ""

        logger.info("2 dict=(%s)" % (str(knowledge_dict)))
        with_condn = ",".join("%s" % (key) for key in [cs.ENTITY, cs.VERB])
        with_query = QueryConstants.WITH_KEYWORD + with_condn
        for key, value in knowledge_dict.items():
            temp = ""
            if (key == cs.ENTITY) or (key == cs.VERB):
                unwind_condn = QueryConstants.UNWIND_QUERY % (key, key)
                unwind_query = ''.join([unwind_query, unwind_condn])
            for i in range(len(value)):
                if value[i] not in QueryConstants.QUERY_STOP_WORDS:
                    temp = (QueryConstants.CASE_INSENSITIVE % (key, value[i]))
                    if key == cs.ENTITY or key == cs.VERB:
                        mod_prop = QueryConstants.LOGICAL_AND.join([mod_prop, temp])
        mod_prop = unwind_query + with_query + QueryConstants.WHERE_SUBSTR_COND + mod_prop
        return QueryConstants.PRIOR_2, mod_prop

    def __priority_unwind_3(self, knowledge_dict):
        """
           constructs query for priority 3
           Args:
               knowledge_dict - extracted knowledge using srl,const parser
           Returns:
               priority : str
               query_results : dict
        """
        mod_prop = ""
        unwind_query = ""
        with_query = ""

        logger.info("2 dict=(%s)" % (str(knowledge_dict)))
        with_condn = ",".join("%s" % (key) for key in [cs.ENTITY])
        with_query = QueryConstants.WITH_KEYWORD + with_condn
        for key, value in knowledge_dict.items():
            temp = ""
            if (key == cs.ENTITY):
                unwind_condn = QueryConstants.UNWIND_QUERY % (key, key)
                unwind_query = ''.join([unwind_query, unwind_condn])
            for i in range(len(value)):
                if value[i] not in QueryConstants.QUERY_STOP_WORDS:
                    temp = (QueryConstants.CASE_INSENSITIVE % (key, value[i]))
                    if key == cs.ENTITY:
                        mod_prop = QueryConstants.LOGICAL_OR.join([mod_prop, temp])
        mod_prop = unwind_query + with_query + QueryConstants.WHERE_SUBSTR_COND + mod_prop
        return QueryConstants.PRIOR_3, mod_prop

    def __priority_unwind_4(self, knowledge_dict):
        """
           constructs query for priority 1
           Args:
               knowledge_dict - extracted knowledge using srl,const parser
           Returns:
               priority : str
               query_results : dict
        """
        mod_prop = ""
        unwind_query = ""
        with_query = ""

        logger.info("1 dict=(%s)" % (str(knowledge_dict)))
        with_condn = ",".join("%s" % (key) for key, value in
                              knowledge_dict.items())
        with_query = QueryConstants.WITH_KEYWORD + with_condn
        for key, value in knowledge_dict.items():
            temp = ""
            if (key == cs.ENTITY) or (key == cs.VERB) or (key == cs.PURPOSE) or (key == cs.CAUSE) or \
                    (key == cs.TEMPORAL):
                unwind_condn = QueryConstants.UNWIND_QUERY % (key, key)
                unwind_query = ''.join([unwind_query, unwind_condn])
            for i in range(len(value)):
                if value[i] not in QueryConstants.QUERY_STOP_WORDS:
                    temp = (QueryConstants.CASE_INSENSITIVE % (key, value[i]))
                    mod_prop = QueryConstants.LOGICAL_OR.join([mod_prop, temp])
        mod_prop = unwind_query + with_query + QueryConstants.WHERE_SUBSTR_COND + mod_prop
        return QueryConstants.PRIOR_4, mod_prop


def execute_query(priority, query, graph):
    """
       executes query and returns the results
       Args:
           priority : priority_level
           query : cypher query
           graph : py2neo object
       Returns:
           priority : str
           query_results : dict
    """
    try:
        query_results = graph.run_query(query)
        RESULTS[priority] = query_results
    except Exception as e:
        logger.error(e)

    return True


def query_parallel_execution(graph, query_list):
    """
       executes query in parallel using threads and returns the results
       Args:
           graph : py2neo object
           query_list : list of dictionary with priority and queries
       Returns:
          result : list of results
    """
    # create a list of threads
    threads = []
    result = None
    for key, value in query_list.items():
        process = Thread(target=execute_query, args=[key, value, graph])
        process.start()
        threads.append(process)

    # This ensures that each has finished processing the urls.
    for process in threads:
        process.join()

    logger.info("Global results:%s", str(RESULTS))

    # check results and returns the answer based on priority
    if len(RESULTS[QueryConstants.PRIOR_1]) > 0:
        result = RESULTS[QueryConstants.PRIOR_1]
    elif len(RESULTS[QueryConstants.PRIOR_2]) > 0:
        result = RESULTS[QueryConstants.PRIOR_2]
    elif len(RESULTS[QueryConstants.PRIOR_3]) > 0:
        result = RESULTS[QueryConstants.PRIOR_3]
    elif len(RESULTS[QueryConstants.PRIOR_4]) > 0:
        result = RESULTS[QueryConstants.PRIOR_4]
    logger.info("Result from query_utils=(%s)", str(result))
    return result


if __name__ == "__main__":
    knowledge_dict = dict()
    knowledge_dict[cs.ENTITY] = ['water inlet hoses']
    knowledge_dict[cs.VERB] = ['kinked', 'pinched', 'resolve']
    knowledge_dict[cs.PURPOSE] = ['clog']
    knowledge_dict[cs.CAUSE] = ['pinch']
    knowledge_dict[cs.TEMPORAL] = ['next time']
    # call for list item search
    s = QueryEngine.get_instance(QueryConstants.LIST_SEARCH)
    # call for sub string search in list
    # s = QueryEngine.get_instance(QueryConstants.UNWIND_SEARCH)
    query_list = s.get_priority_based_cond_query(knowledge_dict)
    print(query_list)