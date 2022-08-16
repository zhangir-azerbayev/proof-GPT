from transformers import AutoTokenizer
import datasets
from datasets import load_dataset

from itertools import islice

from tqdm import tqdm

tokenizer = AutoTokenizer.from_pretrained("gpt2")

to_concat = ["books", "formal", "wiki", "stack-exchange", "math-dataset"]

concat_set = datasets.concatenate_datasets([load_dataset("hoskinson-center/proof-pile", 
    x, streaming=True)["train"] for x in to_concat])

dataset = datasets.interleave_datasets([load_dataset("hoskinson-center/proof-pile", "arxiv", 
    streaming=True)["train"], concat_set], seed=20) # 20 is the random seed

def get_text_iterator():
    for x in dataset: yield x["text"]

text_iterator = get_text_iterator()

new_tokenizer = tokenizer.train_new_from_iterator(text_iterator, 35_000)

new_tokenizer.save_pretrained("tokenizer_v1")



