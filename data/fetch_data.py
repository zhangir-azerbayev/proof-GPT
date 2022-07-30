import sys
import os

import json
import ndjson
import re 

from pathlib import Path
from tqdm import tqdm 

import requests
from tqdm import tqdm 

import base64

PROOFWIKI_URL = "https://zenodo.org/record/4902289/files/naturalproofs_proofwiki.json?download=1" 

def _get_dir_from_repo(author, repo, sha, repo_dir, save_path, creds):
    """
    This super unelegant solution is to get around the github api rate limit

    repo_dir must be top-level in the repo. 
    """
    Path(save_path).mkdir(parents=True, exist_ok=True) 
    archive_path = os.path.join(save_path, "archive.tar.gz") 
    tarball_url = "https://github.com/" + author + "/" + repo + "/archive/" + sha + ".tar.gz"

    os.system("wget -O " +  archive_path + " " + tarball_url)
    os.system("tar -xzf " + archive_path + " -C " + save_path)

    export_name = repo + "-" + sha 

    os.system("cp -r " + os.path.join(save_path, export_name, repo_dir, "*") + " " + save_path)
    os.system("rm -r " + os.path.join(save_path, export_name) + " " + archive_path)

def _delete_files_except_pattern(path, pattern):
    """
    recursively
    """
    for f in os.listdir(path):
        f_path = os.path.join(path, f)
        if os.path.isfile(f_path): 
            if not re.search(pattern, f):
                os.remove(f_path)
        elif not os.path.islink(f_path):
            _delete_files_except_pattern(f_path, pattern)

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

def coq(creds): 
    save_dir = "formal/coq"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    sources = [
                {
                    "author": "math-comp", 
                    "repo": "analysis", 
                    "sha": "2ae3b628d12cacdc000c4cd70e6f3cae26ecf429", 
                    "repo_dir": "theories", 
                    "save_path": os.path.join(save_dir, "analysis"), 
                }, 
                {
                    "author": "math-comp",
                    "repo": "math-comp", 
                    "sha": "65519a110ffdad7869b2a7cd08a2ddb51161b377", 
                    "repo_dir": "mathcomp", 
                    "save_path": os.path.join(save_dir, "math-comp"), 
                },
                {
                    "author": "math-comp",
                    "repo": "odd-order", 
                    "sha": "833261a01fd0c62b05ccbadfc0c682e0bc16a5e9", 
                    "repo_dir": "theories",
                    "save_path": os.path.join(save_dir, "odd-order"),
                }, 
                {
                    "author": "math-comp",
                    "repo": "Abel", 
                    "sha": "61d79aeb0acc1855e22882c484b73645df53b746", 
                    "repo_dir": "theories", 
                    "save_path": os.path.join(save_dir, "abel"), 
                }, 
            ]

    for source in sources: 
        _get_dir_from_repo(**source, creds=creds) 
        _delete_files_except_pattern(source["save_path"], r".*\.v")

def trench(): 
    save_dir = "books/trench"
    archive_path = os.path.join(save_dir, "trench.zip")
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    print("DOWNLOADING TRENCH")
    os.system("wget -O " + archive_path + \
            " \"https://digitalcommons.trinity.edu/cgi/viewcontent.cgi?filename=2&article=1006&context=mono&type=additional\"")
    print("DONE DOWNLOADING TRENCH")

    os.system("unzip " + archive_path + " -d " + save_dir)
    to_delete = ["trench.zip", "wtrench.sty", "SETEPS.TEX", "EPS"]
    os.system("rm -r " + " ".join([os.path.join(save_dir, f) for f in to_delete]))

def setmm(creds):
    """
    incomplete
    """
    save_dir = "formal/setmm"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    resp = _download_with_progress_bar('https://api.github.com/repos/metamath/set.mm/git/blobs/6ccd5acc803808bfc18e8513441a578a301caad5')
    resp_decoded = json.loads(resp.decode('utf-8'))
    src_encoded = base64.b64decode(resp_decoded["content"])
    src = src_encoded.decode('ascii')
    print(src[0:100000])

def stein(creds): 
    save_dir = "books/stein"
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    print("DOWNLOADING STEIN")
    resp = _download_with_progress_bar("https://api.github.com/repos/williamstein/ent/git/blobs/a70578277b1222c94dc395f7d5baaf9862afd166")
    print("DONE DOWNLOADING STEIN")

    resp_json = json.loads(resp.decode('utf-8'))
    src_encoded = base64.b64decode(resp_json["content"])
    src = src_encoded.decode('utf-8')

    with open(os.path.join(save_dir, "stein.tex"), "w") as f: 
        f.write(src)

def hol(testing=False): 
    save_dir = "formal/hol" 
    archive_path = os.path.join(save_dir, "hol.zip")
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    if not testing: 
        os.system("wget -O " +  archive_path + \
                " https://github.com/jrh13/hol-light/archive/538c62f.tar.gz")

    os.system("tar -xvf " + archive_path + " -C " + save_dir)
    os.system("mv " + os.path.join(save_dir, "hol-light-538c62f7cdb0df146752c83f85fa672ae3906b03/* ") + save_dir)
    os.system("rm -r " + os.path.join(save_dir, "hol-light-538c62f7cdb0df146752c83f85fa672ae3906b03"))
    os.system("rm " + archive_path)

    # all top level files are metaprogramming, so delete them
    for f in os.listdir(save_dir):
        f_path = os.path.join(save_dir, f)
        if os.path.isfile(f_path): 
            os.remove(f_path)

    _delete_files_except_pattern(save_dir, r".*\.ml|.*\.doc")

def afp(testing=False): 
    save_dir = "formal/afp" 
    archive_path = os.path.join(save_dir, "afp.zip")
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    if not testing: 
        os.system("wget -O " +  archive_path + \
                " https://github.com/isabelle-prover/mirror-afp-2021-1/archive/5a85b23.tar.gz")

    os.system("tar -xvf " + archive_path + " -C " + save_dir)
    os.system("mv " + os.path.join(save_dir, "mirror-afp-2021-1-5a85b23fb030c472d9a7b2d65a61e428f4eb8233/thys/* ") + save_dir)
    os.system("rm -r " + os.path.join(save_dir, "mirror-afp-2021-1-5a85b23fb030c472d9a7b2d65a61e428f4eb8233"))
    os.system("rm " + archive_path)

    _delete_files_except_pattern(save_dir, r".*\.thy|.*\.tex")

def naturalproofs_proofwiki(testing=False):
    save_dir = "books/proofwiki"
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
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

def mizar(creds): 
    save_dir = "formal/mizar"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    resp = requests.get("https://api.github.com/repos/zhangir-azerbayev/mizar-mirror/git/trees/ce8e9735fd7a4d3488069c48da76bc622aec46ec") 
    if resp.status_code != 200: 
        raise AssertionError("Failed to fetch mizar from Github API")

    resp_json = resp.json()
    tree = resp_json["tree"]
    
    print("DOWNLOADING MIZAR")
    for blob in tqdm(tree): 
        assert blob["type"] == "blob"

        src = _blob_to_text(blob, creds)
        # idk why next line is necessary but it is 
        src = src.decode("utf-8")
        # mml files have licensing information from lines 2-12
        src = "\n".join([x 
            for i, x in enumerate(src.split("\n"))
            if i not in range(2, 13)])

        save_path = os.path.join(save_dir, blob["path"])
        with open(save_path, "w") as f: 
            f.write(src)
    print("DONE DOWNLOADING MIZAR")


def hott(creds): 
    save_dir = "books/hott"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    resp = requests.get("https://api.github.com/repos/HoTT/book/git/trees/781565e93979f926001a353bf4ee1284ffa4fcb0", auth=creds)
    if resp.status_code != 200:
        raise AssertionError("Failed to fetch HoTT book from Github API")

    resp_json = resp.json()
    tree = resp_json["tree"]
    blobs = [blob for blob in tree if blob["type"] == "blob"]

    banned = ["back.tex", 
              "bmpsize-hack.tex", 
              "main.tex",]

    banned_rgx = r"opt|cover|front|hott"
    
    print("DOWNLOADING HOTT BOOK")
    for blob in tqdm(blobs): 
        if blob["path"][-4:] == ".tex" and \
                blob["path"] not in banned \
                and not re.match(banned_rgx, blob["path"]):
            src_enc = _blob_to_text(blob, creds)
            src = src_enc.decode("utf-8")
            
            save_path = os.path.join(save_dir, blob["path"])
            with open(save_path, "w") as f:
                f.write(src)

    print("DONE DOWNLOADING HOTT BOOK")

def stacks(creds): 
    save_dir = "books/stacks"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    resp = requests.get("https://api.github.com/repos/stacks/stacks-project/git/trees/0a847ff5e41b47795be075e130e7810173b35933", 
            auth=creds)
    resp_json = json.loads(resp.content.decode('utf-8'))
    print(json.dumps(resp_json, indent=4))
    # assumes everything we need is a top level file, which is true for this commit.  
    blobs = resp_json["tree"]
    print("DOWNLOADING STACKS")
    for blob in tqdm(blobs):
        if blob["type"]=="blob" and blob["path"][-4:] == ".tex" and blob["path"]!="fdl.tex": 
            decoded_content = _blob_to_text(blob, creds)
            with open(os.path.join(save_dir, blob["path"]), "wb") as f: 
                f.write(decoded_content)
    print("DONE DOWNLOADING STACKS")


def cring(creds):
    save_dir = "books/cring"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

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
    save_dir = "books/napkin"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

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
    #naturalproofs_proofwiki(testing=False)
    #stacks(creds)
    #mizar(creds)
    #afp(testing=False)
    #setmm(creds)
    #trench()
    #hott(creds)
    #stein(creds)
    coq(creds)

if __name__=="__main__": 
    main()
