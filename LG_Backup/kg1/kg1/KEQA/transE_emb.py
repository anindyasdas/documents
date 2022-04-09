from dataset import KnowledgeGraph
from model import TransE

#import tensorflow as tf
import argparse
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior() 
import os


def main():
    parser = argparse.ArgumentParser(description='TransE')
    parser.add_argument('--data_dir', type=str, default='preprocess/')
    parser.add_argument('--embedding_dim', type=int, default=200)
    parser.add_argument('--margin_value', type=float, default=1.0)
    parser.add_argument('--score_func', type=str, default='L1')
    parser.add_argument('--batch_size', type=int, default=4800)
    parser.add_argument('--learning_rate', type=float, default=0.001)
    parser.add_argument('--n_generator', type=int, default=24)
    parser.add_argument('--n_rank_calculator', type=int, default=24)
    parser.add_argument('--ckpt_dir', type=str, default='ckpt/')
    parser.add_argument('--summary_dir', type=str, default='summary/')
    parser.add_argument('--max_epoch', type=int, default=1)
    parser.add_argument('--eval_freq', type=int, default=10)
    args = parser.parse_args()
    print(args)
    if not os.path.exists(args.ckpt_dir):
        os.makedirs(args.ckpt_dir)
    model_path= os.path.join(args.ckpt_dir, 'model.ckpt')
    entity_bin= os.path.join(args.ckpt_dir, 'entity.bin')
    relation_bin= os.path.join(args.ckpt_dir, 'relation.bin')
    kg = KnowledgeGraph(data_dir=args.data_dir)
    kge_model = TransE(kg=kg, embedding_dim=args.embedding_dim, margin_value=args.margin_value,
                       score_func=args.score_func, batch_size=args.batch_size, learning_rate=args.learning_rate,
                       n_generator=args.n_generator, n_rank_calculator=args.n_rank_calculator)
    gpu_config = tf.GPUOptions(allow_growth=True)
    sess_config = tf.ConfigProto(gpu_options=gpu_config)
    saver= tf.train.Saver() #Save all variables/ model
    ####################show list of variables in our graphs####################
    #for i, var in enumerate(saver._var_list):
     #   print('Var {}: {}'.format(i, var))
    #print(saver._var_list)
    #list variables we want to save as serialized binary, if not given all variables
    var_li_E = [v for v in tf.global_variables() if v.name == 'embedding/entity:0']
    #print(var_li)
    var_li_R = [v for v in tf.global_variables() if v.name == 'embedding/relation:0']
    saver1 = tf.train.Saver(var_list=var_li_E)
    saver2 = tf.train.Saver(var_list=var_li_R)
   
    with tf.Session(config=sess_config) as sess:
        print('-----Initializing tf graph-----')
        tf.global_variables_initializer().run()
        print('-----Initialization accomplished-----')
        kge_model.check_norm(session=sess)
        summary_writer = tf.summary.FileWriter(logdir=args.summary_dir, graph=sess.graph)
        #saver.restore(sess, model_path)
        #print("Model restored from file: %s" % model_path)
        for epoch in range(args.max_epoch):
            print('=' * 30 + '[EPOCH {}]'.format(epoch) + '=' * 30)
            kge_model.launch_training(session=sess, summary_writer=summary_writer)
            if (epoch + 1) % args.eval_freq == 0:
                kge_model.launch_evaluation(session=sess)
            if (epoch +1 ) % 5 == 0:
                save_path_m = saver.save(sess, model_path, global_step=epoch, max_to_keep=2)
        save_path_m = saver.save(sess, model_path)
        print("Model saved in file: %s" % save_path_m)
        save_path_E =saver1.save(sess, entity_bin)
        print("Entity Embeddings saved in file: %s" % save_path_E)
        save_path_R =saver2.save(sess, relation_bin)
        print("Relation Embeddings saved in file: %s" % save_path_R)
        #e=sess.run(kge_model.entity.embedding)
        #print(e) #matrix
                


if __name__ == '__main__':
    main()
