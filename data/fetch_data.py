import sys
import os
import json
import ndjson

from pathlib import Path
from tqdm import tqdm 

import requests

import base64

def _blob_to_text(blob, creds): 
    resp = requests.get(blob["url"], auth=creds)
    if resp.status_code != 200: 
        raise AssertionError("Failed to fetch from Github API")

    resp_json = json.loads(resp.content.decode('utf-8'))
    return base64.b64decode(resp_json["content"])

def cring(creds):
    save_dir = "cring"
    Path(save_dir).mkdir(exist_ok=True)

    resp = requests.get('https://api.github.com/repos/aisejohan/cring/git/trees/2db2618ff70831002aeefbb16885ee42d5198db3',
            auth=creds)
    if resp.status_code != 200:
        raise AssertionError("Failed to catch cring from Github API")

    trees = json.loads(resp.content.decode("utf-8"))["tree"]
    
    print("DOWNLOADING CRING")
    for blob in tqdm(trees): 
        if blob["type"]=="blob" and blob["path"]!="license.tex": 
            decoded_content = _blob_to_text(blob, creds)
            with open(os.path.join(save_dir, blob["path"]), "wb") as f: 
                f.write(decoded_content)

    print("DONE DOWNLOADING CRING")
    
def napkin(creds): 
    save_dir = "napkin"
    Path(save_dir).mkdir(exist_ok=True)

    resp = requests.get('https://api.github.com/repos/vEnhance/napkin/git/trees/4f56c2ef5d0faf132ee14c15d96fb0f134d58bf0', 
            auth=creds)

    if resp.status_code != 200:
        raise AssertionError("Failed to catch napkin tree from Github API")
        
    trees = json.loads(resp.content.decode("utf-8"))["tree"]

    # We are assuming that we only want the files exactly two levels deep
    
    print("DOWNLOADING NAPKIN")
    for tree in tqdm(trees): 
        if tree["type"] == "tree": 
            resp = requests.get(tree["url"], auth=creds)
            blobs = json.loads(resp.content.decode('utf-8'))["tree"]
            for blob in blobs: 
                if blob["type"]=="blob": 
                    decoded_content = _blob_to_text(blob, creds)
                    with open(os.path.join(save_dir, blob["path"]), "wb") as f: 
                        f.write(decoded_content)
    print("DONE DOWNLOADING NAPKIN")


def main(): 
    creds = ("zhangir-azerbayev", os.environ["GITHUB_TOKEN"])
    #napkin(creds)
    cring(creds)

if __name__=="__main__": 
    main()
