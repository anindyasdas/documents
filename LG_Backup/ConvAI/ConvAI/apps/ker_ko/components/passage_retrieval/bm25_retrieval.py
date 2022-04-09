"""
/*-------------------------------------------------
* Copyright(c) 2021 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""

from gensim.summarization.bm25 import BM25


class PassageRetrieval:

    def __init__(self, nlp):
        self.tokenize = lambda text: [token.lemma_ for token in nlp(text)]
        self.bm25 = None
        self.passages = None

    def fit(self, passages):
        """
        Fit or train the BM25 model with the incoming set of passages

        Args:
            passages: list of passages or corpus on which the BM25 needs to be trained
        """
        corpus = [self.tokenize(p) for p in passages]
        self.bm25 = BM25(corpus)
        self.passages = passages

    def most_similar(self, question, topk=2):
        """
        Get the top k similar passages from the entire list of passages which on which the BM25 is trained (fitted)

        Args:
            question: Query for which the similar passages need to be retrieved
            topk: Top k number of passages

        Returns:
            list of top similar passages
        """
        tokens = self.tokenize(question)
        scores = self.bm25.get_scores(tokens)
        pairs = [(s, i) for i, s in enumerate(scores)]
        pairs.sort(reverse=True)
        passages = [self.passages[i] for _, i in pairs[:topk]]
        return passages
