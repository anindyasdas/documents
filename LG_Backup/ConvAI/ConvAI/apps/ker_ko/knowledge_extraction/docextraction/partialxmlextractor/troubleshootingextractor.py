from lxml import etree as et
import re
import copy
import logging as logger
from lxml import etree as et

from ...constants import params as p

logger = logger.getLogger("django")

class TroubleshootingExtractor(object):

    def extract_trob_prob_cause(self, ele_topic, internal_heading):
        """
        Extract the troubleshooting section problem with cause and solution
        
        Args:
            ele_topic: lxml elemnt of the topic
            internal_heading:extracted headind from section hierarchy
        Return:
            Extract partial xml string
        """
        logger.debug("extract_trob_prob_cause internal_heading : %s",str(internal_heading))
        if len(internal_heading) > 1:
            return self._extract_trob_based_on_err_code_cause(ele_topic, internal_heading[0], internal_heading[1:])
        else:
            return self._extract_trob_based_on_err_code_cause(ele_topic, internal_heading[0])

    def _extract_trob_based_on_err_code_cause(self, ele_topic, problem, cause=None):
        """
        extract the troubleshooting content based on error code
        
        Args:
            ele_topic:lxml elemnt of the topic
            problem:problem string
            cause: list of causes
        Return:
            Extracted oartial XML string
        """
        temp_ele_topic = copy.deepcopy(ele_topic)
        logger.debug("ele_topic : %s",et.tostring(ele_topic, pretty_print=True, encoding='utf-8'))
        ele_troubleshootings = temp_ele_topic.findall(p.XMLTags.TROUBLESHOOT_TAG)

        for ele_troubleshooting in ele_troubleshootings:
            ele_troublelistentries = ele_troubleshooting.findall(p.XMLTags.TROUBLELIST_ENTRY_TAG)
            for ele_troublelistentry in ele_troublelistentries:
                ele_problem = ele_troublelistentry.find(p.XMLTags.PROBLEM_TAG)
                problem_text = re.sub("[\n\t\s]", "", "".join(ele_problem.itertext())).rstrip(".")
                # invert the error mapped while extracting the troubleshooting error codes
                problem = p.ExtractionConstants.inv_map_error_code(problem)
                logger.debug("inverse mapped error code : %s", problem)
                problem = re.sub("[\n\t\s]", "", problem).rstrip(".")

                if (problem.lower() == problem_text.lower()) and (cause is not None):
                    ele_troublelistitems = ele_troublelistentry.findall(p.XMLTags.TROUBLELISTITEM_TAG)
                    cause = [ re.sub("[\n\t\s\?]", "", man_cause.strip()).rstrip(".") for man_cause in cause]
                    logger.debug("cause : %s",cause)
                    fnd_flag = False # Flag used to identify the cause found or not
                    for ele_troublelistitem in ele_troublelistitems:
                        ele_reason = ele_troublelistitem.find(p.XMLTags.REASON_TAG)
                        reason_text = re.sub("[\n\t\s\?]", "", "".join(ele_reason.itertext())).lower().rstrip(".")
                        logger.debug("reason_text : %s", reason_text)
                        if reason_text not in cause:
                            ele_troublelistitem.getparent().remove(ele_troublelistitem)
                        else:
                            fnd_flag = True
                    #If cause not found return None
                    if not fnd_flag:
                        return None, None
                    return p.XMLTags.TROUBLELIST_ENTRY_TAG, ele_troublelistentry
                elif (problem.lower() == problem_text.lower()):
                    return p.XMLTags.TROUBLELIST_ENTRY_TAG, ele_troublelistentry

        return None, None



