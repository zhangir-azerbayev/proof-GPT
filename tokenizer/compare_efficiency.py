from typing import Dict, List

from functools import reduce
from itertools import islice

from tqdm import tqdm

import datasets
from datasets import load_dataset
from transformers import AutoTokenizer

from itertools import islice
import sys

import logging

logging.getLogger("transformers").setLevel(logging.ERROR)

split = sys.argv[1]

configs = ["arxiv", "books", "formal", "wiki", 
        "stack-exchange", "math-dataset"]

dataset = datasets.concatenate_datasets([load_dataset("hoskinson-center/proof-pile", 
    x, streaming=True)[split]
    for x in configs])

old_count = 0
small_count = 0 
mid_count = 0 
big_count = 0

old_tok = AutoTokenizer.from_pretrained("gpt2")
small_tok = AutoTokenizer.from_pretrained("tokenizer_35000")
mid_tok = AutoTokenizer.from_pretrained("tokenizer_40000")
big_tok = AutoTokenizer.from_pretrained("tokenizer_50000")

for row in tqdm(dataset):
    text = row["text"]
    old_count += len(old_tok(text)["input_ids"])
    small_count += len(small_tok(text)["input_ids"])
    mid_count += len(mid_tok(text)["input_ids"])
    big_count += len(big_tok(text)["input_ids"])


result_string = "GPT2 TOKENIZER: {:.5E}".format(old_count)
result_string += "\n35K TOKENIZER: {:.5E}".format(small_count)
result_string += "\n40K TOKENIZER: {:.5E}".format(mid_count)
result_string += "\n50k TOKENIZER: {:.5E}".format(big_count)

with open(f"{split}_efficiency.txt", "w") as f: 
    f.write(result_string)

print(result_string)
