from datasets import load_dataset
import time
from tqdm import tqdm

remote_dataset = load_dataset("hoskinson-center/proof-pile", "stack-exchange", streaming=True)

then = time.time()
for x in tqdm(remote_dataset["train"]): 
    pass
now = time.time()
print(f"TRAVERSED DATASET IN {now-then} SECONDS")
