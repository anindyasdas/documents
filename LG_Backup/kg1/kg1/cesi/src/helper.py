import os, sys, re, pdb, time, argparse, logging, logging.config
import numpy as np, requests, json, operator, pickle, codecs
from numpy.fft import fft, ifft
from nltk.tokenize import sent_tokenize, word_tokenize
import itertools, pathlib
from pprint import pprint
from copy import deepcopy
from gensim.utils import lemmatize
from nltk.wsd import lesk
from collections import defaultdict as ddict
from joblib import Parallel, delayed

def mergeList(list_of_list):
    return list(itertools.chain.from_iterable(list_of_list))

def unique(l):
    return list(set(l))

def checkFile(filename):
    return pathlib.Path(filename).is_file()

def invertDic(my_map, struct = 'o2o'):
    inv_map = {}

    if struct == 'o2o':                # Reversing one-to-one dictionary
        for k, v in my_map.items():
            inv_map[v] = k

    elif struct == 'm2o':                # Reversing many-to-one dictionary
        for k, v in my_map.items():
            inv_map[v] = inv_map.get(v, [])
            inv_map[v].append(k)

    elif struct == 'm2ol':                # Reversing many-to-one list dictionary
        for k, v in my_map.items():
            for ele in v:
                inv_map[ele] = inv_map.get(ele, [])
                inv_map[ele].append(k)

    elif struct == 'm2os':
        for k, v in my_map.items():
            for ele in v:
                inv_map[ele] = inv_map.get(ele, set())
                inv_map[ele].add(k)

    return inv_map

def dumpCluster(fname, rep2clust, id2name):
    with open(fname, 'w') as f:
        for rep, clust in rep2clust.items():
            f.write(id2name[rep] + '\n')
            for ele in clust:
                f.write('\t' + id2name[ele] + '\n')

def dumpCluster_n(fname, fname1, rep2clust, id2name):
    with open(fname, 'w') as f:
        for rep, clust in rep2clust.items():
            f.write(id2name[rep] + '\n')
            for ele in clust:
                f.write('\t' + id2name[ele] + '\n')
                
    new_clust_dict ={}
    for rep, clust in rep2clust.items():
        new_clust_dict[rep] = list(set(clust))
    for rep, clust in rep2clust.items():
        for item in clust:
            if item not in new_clust_dict:
                new_clust_dict[item] = list(set(clust))
    with open(fname1, 'w') as f1:
        for item in id2name:
            if item not in new_clust_dict:
                f1.write(str(item) + '\t' + '1' + '\t' + str(item) +'\n')
            else:
                clus_item = new_clust_dict[item]
                cl_str = '\t'.join(list(map(str, clus_item)))
                f1.write(str(item) + '\t' + str(len(clus_item)) + '\t' + cl_str + '\n')
                
def dumpClusterAc(fname, fname1, rep2clust, id2name, nm2ac):
    new_clust_dict ={}
    for rep, clust in rep2clust.items():
        new_clust_dict[rep] = list(set(clust))
    for rep, clust in rep2clust.items():
        for item in clust:
            if item not in new_clust_dict:
                new_clust_dict[item] = list(set(clust))
    with open(fname1, 'w') as f1:
        for item in id2name:
            if item not in new_clust_dict:
                f1.write(str(item) + '\t' + '1' + '\t' + str(item) +'\n')
            else:
                clus_item = new_clust_dict[item]
                cl_str = '\t'.join(list(map(str, clus_item)))
                f1.write(str(item) + '\t' + str(len(clus_item)) + '\t' + cl_str + '\n')
        
    #print('nm2ac:',nm2ac)
    with open(fname, 'w') as f:
        for rep, clust in rep2clust.items():
            nm_name = id2name[rep]
            names = deepcopy(nm2ac[nm_name])
            name = names.pop()
            cluster = set()
            for item_name in names:
                cluster.add(item_name)
            for item in clust:
                #print('item 2:',item)
                #print('2:', id2name[item])
                for item_name in nm2ac[id2name[item]]:
                    cluster.add(item_name)
            f.write(name + '\n')
            for ele in cluster:
                f.write('\t' + ele + '\n')
                
def printitem2id(fname, item2id, nm2ac):
    new_dict = {}
    for key, value in item2id.items():
        items = nm2ac[key]
        for item in items:
            new_dict[item] = value
    with open(fname, 'w') as f:
        f.write(str(len(new_dict)) +'\n')
        for key, value in new_dict.items():
            f.write(key +'\t'+ str(value) +'\n')
            
            
def printitem2id_n(fname, item2id):
    with open(fname, 'w') as f:
        f.write(str(len(item2id)) +'\n')
        for key, value in item2id.items():
            f.write(key +'\t'+ str(value) +'\n')
            

def loadCluster(fname, name2id):
    rep2clust = ddict(list)
    with open(fname) as f:
        for line in f:
            if not line.startswith('\t'):     rep = name2id[line.strip()]
            else:                   rep2clust[rep].append(name2id[line.strip()])

    return rep2clust

def loadClusterAc(fname, name2id, ac2nm):
    rep2clust = ddict(list)
    with open(fname) as f:
        for line in f:
            if not line.startswith('\t'):     rep = name2id[ac2nm[line.strip()]]
            else:                   rep2clust[rep].append(name2id[ac2nm[line.strip()]])

    return rep2clust

# Get embedding of words from gensim word2vec model
def getEmbeddings(model, phr_list, embed_dims):
    embed_list = []

    for phr in phr_list:
        if phr in model.vocab:
            embed_list.append(model.word_vec(phr))
        else:
            vec = np.zeros(embed_dims, np.float32)
            wrds = word_tokenize(phr)
            for wrd in wrds:
                if wrd in model.vocab:     vec += model.word_vec(wrd)
                else:            vec += np.random.randn(embed_dims)
            embed_list.append(vec / len(wrds))

    return np.array(embed_list)

# ****************************** QUERYING PPDB SERVICE ***********************************

''' Returns list of PPDB representatives '''
def queryPPDB(ppdb_url, phr_list):
    try:
        data = {"data": phr_list}
        headers = {'Content-Type' : 'application/json'}
        req = requests.post(ppdb_url + 'ppdbAll', data=json.dumps(data), headers=headers)

        if (req.status_code == 200):
            data = json.loads(req.text)
            return data['data']
        else:
            print("Error! Status code :" + str(req.status_code))

    except Exception as e:
        print("Error in getGlove service!! \n\n", e)

def getPPDBclusters(ppdb_url, phr_list, phr2id):
    ppdb_map = dict()
    raw_phr_list = [phr.split('|')[0] for phr in phr_list]
    rep_list = queryPPDB(ppdb_url, raw_phr_list)

    for i in range(len(phr_list)):
        if rep_list[i] == None: continue        # If no representative for phr then skip

        phrId           = phr2id[phr_list[i]]
        ppdb_map[phrId] = rep_list[i]

    return ppdb_map

def getPPDBclustersRaw(ppdb_url, phr_list):
    ppdb_map = dict()
    raw_phr_list = [phr.split('|')[0] for phr in phr_list]
    rep_list = queryPPDB(ppdb_url, raw_phr_list)

    for i, phr in enumerate(phr_list):
        if rep_list[i] == None: continue        # If no representative for phr then skip
        ppdb_map[phr] = rep_list[i]

    return ppdb_map

# ***************************************** TEXT SPLIT ***********************************************
def proc_ent(ent):
    ent = ent.lower().replace('.', ' ').replace('-', ' ').strip().replace('_',' ').replace('|', ' ').strip()
    ent = ' '.join([ tok.decode('utf-8').split('/')[0] for tok in lemmatize(ent)])
    # ent = ' '.join(list( set(ent.split()) - set(config.stpwords)))
    return ent

def proc_rel(text):
    # replacing the multiple in-between spaces with one space
    text = re.sub('\s{2,}', ' ', text)
    # remove the space around the '-' character
    text = re.sub('\s*-\s*', '-', text)
    return text




def removearticles(text):
    toks = [tok for tok in text.split() if tok not in ['a', 'an', 'the']]
    text = " ".join(toks)
    # replacing the multiple in-between spaces with one space
    text = re.sub('\s{2,}', ' ', text)
    # remove the space around the '-' character
    text = re.sub('\s*-\s*', '-', text)
    return text

def proc_ent_n(ent):
    ent = ent.lower().replace('.', ' ').replace(',', '').strip().strip()
    ent = removearticles(ent)
    # ent = ' '.join(list( set(ent.split()) - set(config.stpwords)))
    return ent

def wordnetDisamb(sent, wrd):
    res = lesk(sent, wrd)
    if len(dir(res)) == 92:
        return res.name()
    else:
        return None

def getLogger(name, log_dir, config_dir):
    config_dict = json.load(open(config_dir + '/log_config.json'))

    if os.path.isdir(log_dir) == False:                 # Make log_dir if doesn't exist
        os.system('mkdir {}'.format(log_dir))

    config_dict['handlers']['file_handler']['filename'] = log_dir + '/' + name
    logging.config.dictConfig(config_dict)
    logger = logging.getLogger(name)

    std_out_format = '%(asctime)s - [%(levelname)s] - %(message)s'
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logging.Formatter(std_out_format))
    logger.addHandler(consoleHandler)

    return logger