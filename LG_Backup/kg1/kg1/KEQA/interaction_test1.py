# -*- coding: utf-8 -*-
"""
Created on Wed Nov 18 16:49:42 2020

@author: Anindya
"""
import torch
import numpy as np
import random
import os
import pickle

from nltk.corpus import stopwords
from itertools import compress
from evaluation import evaluation, get_span
from argparse import ArgumentParser
from torchtext import data
from sklearn.metrics.pairwise import euclidean_distances
from fuzzywuzzy import fuzz
from util import www2fb, processed_text, clean_uri

parser = ArgumentParser(description="Joint Prediction")
parser.add_argument('--no_cuda', action='store_false', help='do not use cuda', dest='cuda')
parser.add_argument('--gpu', type=int, default=0)  # Use -1 for CPU
parser.add_argument('--embed_dim', type=int, default=250)
parser.add_argument('--batch_size', type=int, default=16)
parser.add_argument('--seed', type=int, default=3435)
parser.add_argument('--dete_model', type=str, default='dete_best_model.pt')
parser.add_argument('--entity_model', type=str, default='entity_best_model.pt')
parser.add_argument('--pred_model', type=str, default='pred_best_model.pt')
parser.add_argument('--output', type=str, default='preprocess')
args = parser.parse_args()
args.dete_model = os.path.join(args.output, args.dete_model)
args.entity_model = os.path.join(args.output, args.entity_model)
args.pred_model = os.path.join(args.output, args.pred_model)


def entity_predict(dataset_iter, model, index2word):
    model.eval()
    dataset_iter.init_epoch()
    dete_result = []
    question_list = []
    for data_batch_idx, data_batch in enumerate(dataset_iter):
        #batch_size = data_batch.text.size()[1]
        answer = torch.max(model(data_batch), 1)[1].view(data_batch.ed.size())
        answer[(data_batch.text.data == 1)] = 1
        answer = np.transpose(answer.cpu().data.numpy())
        index_question = np.transpose(data_batch.text.cpu().data.numpy())
        question_array = index2word[index_question]
        dete_result.extend(answer)
        question_list.extend(question_array)
        #for i in range(batch_size):  # If no word is detected as entity, select top 3 possible words
        #    if all([j == 1 or j == idxO for j in answer[i]]):
        #        index = list(range(i, scores.shape[0], batch_size))
        #        FindOidx = [j for j, x in enumerate(answer[i]) if x == idxO]
        #        idx_in_socres = [index[j] for j in FindOidx]
        #        subscores = scores[idx_in_socres]
        #        answer[i][torch.sort(torch.max(subscores, 1)[0], descending=True)[1][0:min(2, len(FindOidx))]] = idxI
    return dete_result, question_list

def compute_reach_dic(matched_mid):
    reach_dic = {}  # reach_dic[head_id] = [predicate_1,predicate2,predicate3]
    #all the prediacates associated for headentities of interest
    with open(os.path.join(args.output, 'transE_train.txt'), 'r', encoding='utf8') as f:
        for line in f:
            items = line.strip().split("\t")
            head_id = items[0]
            if head_id in matched_mid and items[2] in pre_dic:
                if reach_dic.get(head_id) is None:
                    reach_dic[head_id] = [pre_dic[items[2]]]
                else:
                    reach_dic[head_id].append(pre_dic[items[2]])
    return reach_dic

# Set random seed for reproducibility
torch.manual_seed(args.seed)
np.random.seed(args.seed)
random.seed(args.seed)

if not args.cuda:
    args.gpu = -1
if torch.cuda.is_available() and args.cuda:
    print("Note: You are using GPU for testing")
    torch.cuda.set_device(args.gpu)
    torch.cuda.manual_seed(args.seed)
if torch.cuda.is_available() and not args.cuda:
    print("Warning: You have Cuda but not use it. You are using CPU for testing.")

####################################################
field_t1 = open(os.path.join(args.output,'TEXT.pkl'),'rb')
TEXT = pickle.load(field_t1)
field_e1=open(os.path.join(args.output,'ED.pkl'),'rb')
ED= pickle.load(field_e1)
field_t1 .close()
field_e1.close()
########################################################################
####################################################
field_t1 = open(os.path.join(args.output,'TEXT1.pkl'),'rb')
TEXT1 = pickle.load(field_t1)
field_e1=open(os.path.join(args.output,'ED1.pkl'),'rb')
ED1= pickle.load(field_e1)
field_t1 .close()
field_e1.close()
########################################################################
####################################################
field_t1 = open(os.path.join(args.output,'TEXT2.pkl'),'rb')
TEXT2 = pickle.load(field_t1)
field_e1=open(os.path.join(args.output,'ED2.pkl'),'rb')
ED2= pickle.load(field_e1)
field_t1 .close()
field_e1.close()
########################################################################
#############################################################
mid_dic_file=open(os.path.join(args.output,'mid_dic.pkl'),'rb')
mid_num_dic_file=open(os.path.join(args.output,'mid_num_dic.pkl'),'rb')
mid_dic=pickle.load(mid_dic_file)
mid_num_dic=pickle.load(mid_num_dic_file)
mid_dic_file.close()
mid_num_dic_file.close()
###################################################################
pre_dic_file=open(os.path.join(args.output,'pre_dic.pkl'),'rb')
pre_num_dic_file=open(os.path.join(args.output,'pre_num_dic.pkl'),'rb')
pre_dic=pickle.load(pre_dic_file)
pre_num_dic=pickle.load(pre_num_dic_file)
pre_dic_file.close()
pre_num_dic_file.close()
#################################################################
match_pool_file=open(os.path.join(args.output,'match_pool.pkl'),'rb')
match_pool= pickle.load(match_pool_file)
match_pool_file.close()
####################################################################
#############################################################
index_name_file=open(os.path.join(args.output,'index_names.pkl'),'rb')
index_names=pickle.load(index_name_file)
index_name_file.close()
###################################################################
#############################################################
name_dict_file=open(os.path.join(args.output,'name_dict.pkl'),'rb')
name_dict=pickle.load(name_dict_file)
name_dict_file.close()
tuple_list_file=open(os.path.join(args.output,'tuple_list.pkl'),'rb')
tuple_list=pickle.load(tuple_list_file)
tuple_list_file.close()
###################################################################
######################################################################

# Embedding for MID
entities_emb = np.fromfile(os.path.join(args.output, 'entities_emb.bin'), dtype=np.float32).reshape((len(mid_dic), args.embed_dim))
predicates_emb = np.fromfile(os.path.join(args.output, 'predicates_emb.bin'), dtype=np.float32).reshape((-1, args.embed_dim))
#names_map = {}
###########################################################################
all_files=[TEXT,ED,TEXT1,ED1,TEXT2,ED2,mid_dic,mid_num_dic,pre_dic,pre_num_dic,match_pool,index_names,tuple_list,name_dict]



def interaction(text,all_files):
    TEXT,ED,TEXT1,ED1,TEXT2,ED2,mid_dic,mid_num_dic,pre_dic,pre_num_dic,match_pool,index_names,tuple_list,name_dict = all_files
    #text='what is a film directed by wiebke von carolsfeld'
    text=processed_text(text)
    temp_file= open('temp_file.txt', 'w', encoding='utf8')
    tokens = text.split()
    label = ["O"] * len(tokens)
    temp_file.write('{}\t{}\n'.format(text, label))
    temp_file.close()
    
    #################################################################################################
    temp = data.TabularDataset(path='temp_file.txt', format='tsv', fields=[('text', TEXT), ('ed', ED)])
    #temp_file.close()
    total_num = len(temp)
    if args.gpu == -1: # Load all tensors onto the CPU
        test_iter = data.Iterator(temp, batch_size=1, train=False, repeat=False, sort=False, shuffle=False, 
                                  sort_within_batch=False)
        model = torch.load(args.dete_model, map_location=lambda storage, loc: storage)
        model.config.cuda = False
    else:
        test_iter = data.Iterator(temp, batch_size=1, device=torch.device('cuda', args.gpu), train=False,
                                  repeat=False, sort=False, shuffle=False, sort_within_batch=False)
        model = torch.load(args.dete_model, map_location=lambda storage, loc: storage.cuda(args.gpu))
    index2tag = np.array(ED.vocab.itos)
    idxO = int(np.where(index2tag == 'O')[0][0])  # Index for 'O'
    idxI = int(np.where(index2tag == 'I')[0][0])  # Index for 'I'
    index2word = np.array(TEXT.vocab.itos)
    # run the model on the test set and write the output to a file
    dete_result, question_list = entity_predict(test_iter, model, index2word )
    del model
    
    ################################################################################################
    #################################################################################################
    
    #for fname in ["train.txt", "valid.txt"]:
    #    with open(os.path.join(args.output, fname), 'r') as f:
    #        for line in f:
    #            items = line.strip().split("\t")
    #            match_pool.extend(list(compress(items[5].split(), [element == 'O' for element in items[6].split()])))
    head_mid_idx = [[] for i in range(total_num)]  # [[head1,head2,...], [head1,head2,...], ...]
    #head_mid_idx contains detected_named entities, if match found or partial named entity
    #match_pool = set(match_pool + stopwords.words('english') + ["'s"]) #collection of tokens from predicates+stopwords
    whhowset = [{'what', 'how', 'where', 'who', 'which', 'whom'},
                {'in which', 'what is', "what 's", 'what are', 'what was', 'what were', 'where is', 'where are',
                 'where was', 'where were', 'who is', 'who was', 'who are', 'how is', 'what did'},
                {'what kind of', 'what kinds of', 'what type of', 'what types of', 'what sort of'}]
    dete_tokens_list, filter_q = [], []
    #dete_tokens_list contains detected_head_enty if match found or entire string exept wh-part
    #filter_q contains question without wh_part
    for i, question in enumerate(question_list):
        question = [token for token in question if token != '<pad>'] #question without pad
        pred_span = get_span(dete_result[i], index2tag, type=False) #position of head entity
        tokens_list, dete_tokens, st, en, changed = [], [], 0, 0, 0
        for st, en in pred_span:
            tokens = question[st:en] #tokens of head entity  ['lucille', 'clifton']
            tokens_list.append(tokens) #list of tokens of head entity [['lucille', 'clifton']]
            if index_names.get(' '.join(tokens)) is not None:  # important
                dete_tokens.append(' '.join(tokens)) #entity token joined ['lucille clifton']
                head_mid_idx[i].append(' '.join(tokens)) ##entity token joined ['lucille clifton']
        if len(question) > 2: #delete wh-part
            for j in range(3, 0, -1):
                if ' '.join(question[0:j]) in whhowset[j - 1]:
                    changed = j
                    del question[0:j]
                    continue
        tokens_list.append(question) #add list of tokens of question without wh-part
        filter_q.append(' '.join(question[:st - changed] + question[en - changed:])) #string without wh and head-entity from question 
        if not head_mid_idx[i]:
            dete_tokens = question
            for tokens in tokens_list:
                grams = []
                maxlen = len(tokens)
                for j in range(maxlen - 1, 1, -1):
                    for token in [tokens[idx:idx + j] for idx in range(maxlen - j + 1)]:
                        grams.append(' '.join(token))
                for gram in grams:
                    if index_names.get(gram) is not None:
                        head_mid_idx[i].append(gram)
                        break
                for j, token in enumerate(tokens):
                    if token not in match_pool:
                        tokens = tokens[j:]
                        break
                if index_names.get(' '.join(tokens)) is not None:
                    head_mid_idx[i].append(' '.join(tokens))
                tokens = tokens[::-1]
                for j, token in enumerate(tokens):
                    if token not in match_pool:
                        tokens = tokens[j:]
                        break
                tokens = tokens[::-1]
                if index_names.get(' '.join(tokens)) is not None:
                    head_mid_idx[i].append(' '.join(tokens))
        dete_tokens_list.append(' '.join(dete_tokens))
    
    id_match = set()
    match_mid_list = []
    tupleset = []
    for i, names in enumerate(head_mid_idx):
        tuplelist = []
        for name in names:
            mids = index_names[name]
            match_mid_list.extend(mids)
            for mid in mids:
                if mid_dic.get(mid) is not None:
                    tuplelist.append((mid, name))
        tupleset.extend(tuplelist)
        head_mid_idx[i] = list(set(tuplelist))
        if tuplelist: #if detected entities are present in database
            id_match.add(i)
    tupleset = set(tupleset)
    
    
    
    
    tuple_topic = []
    for item in tupleset:
        if tuple_list.get(item):
            #if item in tuple_list:
            tuple_topic.append(item)
    
    #for item in tupleset:
     #   if item in tuple_list:
      #      tuple_topic.append(item)
    tuple_topic = set(tuple_topic) #contains set of tuples (entity, object_name), only object name not aliases
    
    
    head_emb = np.zeros((total_num, args.embed_dim))
    
    temp = data.TabularDataset(path='temp_file.txt', format='tsv', fields=[('text', TEXT1), ('ed', None)])
    
    if args.gpu == -1:  # Load all tensors onto the CPU
        test_iter = data.Iterator(temp, batch_size=1, train=False, repeat=False, sort=False, shuffle=False, 
                                  sort_within_batch=False)
        model = torch.load(args.entity_model, map_location=lambda storage, loc: storage)
        model.config.cuda = False
    else:
        test_iter = data.Iterator(temp, batch_size=1, device=torch.device('cuda', args.gpu), train=False,
                                  repeat=False, sort=False, shuffle=False, sort_within_batch=False)
        model = torch.load(args.entity_model, map_location=lambda storage, loc: storage.cuda(args.gpu))
    
    
    model.eval()
    test_iter.init_epoch()
    baseidx = 0
    for data_batch_idx, data_batch in enumerate(test_iter):
        batch_size = data_batch.text.size()[1]
        scores = model(data_batch).cpu().data.numpy()
        for i in range(batch_size):
            head_emb[baseidx + i] = scores[i]
        baseidx = baseidx + batch_size
    del model
    ################################################################################################
    #################################################################################################
    temp = data.TabularDataset(path='temp_file.txt', format='tsv', fields=[('text', TEXT2), ('ed', None)])
    
    # load the model
    if args.gpu == -1:  # Load all tensors onto the CPU
        test_iter = data.Iterator(temp, batch_size=1, train=False, repeat=False, sort=False, shuffle=False, 
                                  sort_within_batch=False)
        model = torch.load(args.pred_model, map_location=lambda storage, loc: storage)
        model.config.cuda = False
    else:
        test_iter = data.Iterator(temp, batch_size=1, device=torch.device('cuda', args.gpu), train=False,
                                  repeat=False, sort=False, shuffle=False, sort_within_batch=False)
        model = torch.load(args.pred_model, map_location=lambda storage, loc: storage.cuda(args.gpu))
    model.eval()
    test_iter.init_epoch()
    baseidx = 0
    #pred_emb contains predicted embeddings of predicates from questions
    pred_emb = np.zeros((total_num, args.embed_dim))
    for data_batch_idx, data_batch in enumerate(test_iter):
        batch_size = data_batch.text.size()[1]
        scores = model(data_batch).cpu().data.numpy()
        for i in range(batch_size):
            pred_emb[baseidx + i] = scores[i]
        baseidx = baseidx + batch_size
    del model
    
    ###############################################
    
    ######################## predict and evaluation ########################
    
    gt_question=[]
    for line in open(os.path.join('temp_file.txt'), 'r', encoding='utf8'):
        items = line.strip().split("\t")
        gt_question.append(items[0])
        
    #find the index in the test set whose entities are not present in database KG
    notmatch = list(set(range(0, total_num)).symmetric_difference(id_match))
    
    if notmatch:# if not empty
        notmatch_idx = euclidean_distances(head_emb[notmatch], entities_emb, squared=True).argsort(axis=1)
        
    for idx, i in enumerate(notmatch):
        for j in notmatch_idx[idx, 0:40]:
            mid = mid_num_dic[j]
            head_mid_idx[i].append((mid, None))#add closest detected head entities with name as none, as there were no detected name_matches of head entity
            match_mid_list.append(mid)
    
    mid_num = 0
    for i, head_ids in enumerate(head_mid_idx):
        mids = set()
        for (head_id, name) in head_ids:
            mids.add(head_id)
        mid_num += len(mids)
    
    #for all the head_ids of interest reach_dic contains list of possible prediactes
    reach_dic = compute_reach_dic(set(match_mid_list))
    learned_pred, learned_fact, learned_head = [-1] * total_num, {}, [-1] * total_num
    #learned_pred, learned_head = [-1] * total_num,  [-1] * total_num
    
    alpha1, alpha3 = .39, .43
    for i, head_ids in enumerate(head_mid_idx):  # head_ids is mids #length is same as length of test set
        if i % 1000 == 1:
            print('progress:  {}'.format(i / total_num), end='\r')
        answers = []
        for (head_id, name) in head_ids: #for all possible head_id,name for a given question #[('m.04w4k8b', 'genevieve'),('m.03m5r9', 'genevieve')]
            mid_score = np.sqrt(np.sum(np.power(entities_emb[mid_dic[head_id]] - head_emb[i], 2)))
            #if name is None and head_id in names_map:
            #    name = names_map[head_id]
            name_score = - .003 * fuzz.ratio(name, dete_tokens_list[i])
            if (head_id, name) in tuple_topic:
                name_score -= .18
            if reach_dic.get(head_id) is not None:
                for pred_id in reach_dic[head_id]:  # reach_dic[head_id] = pred_id are numbers
                    rel_names = - .017 * fuzz.ratio(pre_num_dic[pred_id].replace('.', ' ').replace('_', ' '), filter_q[i]) #0.017 #compare score with question
                    rel_score = np.sqrt(np.sum(np.power(predicates_emb[pred_id] - pred_emb[i], 2))) + rel_names
                    tai_score = np.sqrt(np.sum(
                        np.power(predicates_emb[pred_id] + entities_emb[mid_dic[head_id]] - head_emb[i] - pred_emb[i], 2)))
                    answers.append((head_id, pred_id, alpha1 * mid_score + rel_score + alpha3 * tai_score + name_score))
        if answers:
            answers.sort(key=lambda x: x[2])
            learned_head[i] = answers[0][0]
            learned_pred[i] = answers[0][1]
            if learned_fact.get(' '.join([learned_head[i], pre_num_dic[learned_pred[i]]])) is None:
                learned_fact[' '.join([learned_head[i], pre_num_dic[learned_pred[i]]])] = [i] #note the line number
            else:
                learned_fact[' '.join([learned_head[i], pre_num_dic[learned_pred[i]]])].append(i)
            #if learned_head[i]=='m.02jbfk' and learned_pred[i]=='music.album_content_type.albums':
             #   print(learned_fact[' '.join([learned_head[i], pre_num_dic[learned_pred[i]]])])
            
    
    learned_tail = [[] for i in range(total_num)]
    #check the database to match
    #cleanedFB_dict={}
    
    for line in open(os.path.join(args.output, 'cleanedFB.txt'), 'r'):
        items = line.strip().split("\t")
        #if cleanedFB_dict.get(' '.join([items[0], items[2]])) is None:
         #   cleanedFB_dict[' '.join([items[0], items[2]])] = items[1].split()
        #else:
        #    cleanedFB_dict[' '.join([items[0], items[2]])].extend(items[1].split())
        if learned_fact.get(' '.join([items[0], items[2]])) is not None:
            for query_no in learned_fact[' '.join([items[0], items[2]])]:
                learned_tail[query_no].extend(items[1].split())
    # for i, tail_id in enumerate(learned_tail):
    #    if not tail_id:
    #        learned_tail[i] = mid_num_dic[euclidean_distances(
    #            (entities_emb[mid_dic[learned_head[i]]] + predicates_emb[learned_pred[i]]).reshape(1, -1), entities_emb,
    #            squared=True).argmin(axis=1)[0]]
    for i, qs in enumerate(gt_question):
        if learned_tail[i]:
            temp_list=learned_tail[i][:5]
            possible_answers=[]
            for item in temp_list:
                possible_answers.append(name_dict[item])
                possible_answers.append(',')
            possible_answers.pop()
        else:
            possible_answers = "Sorry, I am afraid , that I can't help with your query"
        #print(qs)
        print(' '.join(possible_answers))
                
        #for query_no in learned_fact[' '.join([learned_head[i], pre_num_dic[learned_pred[i]]])]:
    
while True:
    print("Please Ask Question:")
    text=str(input())
    if text=='0':
        break
    else:
        interaction(text, all_files)
