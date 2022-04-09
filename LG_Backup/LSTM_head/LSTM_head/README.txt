glove based word embedding: data/sq_glove300d.pt
input data file:
	train: preprocess/train.txt
	test:	preprocess/test.txt
	valid:	preprocess/dev.txt

Output:
	saved model: preprocess/dete_best_model.pt 
	dictionary with keys "vocab":TEXT.vocab, "index2tag":index2tag: vocab.pkl
	predicted file(question<tab>predicted<tab>actual)

On dev set:
	Span: Span of "I" tags i.e head entity in labels eg. [OOIIOO] span=[[2,4]]

	Precision: Correctly predicted span/total number of predicted spans
	Recall: Correctly predicted span/total number of gold spans(Actual spans)
	F1: f1 = 2 * precision * recall / (precision + recall)

Accuracy on Train set:
	Number of sentences for which all the token tables are correctly predicted/ total number of sentences
	
