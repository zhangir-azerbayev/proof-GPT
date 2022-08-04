import os
import sys 
from pathlib import Path
import datetime

import tarfile
import xml.etree.ElementTree as ET 
from tqdm import tqdm
import re 
from itertools import chain

import shutil

import arxiv 

def batch_loader(seq, size):
    """
    Iterator that takes in a list `seq` and returns
    chunks of size `size` 
    """
    return [seq[pos:pos + size] for pos in range(0, len(seq), size)]


def _delete_files_except_pattern(path, pattern, transform = lambda x: None):
    """
    recursively
    """
    for f in os.listdir(path):
        f_path = os.path.join(path, f)
        if os.path.isfile(f_path): 
            if not re.search(pattern, f):
                os.remove(f_path)
            else: 
                transform(f_path)
        elif not os.path.islink(f_path):
            _delete_files_except_pattern(f_path, pattern, transform=transform)

def clean_tex_file(path): 
    with open(path, encoding="utf-8") as f: 
        try: 
            src = f.read()
        except UnicodeDecodeError: 
            print(f"UnicodeDecodeError at {path} with utf-8. Try utf-16")
            try: 
                with open(path, encoding="utf-16-le") as fle: 
                    src = fle.read()
                    print("utf-16 successful")
            except UnicodeDecodeError: 
                print("utf-16 decoding failed. Deleting this file.")
                print("This issue should only occur with a handful of quite old files. Continuing...\n")
                return 

    end = re.search(r"\\end\{document\}", src)
    if end: 
        src = src[:end.span()[1]]

    bib = re.search(r"\\Refs|\\begin\{thebibliography\}", src)
    if bib:
        src = src[:bib.span()[0]]

    with open(path, "w", encoding="utf-8") as f: 
        f.write(src)

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
                eyed = zipped_name[:-len(".gz")]
                if tarfile.is_tarfile(zipped_path): 
                    article_dir = os.path.join(subpath, eyed)
                    Path(article_dir).mkdir()
                    os.system("tar -xzf " + zipped_path + " -C " + article_dir)
                    os.remove(zipped_path)
                else: 
                    os.system("gzip -d " + zipped_path)
                    unzipped_path = os.path.join(subpath, eyed)
                    os.rename(unzipped_path, unzipped_path + ".tex")
            else: 
                os.remove(zipped_path)

    _delete_files_except_pattern(subpath, r".*\.tex", transform=clean_tex_file)
    #os.remove(tarball_path)

def process_tarball(tarball_name, save_dir): 
    tarball_path = os.path.join(save_dir, tarball_name)
    untar_cmd = "tar -xvf " + tarball_path + " -C " + save_dir
    os.system(untar_cmd)
    
    last_ = tarball_name.rfind("_")
    second_last_ = tarball_name.rfind("_", 0, last_)
    subdir = tarball_name[second_last_+1:last_]
    
    subpath = os.path.join(save_dir, subdir)
    listdir = os.listdir(subpath)

    ids = [x[:-3] for x in listdir if x[-3:]==".gz"]

    print("IDS TO FILTER:", len(ids))
    
    # the arXiv metadata API can only handle a few hundred requests
    # at a time, and this is a little hack to get around it 
    id_chunks = batch_loader(ids, 511)
    chunk_iterators = []
    for chunk in id_chunks: 
        chunk_iterators.append(arxiv.Search(
                id_list = chunk, 
                max_results=float('inf')
        ).results())


    math_ids = []
    print("filtering for math articles")
    for result in tqdm(chain(*chunk_iterators), total=len(ids)): 
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
                article_dir = os.path.join(subpath, eyed)
                Path(article_dir).mkdir()
                os.system("tar -xzf " + zipped_path + " -C " + article_dir)
                os.remove(zipped_path)
            else: 
                os.system("gzip -d " + zipped_path)
                unzipped_path = os.path.join(subpath, eyed)
                os.rename(unzipped_path, unzipped_path + ".tex")
    
    _delete_files_except_pattern(subpath, r".*\.tex", transform=clean_tex_file)
    #os.remove(tarball_path)

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
    
    shards_and_dates = []
    for child in root: 
        if child.tag == "file":
            shard = child[1].text # the index of filename
            yymm = child[9].text # the index of yymm
            shards_and_dates.append((shard, yymm))

    shards_and_dates = [shards_and_dates[0], shards_and_dates[250], shards_and_dates[5000]]
     
    format_cutoff = datetime.datetime(2007, 3, 1)
    for shard, yymm in tqdm(shards_and_dates): 
        print("SHARD: ", shard)
        os.system(f"s3cmd get s3://arxiv/" + shard + \
                " --requester-pays " + save_dir) 
        tarball_name=shard[shard.rindex("/")+1:]
        
        # nb this code will stop working in 2051 ;) 
        year = int("19" + yymm[:2]) if int(yymm[:2])>50 else int("20"+yymm[:2])
        if datetime.datetime(year, int(yymm[2:]), 1)<=format_cutoff: 
            process_tarball_old_scheme(tarball_name, save_dir)
        else: 
            process_tarball(tarball_name, save_dir) 

    #os.remove(manifest_path)

if __name__=="__main__": 
    main()
