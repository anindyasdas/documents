"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: vishwaas@lge.com
"""

from .siamese_bert import SiameseBERT
from . import constants


class SimilarityFactory:

    SIAMESE_BERT_MODEL = 3

    @staticmethod
    def get_text_sim_model(model, config=None):
        """
        Gets the similarity model
        :param model: int model
        :param config: configuration of required
        :return: Model
        """
        if model == SimilarityFactory.SIAMESE_BERT_MODEL:
            siam = SiameseBERT(config)
            return siam
        else:
            raise ValueError("Model not found!")


if __name__ == '__main__': # pragma: no cover
    siam_fact = SimilarityFactory()
    config = {'ensemble': True, 'rem_words': []}
    config = None
    siam = siam_fact.get_text_sim_model(SIAMESE_BERT_MODEL, config)
    '''
    # siam.train()
    # siam.test()
    #siam.model_evaluate_file(Constants.FILE_PATH)
    '''
    print(siam.model_evaluate_single('I want to save energy, what option should I choose?'))
