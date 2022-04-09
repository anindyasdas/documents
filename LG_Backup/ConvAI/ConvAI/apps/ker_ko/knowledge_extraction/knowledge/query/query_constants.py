"""
/*-------------------------------------------------
* Copyright(c) 2020-2022 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""


class QueryConstants(object):
    """
    section constants used for cypher queries
    """
    LIST_SEARCH = "list"
    UNWIND_SEARCH = "unwind"

    # query priority levels
    PRIOR_1 = "priority_1"
    PRIOR_2 = "priority_2"
    PRIOR_3 = "priority_3"
    PRIOR_4 = "priority_4"

    # logical operators
    LOGICAL_AND = " AND "
    LOGICAL_OR = " OR "

    # words need not be considered for retrieval
    QUERY_STOP_WORDS = ['solution', 'soln', 'resolve', 'resolution', 'fix', 'cause',
                        'reason', 'trigger', 'problem', 'issue']

    # constants used for partial search
    UNWIND_QUERY = " UNWIND b.%s as %s "
    CASE_INSENSITIVE = "toLower(%s) contains toLower('%s')"
    WITH_KEYWORD = "with "
    WHERE_SUBSTR_COND = ",b,c where "
    WHERE_COND = " WHERE "

    # query to return all part numbers
    RETRIEVE_ALL_PART_NOS = """MATCH(a:PartNumber)-[r:TypeOf]->(b:Product) WITH DISTINCT a.Name as part_nos,b.Name
                           as product_type,b.sub_product_type as sub_product_type ORDER BY part_nos return product_type ,sub_product_type,COLLECT(part_nos) as value"""

    # query to return models for a product
    RETRIEVE_PROD_PART_NOS = """MATCH(a:PartNumber)-[r:TypeOf]->(b:Product{Name:'%s'}) WITH DISTINCT a.Name as part_nos,b.Name
                            as product_type ORDER BY part_nos return product_type ,COLLECT(part_nos) as value"""

    # query to get product type
    RETRIEVE_PROD_TYPE = """MATCH(a:PartNumber{Name:'%s'})-[r:TypeOf]->(b) return b.Name as value"""

    # query to get part number
    RETRIEVE_PART_NUMBER = """MATCH(a:Model{{Name:"{model_number}"}})-[:HAS_PART_NUMBER]->(part) return part.Name as value"""

class SpecQuery(object):
    """
    This class contains all the constants related to
    Cypher Query for Specification
    """
    MATCH_MODEL_PART_NUMBERS = """MATCH(a:Model{{Name:"{model_number}"}})-[:HAS_PART_NUMBER]->(part)  
                            WITH COLLECT(part.Name) as part_nos"""
    RETRIEVE_NODE_OLD = """MATCH(a:%s{Name:"%s"})-[r:%s]->(b) RETURN b as value"""
    RETRIEVE_NODE = """MATCH s = (a)-[r:{specification_type}]->(b) 
                            WHERE all(r IN relationships(s) WHERE 
                            r.part_number IN part_nos)
                            RETURN b as value"""
    RETRIEVE_SPECIFIC_PARAM_OLD = """MATCH(a:%s{Name:"%s"})-[r:%s{%s}]->(b) 
                                  RETURN b as value,r as relation"""

    RETRIEVE_SPECIFIC_PARAM = """MATCH s = (a)-[r:{specification_type}{{{specification_property}}}]->(b) 
                                    WHERE all(r IN relationships(s) WHERE 
                                    r.part_number IN part_nos)
                                    RETURN b as value,r as relation"""


class TrobQuery(object):
    """
    This class contains all the constants related to
    Cypher Query for troubleshooting
    """
    MATCH_PART_NUMBER = """MATCH(a:PartNumber{{Name:"{part_number}"}}) WITH COLLECT(a.Name) as part_nos, a """

    # Should always be preceded by MATCH_MODEL_PART_NUMBERS
    MATCH_FAQ_NODE = """MATCH f = (a)-[:HAS_QUESTION]->(b:Question)-
                            [:HAS_SOLUTION]->(c) WHERE apoc.text.compareCleaned(b.Name, "{faq_question}")
                            AND all(r IN relationships(f) WHERE 
                            r.part_number IN part_nos AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))"""

    MATCH_SPECIFIC_CAUSE = """MATCH t = (a)-[r1:{problem_type}]->(b:Cause)-[:HAS_SOLUTION]->(c) 
                             WHERE apoc.text.compareCleaned(r1.{property_key}, "{property_value}")
                             AND apoc.text.compareCleaned(b.Name, "{specific_cause}") AND 
                             all(r IN relationships(t) WHERE 
                             r.part_number IN part_nos AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))"""

    MATCH_SPECIFIC_PROBLEM = """MATCH t = (a)-[r1:{problem_type}]->(b:Cause)-[:HAS_SOLUTION]->(c) 
                              WHERE apoc.text.compareCleaned(r1.{property_key}, "{property_value}") 
                              AND all(r IN relationships(t) WHERE 
                              r.part_number IN part_nos AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))
                              """

    RETRIEVE_DIAG_BEEP_PROB = """MATCH t = (a)-[r1:DIAGNOSE_WITH_BEEP]->(b)-[:HAS_PROCEDURE]->(c) 
                                WHERE all(r IN relationships(t) WHERE 
                                r.part_number IN part_nos AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))
                                WITH r1, part_nos, c ORDER BY c.step_no
                                OPTIONAL MATCH i = (c)-[:HAS_IMAGE]->(d)
                                WHERE all(r IN relationships(i) WHERE 
                                r.part_number IN part_nos AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))
                                RETURN DISTINCT c.Name as reason,c.desc as solution,
                                d.file_path as mediaUrl,d.file_type as mediaContentType,d.size as mediaFileSize"""

    RETRIEVE_DIAG_THINQ = """MATCH t = (a)-[:DIAGNOSE_WITH_LG_THINQ]->(b)  
                                 WHERE all(r IN relationships(t) WHERE 
                                 r.part_number IN part_nos AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))
                                 RETURN DISTINCT b.Name as reason,b.desc as solution"""
    RETRIEVE_ALL_TS_CAUSES = """
                MATCH t = (a)-[r1]->(b:Cause) WHERE all(r IN relationships(t) 
                WHERE r.part_number IN part_nos AND any(x IN {entity_type} WHERE x IN r.entity_prd_type)) 
                WITH  COLLECT(DISTINCT b.Name)+ COLLECT(DISTINCT r1.problem)+ COLLECT(DISTINCT r1.noise)+ 
                COLLECT(DISTINCT r1.error_code) as reason RETURN reason
                """

    MATCH_ALL_CAUSE = """MATCH(a:%s{Name:"%s"})-[r:%s]->(b:Cause)-[:%s]->(c:Solution) """
    RETURN_SOLUTION = """ RETURN DISTINCT c.Name as solution"""
    RETURN_CAUSE = """ RETURN DISTINCT b.Name as reason"""
    RETURN_CAUSE_SOLUTION = """ RETURN DISTINCT b.Name as reason,c.Name as solution"""


class OperationQuery(object):
    """
    This class contains all the constants related to
    Cypher Query for operation section
    """
    # queries for full text index
    DROP_FULLTEXT_INDEX = """CALL db.index.fulltext.drop("search")"""
    # TODO Include Procedure and Values (for extra info)
    CREATE_FULLTEXT_INDEX = """CALL db.index.fulltext.createNodeIndex("search",["OperationSubSection","Feature"],
                                ["Name"],{ analyzer: "cjk"})"""
    # { will be escaped by {{ in formatted strings
    # This will return list of 'op_sections' and its types as 'op_sections_type' based on the 'search_query' filtered
    # that 'model_number'
    # Should have 'model_number' and 'search_query' as inputs
    # This will query full text search nodes for that particular model
    SEARCH_FULLTEXT_INDEX = """MATCH (n:Model{{Name:"{model_number}"}})-[:HAS_PART_NUMBER]->(part) 
                                WITH COLLECT(part.Name) as part_nos 
                                CALL db.index.fulltext.queryNodes("search", "{search_query}") YIELD node, score 
                                WITH node.Name as listA, score as sc, part_nos as ps 
                                MATCH p = (n:Model{{Name:"{model_number}"}})-->()-[:HAS_SUB_SECTION|HAS_FEATURE*]->(b) 
                                WHERE b.Name in listA AND all(r IN relationships(p) WHERE r.part_number IN ps) 
                                WITH COLLECT(b.Name) as matched_nodes,COLLECT(labels(b)[0]) as node_labels
                                RETURN matched_nodes as op_sections, node_labels as op_sections_type"""

    # New Queries

    # To match L1 nodes
    # a = Model
    # b = OperationSection OR OperationSubSection
    # d = Image
    # e = Procedure
    # fe = Feature

    # Variables: model_number, operation_section, operation_sub_section, entity_type
    MATCH_PART_NUMBER = """MATCH(a:Model{{Name:"{model_number}"}})-[:HAS_PART_NUMBER]->(part)  
                           WITH COLLECT(part.Name) as part_nos, a """

    OPERATION_SECTION = """MATCH o = (a)-[:HAS_OPERATION_SECTION|HAS_SUB_SECTION*1..2]->(b) 
                    WHERE toLower(b.Name) contains toLower("{operation_section}")
                    AND all(r IN relationships(o) WHERE r.part_number IN part_nos 
                    AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))"""

    OPERATION_SUB_SECTION = """MATCH o = (a)-[:HAS_OPERATION_SECTION|HAS_SUB_SECTION*1..2]->(c)-[:HAS_SUB_SECTION|HAS_FEATURE*]->(b) 
                            WHERE toLower(c.Name) contains toLower("{operation_section}")
                            AND toLower(b.Name) contains toLower("{operation_sub_section}")
                            AND all(r IN relationships(o) WHERE r.part_number IN part_nos 
                            AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))"""

    FULL_TEXT_SEARCH_SECTION = """MATCH o = (a)-[:HAS_SUB_SECTION|HAS_FEATURE*]->(b)
                    WHERE toLower(b.Name) contains toLower("{operation_sub_section}")
                    AND all(r IN relationships(o) WHERE r.part_number IN part_nos 
                    AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))"""

    # Image query for Operation Sections and SubSections
    IMAGE_QUERY = """WITH b, part_nos 
                    OPTIONAL MATCH i = (b)-[:HAS_IMAGE]->(image) WHERE all(r IN relationships(i) WHERE r.part_number IN part_nos 
                    AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))
                    """
    SUB_SECTION_IMAGE_QUERY = """WITH b, part_nos, [b,c] as sec_sub_sec_nodes
                    OPTIONAL MATCH i = (n)-[:HAS_IMAGE]->(image) WHERE n in sec_sub_sec_nodes and
                    all(r IN relationships(i) WHERE r.part_number IN part_nos 
                    AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))
                    """
    # Return query for Operation Sections and SubSections
    RETURN_QUERY = """RETURN DISTINCT b.Name as feature, b.desc as desc, image.file_path as mediaUrl,
                    image.file_type as mediaContentType,image.size as mediaFileSize"""

    # The following queries are optional
    UNION_STRING = " UNION "
    # these will always prefixed with UNION
    # Variables: part_number_query, operation_or_subsection from above
    PROCEDURE_QUERY = """{part_number_query} {operation_or_subsection} WITH b, part_nos 
                         OPTIONAL MATCH p = (b)-[:HAS_PROCEDURE]->(e)
                         WHERE all(r IN relationships(p) WHERE r.part_number IN part_nos AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))
                         WITH part_nos, e
                         OPTIONAL MATCH i = (e)-[:HAS_IMAGE]->(image) WHERE all(r IN relationships(i) WHERE r.part_number IN part_nos 
                         AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))
                         WITH image, e ORDER BY e.step_no RETURN DISTINCT e.Name as feature,
                         e.desc as desc,image.file_path as mediaUrl,
                         image.file_type as mediaContentType,image.size as mediaFileSize
                        """

    FEATURE_QUERY = """{part_number_query} {operation_or_subsection} WITH b, part_nos 
                         OPTIONAL MATCH f = (b)-[:HAS_FEATURE]->(fe)
                         WHERE all(r IN relationships(f) WHERE r.part_number IN part_nos AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))
                         WITH part_nos, fe
                         OPTIONAL MATCH i = (fe)-[:HAS_IMAGE]->(image) WHERE all(r IN relationships(i) WHERE r.part_number IN part_nos 
                         AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))
                         WITH image, fe RETURN DISTINCT fe.Name as feature,
                         fe.desc as desc,image.file_path as mediaUrl,
                         image.file_type as mediaContentType,image.size as mediaFileSize
                        """

    SUB_SECTION_QUERY = """{part_number_query} {operation_or_subsection} WITH b, part_nos 
                         OPTIONAL MATCH s = (b)-[:HAS_SUB_SECTION*]->(su)
                         WHERE all(r IN relationships(s) WHERE r.part_number IN part_nos AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))
                         WITH part_nos, su
                         OPTIONAL MATCH i = (su)-[:HAS_IMAGE]->(image) WHERE all(r IN relationships(i) WHERE r.part_number IN part_nos 
                         AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))
                         WITH image, su RETURN DISTINCT su.Name as feature,
                         su.desc as desc,image.file_path as mediaUrl,
                         image.file_type as mediaContentType,image.size as mediaFileSize
                        """

    # The variable extra_info will be replaced at runtime as HAS_NOTE/HAS_CAUTION/HAS_WARNING
    EXTRA_INFO_QUERY = """{part_number_query} {operation_or_subsection} WITH b, part_nos 
                         OPTIONAL MATCH x = (b)-[:{extra_info}]->(ex)
                         WHERE all(r IN relationships(x) WHERE r.part_number IN part_nos AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))
                         WITH part_nos, ex
                         OPTIONAL MATCH i = (ex)-[:HAS_IMAGE]->(image) WHERE all(r IN relationships(i) WHERE r.part_number IN part_nos 
                         AND any(x IN {entity_type} WHERE x IN r.entity_prd_type))
                         WITH image, ex RETURN DISTINCT ex.Name as feature,
                         ex.desc as desc,image.file_path as mediaUrl,
                         image.file_type as mediaContentType,image.size as mediaFileSize
                        """

    # OLD QUERIES
    RETRIEVE_SECTION = """ MATCH(a)-[r1:HAS_OPERATION_SECTION]->(b) WHERE toLower(b.Name) 
                            contains toLower("%s") AND "%s" in r1.entity_prd_type AND 
                           r1.part_number in part.Name RETURN DISTINCT b.Name as feature,
                            b.desc as desc"""

    RETRIEVE_SUB_SECTION = """ MATCH(a)-[r1:HAS_OPERATION_SECTION]->(b)-[:HAS_SUB_SECTION*]->(c) 
                            WHERE "%s" in r1.entity_prd_type AND r1.part_number in part.Name
                            OPTIONAL MATCH (c)-[HAS_IMAGE]->(d) WITH part,b,c,d WHERE toLower(b.Name) 
                            contains toLower("%s") AND toLower(c.Name) contains toLower("%s") OR toLower(d.file_path) 
                            contains toLower(part.Name) RETURN DISTINCT c.Name as feature,
                            c.desc as desc,d.file_path as mediaUrl,
                            d.file_type as mediaContentType,d.size as mediaFileSize"""

    RETRIEVE_PROCEDURE = """ MATCH(a)-[r1:HAS_OPERATION_SECTION]->(b)-[:HAS_SUB_SECTION*]->(c)-[r2:HAS_PROCEDURE]->(d)
                            WHERE "%s" in r1.entity_prd_type AND r1.part_number in part.Name
                            AND "%s" in r2.entity_prd_type AND r2.part_number in part.Name 
                            AND toLower(c.Name) contains toLower("%s")
                            OPTIONAL MATCH (d)-[HAS_IMAGE]->(e)  OR toLower(e.file_path) 
                            contains toLower(part.Name)
                            WITH part,b,c,d,e ORDER BY d.step_no RETURN DISTINCT d.Name as feature,
                            d.desc as desc,e.file_path as mediaUrl,
                            e.file_type as mediaContentType,e.size as mediaFileSize """

    RETRIEVE_SPECIFIC_CNTLPANEL_FEATURE = """MATCH(a)-[r1:HAS_OPERATION_SECTION]->(b)-[:HAS_SUB_SECTION*]-(c)-[r2:HAS_FEATURE]->(d)
                            WHERE "%s" in r1.entity_prd_type AND r1.part_number in part.Name
                            AND "%s" in r2.entity_prd_type AND r2.part_number in part.Name 
                            AND toLower(c.Name) contains toLower("%s")
                            optional match(c)-[:HAS_IMAGE]->(e) WHERE toLower(e.file_path) contains toLower(part.Name) 
                            WITH part,d,e WHERE toLower(d.Name) contains toLower("%s")
                            RETURN DISTINCT d.Name as feature,
                            d.desc as desc,e.file_path as mediaUrl,e.file_type as mediaContentType,e.size as mediaFileSize"""

    RETRIEVE_CNTLPNL_FEATURE = """MATCH(a)-[r1:HAS_OPERATION_SECTION]->(b)-[:HAS_SUB_SECTION*]-(c)-[r2:HAS_FEATURE]->(d)
                            WHERE "%s" in r1.entity_prd_type AND r1.part_number in part.Name
                            AND "%s" in r2.entity_prd_type AND r2.part_number in part.Name 
                            AND toLower(c.Name) contains toLower("%s")
                           optional match(c)-[:HAS_IMAGE]-(e) WITH part,d,e WHERE toLower(e.file_path) contains 
                           toLower(part.Name) RETURN DISTINCT d.Name as feature,d.Name as desc, 
                           e.file_path as mediaUrl,e.file_type as mediaContentType,e.size as mediaFileSize"""

    # below queries will be used to retrieve note/caution/warning
    RETRIEVE_EXTRA_INFO = """ MATCH(a)-[r1:HAS_OPERATION_SECTION]->(b{Name:"%s"})-[r2:%s]->(c) 
                              WHERE "%s" in r1.entity_prd_type AND r1.part_number in part.Name AND "%s" in 
                              r2.entity_prd_type AND r2.part_number in part.Name  OPTIONAL MATCH (c)-[HAS_IMAGE]->(d) 
                              WHERE toLower(d.file_path) contains toLower(part.Name) 
                              WITH part,b,c,d RETURN DISTINCT b.Name as feature,c.Name as desc,d.file_path as mediaUrl,
                              d.file_type as mediaContentType,d.size as mediaFileSize """
    RETRIEVE_SPECIFIC_EXTRA_INFO = """ MATCH(a)-[r1:HAS_OPERATION_SECTION]->(b{Name:"%s"})-[:HAS_SUB_SECTION*]->
                                  (c{Name:"%s"})-[r2:%s]->(d) WHERE "%s" in r1.entity_prd_type AND r1.part_number in 
                                  part.Name AND "%s" in r2.entity_prd_type AND r2.part_number in part.Name 
                                  OPTIONAL MATCH (d)-[HAS_IMAGE]->(e) WHERE toLower(e.file_path) 
                                  contains toLower(part.Name) WITH part,b,c,d,e RETURN DISTINCT c.Name as feature,d.Name as desc,
                                  e.file_path as mediaUrl,e.file_type as mediaContentType,e.size as mediaFileSize """
    # queries to from paragraph with all info
    RETRIEVE_SECTION_ALL_INFO = """MATCH(n:%s{Name:"%s"})-[r1:HAS_OPERATION_SECTION]->(b) where toLower(b.Name)=toLower("%s")
                              AND "%s" in r1.entity_prd_type AND r1.part_number in part.Name 
                              OPTIONAL MATCH (c)-[HAS_IMAGE]->(d) WHERE toLower(d.file_path) contains toLower(part.Name) 
                            OPTIONAL MATCH(b)-[:HAS_SUB_SECTION]->(c) OPTIONAL MATCH(c)-[*]->(d) 
                            return distinct b as key1,c as key2,d as key3"""

    RETRIEVE_CNTLPNL_ALL_INFO = """MATCH(n:%s{Name:"%s"})-[:HAS_OPERATION_SECTION]->(b)-[:HAS_SUB_SECTION]->(c)-[:HAS_FEATURE]->(d)
                                    OPTIONAL MATCH(d)-[*]->(e) return distinct c as key1, d as key2, e as key3 """


class SeeManualContents(object):
    FOR_TROUBLESHOOTING = """
            MATCH(a:PartNumber{{Name:"{part_number}"}}) WITH COLLECT(a.Name) as part_nos, a 
            MATCH p = (a)-[r]->(b:Cause) 
            WHERE all(r IN relationships(p) WHERE r.part_number IN part_nos) 
            WITH DISTINCT coalesce(r.problem, r.error_code, r.noise) as problem, r.issue_type as problem_type RETURN problem_type, collect(problem) as problems"""

    FOR_OPERATION = """
                MATCH(a:PartNumber{{Name:"{part_number}"}}) WITH COLLECT(a.Name) as part_nos, a 
                MATCH p = (a)-[:HAS_OPERATION_SECTION]->()-[r:HAS_SUB_SECTION]->(b:OperationSubSection) 
                WHERE all(r IN relationships(p) WHERE r.part_number IN part_nos) 
                WITH COLLECT(DISTINCT b.Name) as sub_sections 
                RETURN sub_sections"""