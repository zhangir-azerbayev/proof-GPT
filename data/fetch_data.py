import sys
import os
import json
import ndjson

from pathlib import Path
from tqdm import tqdm 

import requests
from tqdm import tqdm 

import base64

PROOFWIKI_URL = "https://zenodo.org/record/4902289/files/naturalproofs_proofwiki.json?download=1" 

def _download_with_progress_bar(url): 
    response = requests.get(url, stream=True)
    total_size_in_bytes= int(response.headers.get('content-length', 0))
    block_size = 1024 #1 Kibibyte
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
    to_return = bytearray()
    for data in response.iter_content(block_size):
        progress_bar.update(len(data))
        to_return += data
    progress_bar.close()
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        raise AssertionError("ERROR, something went wrong")

    return to_return 

def _blob_to_text(blob, creds): 
    resp = requests.get(blob["url"], auth=creds)
    if resp.status_code != 200: 
        raise AssertionError("Failed to fetch from Github API")

    resp_json = json.loads(resp.content.decode('utf-8'))
    return base64.b64decode(resp_json["content"])

def naturalproofs_proofwiki(testing=False):
    save_dir = "proofwiki"
    Path(save_dir).mkdir(exist_ok=True)
    
    if testing: 
        with open("naturalproofs/proofwiki.json") as f: 
            struct = json.load(f)
    else: 
        print("DOWNLOADING PROOFWIKI")
        resp = _download_with_progress_bar(PROOFWIKI_URL)
        struct = json.loads(resp.decode('utf-8'))
        print("DONE DOWNLOADING PROOFWIKI")

    for thm in struct["dataset"]["theorems"]: 
        if thm["contents"]: 
            thm_string = "\\section{" + thm["label"] + "}\n"
            thm_string += "Tags: " + ", ".join(thm["categories"]).replace("/", ": ") + "\n\n"

            thm_string += "\\begin{theorem}\n" + "\n".join(thm["contents"]) + "\n\\end{theorem}\n\n"

            for proof in thm["proofs"]:
                thm_string += "\\begin{proof}\n" + "\n".join(proof["contents"]) + "\n\\end{proof}\n\n"

            with open(os.path.join(save_dir, str(thm["id"])+".txt"), "w") as f: 
                f.write(thm_string)

    defn_string = ""
    for defn in struct["dataset"]["definitions"]: 
        if defn["contents"]: 
            defn_string += "\\begin{definition}[" + defn["label"] + "]\n" + "\n".join(defn["contents"]) + "\n\\end{definition}\n\n"

    with open(os.path.join(save_dir, "defs.txt"), "w") as f: 
        f.write(defn_string)


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
    #cring(creds)
    naturalproofs_proofwiki(testing=False)

if __name__=="__main__": 
    main()
