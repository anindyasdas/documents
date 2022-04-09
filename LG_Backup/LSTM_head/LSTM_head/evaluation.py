
def get_span(label, index2tag):
    """
    

    Parameters
    ----------
    label : TYPE
        DESCRIPTION. indices corresponding to labels of a sentence
        [2 2 2 3 3 2 2 1 1]
    index2tag : TYPE
        DESCRIPTION. np.array index to tag  ['<unk>' '<pad>' 'O' 'I']
    type : TYPE
        DESCRIPTION.

    Returns
    -------
    span : TYPE
        DESCRIPTION. Span of the "I" tag, [(3, 5)]

    """
    span = []
    st = -1
    en = -1
    flag = False
    for k in range(len(label)):
        if index2tag[label[k]][0] == 'I' and flag == False:
            flag = True
            st = k
            
        
        if index2tag[label[k]][0] != 'I' and flag == True:
            flag = False
            en = k
            span.append((st,en))
            st = -1
            en = -1
    if st != -1 and en == -1:
        en = len(label)
        
        span.append((st, en))

    return span

def evaluation(gold, pred, index2tag):
    right = 0
    predicted = 0
    total_en = 0
    #fout = open('log.valid', 'w')
    #print("len gold:", len(gold)) #total number of batches in dev set
    for i in range(len(gold)):
        gold_batch = gold[i] #one of the batches
        pred_batch = pred[i] #correspodning predicted batch
        

        for j in range(len(gold_batch)):
            gold_label = gold_batch[j] #labels of one sentence
            pred_label = pred_batch[j] #labels of one predicted sentence
            #print("gold_label:", gold_label)
            #print("pred_label:", pred_label)
            #print("index2tag:", index2tag)
            gold_span = get_span(gold_label, index2tag)
            pred_span = get_span(pred_label, index2tag)
            #print("gold_span:", gold_span)
            #print("pred_span:", pred_span)
            
            #fout.write('{}\t{}\n'.format(gold_span, pred_span))
            total_en += len(gold_span)
            predicted += len(pred_span)
            for item in pred_span:
                if item in gold_span:
                    right += 1
    if predicted == 0:
        precision = 0
    else:
        precision = right / predicted
    if total_en == 0:
        recall = 0
    else:
        recall = right / total_en
    if precision + recall == 0:
        f1 = 0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    #fout.flush()
    #fout.close()
    return precision, recall, f1

def prepare_output_data(questions, gold_tags, pred_tags, vocab, index2tag): 
    output_data=[]
    stoi= vocab.stoi
    itos= vocab.itos
    pad_index= stoi['<pad>']
    for ind in range(len(questions)):
        question_batch= questions[ind]
        gold_batch= gold_tags[ind]
        pred_batch= pred_tags[ind]
        for q,g,p in zip(question_batch, gold_batch, pred_batch):
            q_indices=[itos[i] for i in q if i!=pad_index]
            st=" ".join(q_indices)
            pred_span = get_span(p, index2tag)
            try:
                start_idx=pred_span[0][0]
                end_index=pred_span[0][1]
                predicted_entity=q[start_idx:end_index]
                predicted_entity=[itos[i] for i in predicted_entity if i!=pad_index]
                predicted_entity=" ".join(predicted_entity)
            except:
                predicted_entity= "NOT FOUND"
            gold_span = get_span(g, index2tag)
            start_idx=gold_span[0][0]
            end_index=gold_span[0][1]
            gold_entity=q[start_idx:end_index]
            gold_entity=[itos[i] for i in gold_entity if i!=pad_index]
            gold_entity=" ".join(gold_entity)
            output_data.append((st, predicted_entity, gold_entity))
    return output_data
    
    

def get_names_for_entities(namespath):
    print("getting names map...")
    names = {}
    with open(namespath, 'r') as f:
        for i, line in enumerate(f):
            items = line.strip().split("\t")
            if len(items) != 2:
                print("ERROR: line - {}".format(line))
                continue
            entity = items[0]
            literal = items[1].strip()
            if literal != "":
                if names.get(literal) is None:
                    names[literal] = [(entity)]
                else:
                    names[literal].append(entity)
                    #print('ERROR: Entities with the same name!')
    return names