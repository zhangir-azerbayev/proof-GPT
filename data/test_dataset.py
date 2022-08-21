from datasets import load_dataset
import time
from tqdm import tqdm

configs = ["arxiv", "stack-exchange", "books", "formal", "wiki", "stack-exchange", "math-dataset"]

total_time = 0 
for x in configs: 
    remote_dataset = load_dataset("hoskinson-center/proof-pile", x, streaming=True)

    print(remote_dataset)
    then = time.time()
    for x in tqdm(remote_dataset["train"]): 
        pass

    now = time.time()
    print(f"CONFIG {x} TRAVERSED IN {now-then} SECONDS")
    total_time += now-then 

print(f"ENTIRE DATASET TRAVERSED IN {total_time} SECONDS")
