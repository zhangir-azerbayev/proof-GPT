# Data 
This directory only exists for reproducibility/iteration purposes. If you want to use the MathPile dataset, download it from the Huggingface hub. 

Running `fetch_raw_data.py` will download the entire X GB pre-training corpus. Running `make_dataset.py` will create a Huggingface dataset instance. 

Please note that the data fetching scripts do *a lot* of OS operations and have not been tested for safety. I recommend running them in a sandbox. 

For some reasoning arXiv 1510 is failing to download. 
