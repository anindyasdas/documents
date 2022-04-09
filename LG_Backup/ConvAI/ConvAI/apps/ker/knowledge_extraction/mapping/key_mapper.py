"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vanitha.alagarsamy@lge.com
"""


class ProductKeyMapper(object):
    """
        utility class to map the key with the product
    """

    def __init__(self):
        self.key_map_dict = {"power": {"voltage": ['refrigerator']},
                             "model": {"description": ['washing machine', 'refrigerator', 'air conditioner',
                                                       'vacuum cleaner', 'microwave oven', 'dish washer']},
                             "power supply": {"output": ['microwave oven']}}

    def get_product_mapped_key(self, similarity_key, product):
        """
            function to map the similarity key with the
            product and returns the mapped key for product
            Args:
                similarity_key : str
                product : str
            Returns:
                mapped_key : str

        """
        similarity_dict = self.key_map_dict.get(similarity_key, None)

        if similarity_dict is None:
            return None

        for mapped_key, value in similarity_dict.items():
            if product in value:
                return mapped_key
        return None


if __name__ == "__main__":
    obj = ProductKeyMapper()
    mapped_key = obj.get_product_mapped_key("power", "refrigerator")
    print("mapped_key=%s" % str(mapped_key))
