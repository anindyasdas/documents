"""
/*-------------------------------------------------
* Copyright(c) 2021 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: anusha.kamath@lge.com
"""
import sys
import logging as logger
from difflib import get_close_matches

logger.debug("paths : %s", sys.path)

VC = "vacuum cleaner"
OVEN = "microwave oven"
WM = "washing machine"
AC = "air conditioner"
REF = "refrigerator"
DISHWASH = "dish washer"


def close_match_model(query_extracted_model, product=None):
    """
    function to get closest matching model number
    Args:
        query_extracted_model: model number extracted from the query
        product: product to which the model number belongs to

    Returns:
            model no in the DB if the given string matches any models of that product
    """
    from dialogue_manager.dialoguemanager import DialogueManager
    PROD_DICT = DialogueManager.get_instance().get_product_models()
    if product is None:
        patterns = sum(PROD_DICT.values(), [])
        d_model = get_close_matches(query_extracted_model, patterns, n=1, cutoff=0.6)
        if len(d_model) > 0: #if any model matches more than 60%
            product = [k for k, v in PROD_DICT.items() if d_model[0] in v]
            return d_model[0], product[0]
        return None, None
    else:
        patterns = PROD_DICT[product]
        d_model = get_close_matches(query_extracted_model, patterns, n=1, cutoff=0.6)
        if len(d_model) < 0: #if no model matches more than 60%
          return None, None
    return d_model[0], product


if __name__ == "__main__":
    print(close_match_model("DVAC903A", VC))
    print(close_match_model("VAC-902A*", VC))
