# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 15:34:30 2021

@author: anindya06.das
"""
import warnings
from transformers import GPT2LMHeadModel,  GPT2Tokenizer, GPT2Config, GPT2LMHeadModel
from transformers import AdamW, get_linear_schedule_with_warmup

import nltk
import torch
import torch.nn.functional as F
from copy import deepcopy
#nltk.download('punkt')
from torch.utils.data import Dataset, DataLoader, random_split, RandomSampler, SequentialSampler
torch.manual_seed(42)
import numpy as np
import random
import datetime
# Load the GPT tokenizer.
import time
import pickle
import json
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')#, bos_token='<qbos>', eos_token='<qeos>', pad_token='<pad>') #gpt2-medium

#############################################
ATTR_TO_SPECIAL_TOKEN = {
    "bos_token": "<qbos>",
    "eos_token": "<eeos>",
    "pad_token": "<pad>",
    "additional_special_tokens": ["<qeos>"],
}
SPECIAL_TOKEN=["<qbos>","<qeos>","<eeos>","<pad>"]

batch_size=16

# some parameters I cooked up that work reasonably well

epochs = 50
learning_rate = 1e-4
warmup_steps = 1e2
epsilon = 1e-8

# this produces sample output every 100 steps
sample_every = 100
#%%
def top_filtering(logits, top_k=0.0, top_p=0.9, threshold=-float("Inf"), filter_value=-float("Inf")):
    """ Filter a distribution of logits using top-k, top-p (nucleus) and/or threshold filtering
        Args:
            logits: logits distribution shape (vocabulary size)
            top_k: <=0: no filtering, >0: keep only top k tokens with highest probability.
            top_p: <=0.0: no filtering, >0.0: keep only a subset S of candidates, where S is the smallest subset
                whose total probability mass is greater than or equal to the threshold top_p.
                In practice, we select the highest probability tokens whose cumulative probability mass exceeds
                the threshold top_p.
            threshold: a minimal threshold to keep logits
    """
    assert (
        logits.dim() == 1
    )  # Only work for batch size 1 for now - could update but it would obfuscate a bit the code
    top_k = min(top_k, logits.size(-1))
    if top_k > 0:
        # Remove all tokens with a probability less than the last token in the top-k tokens
        indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
        logits[indices_to_remove] = filter_value

    if top_p > 0.0:
        # Compute cumulative probabilities of sorted tokens
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
        cumulative_probabilities = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

        # Remove tokens with cumulative probability above the threshold
        sorted_indices_to_remove = cumulative_probabilities > top_p
        # Shift the indices to the right to keep also the first token above the threshold
        sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
        sorted_indices_to_remove[..., 0] = 0

        # Back to unsorted indices and set them to -infinity
        indices_to_remove = sorted_indices[sorted_indices_to_remove]
        logits[indices_to_remove] = filter_value

    indices_to_remove = logits < threshold
    logits[indices_to_remove] = filter_value

    return logits

def sample_sequence(text, tokenizer, model, device="cuda", min_length=1, max_length=40, do_sample=True, current_output=None):   
    special_tokens_ids = tokenizer.convert_tokens_to_ids(SPECIAL_TOKEN)
    if current_output is None:
        current_output = []
    encodings_dict = tokenizer(text)
        #print(txt)
  
    input_ids =encodings_dict['input_ids']
    #print(input_ids)

    for i in range(max_length):

  
        input_ids =input_ids+ current_output
        #print("GGGGG:", i, input_ids)
        input_tensor= torch.tensor(input_ids).long()
        input_tensor= input_tensor.to(device)
        
        

        

        outputs = model(input_tensor)
        logits=outputs[0]
        logits = logits[-1, :] 
        logits = top_filtering(logits)
        probs = F.softmax(logits, dim=-1)

        prev = torch.topk(probs, 1)[1] if not do_sample else torch.multinomial(probs, 1)
        #print(prev)
        if i < min_length and prev.item() in special_tokens_ids:
            while prev.item() in special_tokens_ids:
                if probs.max().item() == 1:
                    warnings.warn("Warning: model generating special token with probability 1.")
                    break  # avoid infinitely looping over special token
                prev = torch.multinomial(probs, num_samples=1)

        if prev.item() in special_tokens_ids:
            break
        #print(prev)
        current_output.append(prev.item())

    return tokenizer.decode(current_output)

def format_time(elapsed):
    return str(datetime.timedelta(seconds=int(round((elapsed)))))

def add_special_tokens_(model, tokenizer):
    """ Add special tokens to the tokenizer and the model if they have not already been added. """
    orig_num_tokens = len(tokenizer.encoder)
    num_added_tokens = tokenizer.add_special_tokens(ATTR_TO_SPECIAL_TOKEN)  # doesn't add if they are already there
    if num_added_tokens > 0:
        # this step is necessary because I've added some tokens (bos_token, etc) to the embeddings
        # otherwise the tokenizer and model tensors won't match up
        model.resize_token_embeddings(new_num_tokens=orig_num_tokens + num_added_tokens)
    return model, tokenizer

###################################################

def read_data(file_name):
    train=[]
    f=open(file_name, 'r', encoding='latin1')
    for line in f:
        q,n,h,a=line.strip().split("\t")
        new_line='<qbos> '+q.strip()+ ' <qeos> '+n.strip() +' <eeos>'
        train.append(new_line.strip())
    return train
    

    
##########################################    


#%%
        
        
class GPT2Dataset(Dataset):

  def __init__(self, txt_list, tokenizer, gpt2_type="gpt2", max_length=768):

    self.tokenizer = tokenizer
    self.input_ids = []
    self.attn_masks = []
    self.labels =[]
    self.qbos=tokenizer.bos_token_id
    self.eeos=tokenizer.eos_token_id
    self.pad=tokenizer.pad_token_id
    self.qeos=tokenizer.encode(SPECIAL_TOKEN[1])[0]

    for txt in txt_list:

      encodings_dict = tokenizer(txt, truncation=True, max_length=max_length, padding="max_length")
      #print(txt)
      
      input_id =encodings_dict['input_ids']
      #print(input_id)
      start_head=input_id.index(self.qeos) 
      #start_head=(input_id == self.qeos).nonzero(as_tuple=True)[0]
      end_head=input_id.index(self.eeos)
      #end_head=(input_id == self.eeos).nonzero(as_tuple=True)[0]
      label= torch.Tensor(deepcopy(input_id))
      label[:start_head+1]=-100
      label[end_head+1:]=-100

      self.input_ids.append(torch.tensor(input_id))
      self.attn_masks.append(torch.tensor(encodings_dict['attention_mask']))
      self.labels.append(label)
      #print(label)
    
  def __len__(self):
    return len(self.input_ids)

  def __getitem__(self, idx):
    return self.input_ids[idx].long(), self.attn_masks[idx].long() , self.labels[idx].long()
       
#%%
##################################################
####################################model###################
    
# I'm not really doing anything with the config buheret
configuration = GPT2Config.from_pretrained('gpt2', output_hidden_states=False)

# instantiate the model
model = GPT2LMHeadModel.from_pretrained("gpt2", config=configuration)


#%%
###########################################################
#####################Add special tokens########################
    

        
model, tokenizer= add_special_tokens_(model, tokenizer)
#################################################################

print("The max model length is {} for this model, although the actual embedding size for GPT small is 768".format(tokenizer.model_max_length))
print("The beginning of sequence token {} token has the id {}".format(tokenizer.convert_ids_to_tokens(tokenizer.bos_token_id), tokenizer.bos_token_id))
print("The end of sequence token {} has the id {}".format(tokenizer.convert_ids_to_tokens(tokenizer.eos_token_id), tokenizer.eos_token_id))
print("The padding token {} has the id {}".format(tokenizer.convert_ids_to_tokens(tokenizer.pad_token_id), tokenizer.pad_token_id))


file_train="./web_train.txt"
file_test="./web_test.txt"
train=read_data(file_train)
test=read_data(file_test)
#%%

train_dataset = GPT2Dataset(train, tokenizer, max_length=100)
test_dataset = GPT2Dataset(test, tokenizer, max_length=100)

# Create the DataLoaders for our training and validation datasets.
# We'll take training samples in random order. 
train_dataloader = DataLoader(
            train_dataset,  # The training samples.
            sampler = RandomSampler(train_dataset), # Select batches randomly
            batch_size = batch_size # Trains with this batch size.
        )

# For validation the order doesn't matter, so we'll just read them sequentially.
test_dataloader = DataLoader(
            test_dataset, # The validation samples.
            sampler = SequentialSampler(test_dataset), # Pull out batches sequentially.
            batch_size = batch_size # Evaluate with this batch size.
        )

#%%    
# Tell pytorch to run this model on the GPU.
device = torch.device("cuda")
model.cuda()

# Set the seed value all over the place to make this reproducible.
seed_val = 42

random.seed(seed_val)
np.random.seed(seed_val)
torch.manual_seed(seed_val)
torch.cuda.manual_seed_all(seed_val)
#%%
# Note: AdamW is a class from the huggingface library (as opposed to pytorch) 
optimizer = AdamW(model.parameters(),
                  lr = learning_rate,
                  eps = epsilon
                )
#%%
# Total number of training steps is [number of batches] x [number of epochs]. 
# (Note that this is not the same as the number of training samples).
total_steps = len(train_dataloader) * epochs

# Create the learning rate scheduler.
# This changes the learning rate as the training loop progresses
scheduler = get_linear_schedule_with_warmup(optimizer, 
                                            num_warmup_steps = warmup_steps, 
                                            num_training_steps = total_steps)
#%%
total_t0 = time.time()

training_stats = []

model = model.to(device)
best_val_loss=float("Inf")
patience_counter=0
patience=50
epoch_i=0
while True:
    if patience_counter==patience:
        break

    # ========================================
    #               Training
    # ========================================

    print("")
    print('======== Epoch {:} / {:} ========'.format(epoch_i + 1, epochs))
    print('Training...')

    t0 = time.time()

    total_train_loss = 0

    model.train()

    for step, batch in enumerate(train_dataloader):

        b_input_ids = batch[0].to(device)
        b_labels = batch[2].to(device)
        b_masks = batch[1].to(device)

        model.zero_grad()        

        outputs = model(  b_input_ids,
                          labels=b_labels, 
                          attention_mask = b_masks,
                          token_type_ids=None
                        )
       

        loss = outputs[0]
        logits=outputs[1]

        batch_loss = loss.item()
        total_train_loss += batch_loss

        print("\rRunning loss: %f" %batch_loss, end="")

        loss.backward()

        optimizer.step()

        scheduler.step()

    # Calculate the average loss over all of the batches.
    avg_train_loss = total_train_loss / len(train_dataloader)       
    
    # Measure how long this epoch took.
    training_time = format_time(time.time() - t0)

    print("")
    print("  Average training loss: {0:.2f}".format(avg_train_loss))
    print("  Training epoch took: {:}".format(training_time))
        
    # ========================================
    #               Validation
    # ========================================

    print("")
    print("Running Validation...")
    epoch_i+=1
    

    t0 = time.time()

    model.eval()

    total_eval_loss = 0
    nb_eval_steps = 0

    # Evaluate data for one epoch
    for batch in test_dataloader:
        
        b_input_ids = batch[0].to(device)
        b_labels = batch[0].to(device)
        b_masks = batch[1].to(device)
        
        with torch.no_grad():        

            outputs  = model(b_input_ids, 
#                            token_type_ids=None, 
                             attention_mask = b_masks,
                            labels=b_labels)
          
            loss = outputs[0]  
            
        batch_loss = loss.item()
        total_eval_loss += batch_loss        

    avg_val_loss = total_eval_loss / len(test_dataloader)
    
    validation_time = format_time(time.time() - t0)    

    print("  Validation Loss: {0:.2f}".format(avg_val_loss))
    print("  Validation took: {:}".format(validation_time))
    if avg_val_loss < best_val_loss:
        print("***best model updated***")
        best_val_loss=avg_val_loss
        best_model =model
    else:
        patience_counter+=1

    # Record all statistics from this epoch.
    training_stats.append(
        {
            'epoch': epoch_i + 1,
            'Training Loss': avg_train_loss,
            'Valid. Loss': avg_val_loss,
            'Training Time': training_time,
            'Validation Time': validation_time
        }
    )

print("")
print("Training complete!")
print("Total training took {:} (h:mm:ss)".format(format_time(time.time()-total_t0)))

pkl_file=open("model_head_gpt.pkl", "wb")
pickle.dump(model, pkl_file)
pkl_file.close()

pkl_file=open("data.json", "w")
json.dump(training_stats, pkl_file)
pkl_file.close()

output=open('output_gpt_test.txt', 'w', encoding='latin1')
for item in test:
    q, a=item.split('<qeos>')
    q=q+'<qeos>'
    nq=q.split('<qbos>')[1].strip()
    a=a.strip().split('<eeos>')[0].strip()
    pred= sample_sequence(q, tokenizer, model, device=device)
    output.write('{}\t{}\t{}\n'.format(nq,pred,a))
    
output.close()
output=open('output_gpt_train.txt', 'w', encoding='latin1')
for item in train:
    q, a=item.split('<qeos>')
    q=q+'<qeos>'
    nq=q.split('<qbos>')[1].strip()
    a=a.strip().split('<eeos>')[0].strip()
    pred= sample_sequence(q, tokenizer, model, device=device)
    output.write('{}\t{}\t{}\n'.format(nq,pred,a))
    
output.close()
    




