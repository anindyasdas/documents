# -------------------------------------------------
# Copyright(c) 2021 by LG Electronics.
# Confidential and Proprietary All Rights Reserved.
# -------------------------------------------------
import os
import tensorflow as tf
from tensorflow.contrib import predictor
from pathlib import Path
import collections

from . import constants as cs
from . import modeling as modeling
from . import run_squad as run_squad
from . import tokenization as tokenization
from .run_squad import model_fn_builder as model_fn_builder

from .constants import Flags as FLAGS


def serving_input_fn():
    """
    Input function when the model is Served as a Saved model (pb file)
    """
    input_ids = tf.placeholder(tf.int32, [None, FLAGS.max_seq_length], name=cs.KerKoStringConstants.INPUT_IDS)
    input_mask = tf.placeholder(tf.int32, [None, FLAGS.max_seq_length], name=cs.KerKoStringConstants.INPUT_MASK)
    segment_ids = tf.placeholder(tf.int32, [None, FLAGS.max_seq_length], name=cs.KerKoStringConstants.SEGMENT_IDS)
    input_fn = tf.estimator.export.build_raw_serving_input_receiver_fn({
        # cs.KerKoStringConstants.LABEL_IDS: label_ids,
        cs.KerKoStringConstants.INPUT_IDS: input_ids,
        cs.KerKoStringConstants.INPUT_MASK: input_mask,
        cs.KerKoStringConstants.SEGMENT_IDS: segment_ids,
    })()
    return input_fn


class MrcQaEngine:
    """
    Interface to execute MRC QA
    ##TBD Singleton class
    """

    def __init__(self):
        self.bert_config = modeling.BertConfig.from_json_file(FLAGS.bert_config_file)
        self.is_per_host = tf.contrib.tpu.InputPipelineConfig.PER_HOST_V2

        # Instance of BERT tokenizer
        # When using this model, make sure to pass --do_lower_case=false to run_pretraining.py and other scripts.
        # From https://github.com/google-research/bert/blob/master/multilingual.md
        self.tokenizer = tokenization.FullTokenizer(
            vocab_file=FLAGS.vocab_file, do_lower_case=False)

        run_config = tf.contrib.tpu.RunConfig(
            cluster=None,
            master=FLAGS.master,
            model_dir=FLAGS.output_dir,
            save_checkpoints_steps=FLAGS.save_checkpoints_steps,
            tpu_config=tf.contrib.tpu.TPUConfig(
                iterations_per_loop=FLAGS.iterations_per_loop,
                num_shards=FLAGS.num_tpu_cores,
                per_host_input_for_training=self.is_per_host))

        model_fn = model_fn_builder(
            bert_config=self.bert_config,
            init_checkpoint=FLAGS.init_checkpoint,
            learning_rate=FLAGS.learning_rate,
            num_train_steps=None,
            num_warmup_steps=None,
            use_tpu=FLAGS.use_tpu,
            use_one_hot_embeddings=FLAGS.use_tpu)

        # If TPU is not available, this will fall back to normal Estimator on CPU
        # or GPU.
        self.estimator = tf.contrib.tpu.TPUEstimator(
            use_tpu=FLAGS.use_tpu,
            model_fn=model_fn,
            config=run_config,
            train_batch_size=FLAGS.train_batch_size,
            predict_batch_size=FLAGS.predict_batch_size)

        self.estimator._export_to_tpu = False
        output_dir_temp = cs.PathConstants.OUTPUT_EXPT_DIR
        os.makedirs(output_dir_temp, exist_ok=True)
        if len(os.listdir(output_dir_temp)) == 0:
            self.estimator.export_saved_model(output_dir_temp, serving_input_fn)

        export_dir = FLAGS.output_dir
        subdirs = [x for x in Path(export_dir).iterdir() if x.is_dir() and 'temp' not in str(x)]
        latest = str(sorted(subdirs)[-1])
        self.model_predictor = predictor.from_saved_model(latest)

    def _read_squad_example(self, paragraph_text, question_text):
        """
        Function to get the input feature for the model on single line output.

        Args:
            paragraph_text: context for the question
            question_text: User query to be answered

        Returns:
            Input to be given to the MRC QA model
        """
        def is_whitespace(c):
            if c == " " or c == "\t" or c == "\r" or c == "\n" or ord(c) == 0x202F:
                return True
            return False

        doc_tokens = []
        char_to_word_offset = []
        prev_is_whitespace = True
        start_position = None
        end_position = None
        orig_answer_text = None
        is_impossible = False
        for c in paragraph_text:
            if is_whitespace(c):
                prev_is_whitespace = True
            else:
                if prev_is_whitespace:
                    doc_tokens.append(c)
                else:
                    doc_tokens[-1] += c
                prev_is_whitespace = False
            char_to_word_offset.append(len(doc_tokens) - 1)

        example = run_squad.SquadExample(
            qas_id=1,
            question_text=question_text,
            doc_tokens=doc_tokens,
            orig_answer_text=orig_answer_text,
            start_position=start_position,
            end_position=end_position,
            is_impossible=is_impossible)

        return [example]

    def get_input_features(self, paragraph_text, question_text, output_fn):
        """
        To convert the text input as features in the format required by BERT
        A dict which include list of input_ids, input_mask, segment_ids
        """
        example = self._read_squad_example(paragraph_text, question_text)[0]
        query_tokens = self.tokenizer.tokenize(example.question_text)
        if len(query_tokens) > FLAGS.max_query_length:
            query_tokens = query_tokens[0: FLAGS.max_query_length]

        tok_to_orig_index = []
        orig_to_tok_index = []
        all_doc_tokens = []
        for (i, token) in enumerate(example.doc_tokens):
            orig_to_tok_index.append(len(all_doc_tokens))
            sub_tokens = self.tokenizer.tokenize(token)
            for sub_token in sub_tokens:
                tok_to_orig_index.append(i)
                all_doc_tokens.append(sub_token)

        # The -3 accounts for [CLS], [SEP] and [SEP]
        max_tokens_for_doc = FLAGS.max_seq_length - len(query_tokens) - 3

        # We can have documents that are longer than the maximum sequence length.
        # To deal with this we do a sliding window approach, where we take chunks
        # of the up to our max length with a stride of `doc_stride`.
        _DocSpan = collections.namedtuple(  # pylint: disable=invalid-name
            "DocSpan", ["start", "length"])
        doc_spans = []
        start_offset = 0
        while start_offset < len(all_doc_tokens):
            length = len(all_doc_tokens) - start_offset
            if length > max_tokens_for_doc:
                length = max_tokens_for_doc
            doc_spans.append(_DocSpan(start=start_offset, length=length))
            if start_offset + length == len(all_doc_tokens):
                break
            start_offset += min(length, FLAGS.doc_stride)

        for (doc_span_index, doc_span) in enumerate(doc_spans):
            tokens = []
            token_to_orig_map = {}
            token_is_max_context = {}
            segment_ids = []
            tokens.append("[CLS]")
            segment_ids.append(0)
            for token in query_tokens:
                tokens.append(token)
                segment_ids.append(0)
            tokens.append("[SEP]")
            segment_ids.append(0)

            for i in range(doc_span.length):
                split_token_index = doc_span.start + i
                token_to_orig_map[len(tokens)] = tok_to_orig_index[split_token_index]

                is_max_context = run_squad._check_is_max_context(doc_spans, doc_span_index,
                                                                 split_token_index)
                token_is_max_context[len(tokens)] = is_max_context
                tokens.append(all_doc_tokens[split_token_index])
                segment_ids.append(1)
            tokens.append("[SEP]")
            segment_ids.append(1)

            input_ids = self.tokenizer.convert_tokens_to_ids(tokens)

            # The mask has 1 for real tokens and 0 for padding tokens. Only real
            # tokens are attended to.
            input_mask = [1] * len(input_ids)

            # Zero-pad up to the sequence length.
            while len(input_ids) < FLAGS.max_seq_length:
                input_ids.append(0)
                input_mask.append(0)
                segment_ids.append(0)
            start_position = None
            end_position = None
            feature = run_squad.InputFeatures(
                unique_id=1,
                example_index=1,
                doc_span_index=doc_span_index,
                tokens=tokens,
                token_to_orig_map=token_to_orig_map,
                token_is_max_context=token_is_max_context,
                input_ids=input_ids,
                input_mask=input_mask,
                segment_ids=segment_ids,
                start_position=start_position,
                end_position=end_position,
                is_impossible=example.is_impossible)
            output_fn(feature)

        return {"input_ids": [input_ids], "input_mask": [input_mask], "segment_ids": [segment_ids]}, example

    def get_mrc_output(self, paragraph, user_query):
        """
        Public function to get MRC QA output
        Args:
            paragraph: context for the question
            user_query: user query to be answered

        Returns:
            Answer to the factoid user question & the  model confidence_score
        """
        eval_features = []

        def append_feature(feature):
            eval_features.append(feature)

        predictor = self.model_predictor
        final_fe_dict , eval_sample= self.get_input_features(paragraph, user_query, append_feature)
        predictions = predictor(final_fe_dict)
        all_results = []
        start_logits = [float(x) for x in predictions["start_logits"].flat]
        end_logits = [float(x) for x in predictions["end_logits"].flat]
        all_results.append(
            run_squad.RawResult(
                start_logits=start_logits,
                end_logits=end_logits))
        ans = run_squad.write_predictions(all_examples=[eval_sample], all_features=eval_features, all_results=[all_results],
                                    n_best_size=FLAGS.n_best_size,
                                    max_answer_length=FLAGS.max_seq_length, do_lower_case=FLAGS.do_lower_case,
                                    output_prediction_file=None,
                                    output_nbest_file=None, output_null_log_odds_file=None)

        best_answer = ans[1]["text"]
        confidence_score = ans[1]["probability"]

        return best_answer, confidence_score


if __name__ == "__main__":
    ce = MrcQaEngine()
    para = r"그리고 갤럭시 S5에 탑재되었다가 갤럭시 S6/S6 엣지에서 도로 삭제되었던 방수 방진을 다시 지원한다. 등급은 IP68로, 이는 방진 등급으로나 방수 등급으로나 모두 최고레벨이며 갤럭시 S5보다도 높은 등급이다. 또한, 심장 박동 인식 센서가 전작인 갤럭시 S6와 동일하게 후면 카메라 모듈 옆에 존재한다. 다만, 안드로이드 6.0 마시멜로가 AOSP 단에서 기본적으로 지원하기 시작한 USB Type-C가 아닌 micro 5핀이라 불리는 기존 규격인 USB micro Type-B를 입출력 단자로 사용한다. 이는 USB Type-C로 아직 캡리스 방수 솔루션이 준비되지 않았고 여기에 삼성 기어 VR과의 호환성 문제도 존재하기 때문이다."
    question = "갤럭시 S7 엣지의 방수 방진 등급은 무엇인가?"
    print(ce.get_mrc_output(para, question))
