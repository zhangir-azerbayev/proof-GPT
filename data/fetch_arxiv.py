import os
import sys 
from pathlib import Path
import datetime

import tarfile
import xml.etree.ElementTree as ET 
from tqdm import tqdm
import re 

import shutil

import arxiv 

def process_tarball_old_scheme(tarball_name, save_dir): 
    tarball_path = os.path.join(save_dir, tarball_name)
    os.system("tar -xf " + tarball_path + " -C " + save_dir)

    last_ = tarball_name.rfind("_")
    second_last_ = tarball_name.rfind("_", 0, last_)
    subdir = tarball_name[second_last_+1:last_]
    
    subpath = os.path.join(save_dir, subdir)
    zipped_names = os.listdir(subpath)

    for zipped_name in zipped_names: 
        if zipped_name[-len(".gz"):]==".gz": 
            zipped_path = os.path.join(subpath, zipped_name)
            if re.match(r"math", zipped_name): 
                if tarfile.is_tarfile(zipped_path): 
                    os.system("tar -xzf " + zipped_path + " -C " + subpath)
                    os.remove(zipped_path)
                else: 
                    os.system("gzip -d " + zipped_path)
                    unzipped_path = os.path.join(subpath, zipped_name[:-len(".gz")])
                    os.rename(unzipped_path, unzipped_path + ".tex")
            else: 
                os.remove(zipped_path)

    listdir = os.listdir(subpath)
    for fle in listdir: 
        path = os.path.join(subpath, fle)
        if not re.match(r".*\.tex", fle): 
            if os.path.isfile(path): 
                os.remove(path)
            else: 
                shutil.rmtree(path)

def process_tarball(tarball_name, save_dir): 
    tarball_path = os.path.join(save_dir, tarball_name)
    os.system("tar -xf " + tarball_path + " -C " + save_dir)
    
    last_ = tarball_name.rfind("_")
    second_last_ = tarball_name.rfind("_", 0, last_)
    subdir = tarball_name[second_last_+1:last_]
    
    subpath = os.path.join(save_dir, subdir)
    listdir = os.listdir(subpath)

    ids = [x[:-3] for x in listdir if x[-3:]==".gz"]

    search = arxiv.Search(
            id_list = ids, 
            max_results=float('inf')
    )

    math_ids = []
    print("filtering for math articles")
    for result in tqdm(search.results()): 
        if result.primary_category[:4]=="math": 
            id_beg = result.entry_id.rfind("/")+1
            id_end = result.entry_id.rfind("v")
            math_id = result.entry_id[id_beg:id_end]
            math_ids.append(math_id)
    
    "unzipping math papers"
    for eyed in ids: 
        if eyed in math_ids: 
            zipped_path = os.path.join(subpath, eyed + ".gz")

            if tarfile.is_tarfile(zipped_path): 
                os.system("tar -xzf " + zipped_path + " -C " + subpath)
                os.remove(zipped_path)
            else: 
                os.system("gzip -d " + zipped_path)
                unzipped_path = os.path.join(subpath, eyed)
                os.rename(unzipped_path, unzipped_path + ".tex")

    listdir = os.listdir(subpath)
    for fle in listdir: 
        path = os.path.join(subpath, fle)
        if not re.match(r".*\.tex", fle): 
            if os.path.isfile(path): 
                os.remove(path)
            else: 
                shutil.rmtree(path)

def main(): 
    """
    Warning: this code is *extremely* brittle and will break 
    if arXiv changes their scheme for formatting data in 
    any way
    """
    save_dir = "arxiv"
    Path(save_dir).mkdir(exist_ok=True) 
    manifest_path = os.path.join(save_dir, "manifest.xml")
    
    os.system(f"s3cmd get s3://arxiv/src/arXiv_src_manifest.xml --requester-pays {manifest_path}") 

    tree = ET.parse(manifest_path)
    root = tree.getroot()
    
    shards_to_get = []
    yymms = []
    for child in root: 
        if child.tag == "file":
            fle_field = child[1] # the index of filename
            shards_to_get.append(fle_field.text)
            yymms.append(child[9].text)
    # delete this line later
    print(yymms)
    sys.exit()
    shards_to_get = [shards_to_get[0], shards_to_get[1000]]
    
    format_cutoff = datetime.datetime(2007, 3, 1)
    for shard, yymm in tqdm(zip(shards_to_get, yymms)): 
        print("SHARD: ", shard)
        os.system(f"s3cmd get s3://arxiv/" + shard + \
                " --requester-pays " + save_dir) 
        tarball_name=shard[shard.rindex("/")+1:]
        if datetime.datetime(yymm[:2], yymm[2:], 1)<=format_cutoff: 
            process_tarball_old_scheme(tarball_name, save_dir)
        else: 
            process_tarball(tarball_name, save_dir)
    
if __name__=="__main__": 
    main()
