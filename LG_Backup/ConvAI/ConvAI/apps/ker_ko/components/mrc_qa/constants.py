# -------------------------------------------------
# Copyright(c) 2021 by LG Electronics.
# Confidential and Proprietary All Rights Reserved.
# -------------------------------------------------
import os

class PathConstants:
    # general paths for input/ output / model files
    current_folder = os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'dataset')) + '/'
    DATA_PATH = current_folder + 'dataset/'
    MODEL = current_folder + 'models/mrc_qa/'
    OUTPUT_DIR = MODEL + 'trained_model/'
    OUTPUT_EXPT_DIR = MODEL + 'trained_model/tmp'


class BertConstants:
    # Bert configs related constants
    BERT_PATH = PathConstants.MODEL + "multi_cased_L-12_H-768_A-12" + "/"
    VOCAB = BERT_PATH + 'vocab.txt'
    CHECKPOINT = BERT_PATH + 'checkpoint/bert_model.ckpt'
    CONFIG = BERT_PATH + 'bert_config.json'

class KerKoStringConstants:
    # features Dictionary keys
    INPUT_IDS = 'input_ids'
    INPUT_MASK = 'input_mask'
    SEGMENT_IDS = 'segment_ids'
    LABEL_IDS = 'label_ids'

class ResponseConstants:
    response_code = 'response_code'
    response_data = 'response_data'
    STATUS_OK = 200
    STATUS_UNSUPPORTED_QUERY = 201


class Flags:
    # Alternative to tf.flags to avoid conflicts with other BERT models in the pipeline
    bert_config_file = BertConstants.CONFIG
    vocab_file = BertConstants.VOCAB
    output_dir = PathConstants.OUTPUT_DIR
    train_file = "train.json"
    predict_file = "dev.json"
    init_checkpoint = BertConstants.CHECKPOINT
    do_lower_case = False
    max_seq_length = 512
    doc_stride = 128
    max_query_length = 64
    do_train = False
    do_predict = True
    train_batch_size = 32
    predict_batch_size = 8
    learning_rate = 5e-5
    num_train_epochs = 3.0
    warmup_proportion = 0.1
    save_checkpoints_steps = 100
    iterations_per_loop = 1000
    n_best_size = 20
    max_answer_length = 30
    use_tpu = False
    tpu_name = None
    tpu_zone = None
    gcp_project = None
    master = None
    num_tpu_cores = 8
    verbose_logging = False
    version_2_with_negative = False
    null_score_diff_threshold = 0.0