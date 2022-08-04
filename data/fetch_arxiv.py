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
    with open(path) as f: 
        try: 
            src = f.read()
        except UnicodeDecodeError: 
            print(f"UnicodeDecodeError at {path}. Deleting this file.")
            print("This issue should only occur with a handful of quite old files. Continuing...\n")
            os.remove(path)
            return 

    end = re.search(r"\\end\{document\}", src)
    if end: 
        src = src[:end.span()[1]]

    bib = re.search(r"\\Refs|\\begin\{thebibliography\}", src)
    if bib:
        src = src[:bib.span()[0]]

    with open(path, "w") as f: 
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
    """
    listdir = os.listdir(subpath)
    for fle in listdir: 
        path = os.path.join(subpath, fle)
        if not re.match(r".*\.tex", fle): 
            if os.path.isfile(path): 
                os.remove(path)
            else: 
                shutil.rmtree(path)
        else: 
            clean_tex_file(path)
    """
    #os.remove(tarball_path)

def process_tarball(tarball_name, save_dir): 
    tarball_path = os.path.join(save_dir, tarball_name)
    untar_cmd = "tar -xvf " + tarball_path + " -C " + save_dir
    print("UNTAR CMD: ", untar_cmd)
    os.system(untar_cmd)
    
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
                article_dir = os.path.join(subpath, eyed)
                Path(article_dir).mkdir()
                os.system("tar -xzf " + zipped_path + " -C " + article_dir)
                os.remove(zipped_path)
            else: 
                os.system("gzip -d " + zipped_path)
                unzipped_path = os.path.join(subpath, eyed)
                os.rename(unzipped_path, unzipped_path + ".tex")
    
    #_delete_files_except_pattern(subpath, r".*\.tex", transform=clean_tex_file)
    """
    listdir = os.listdir(subpath)
    for fle in listdir: 
        path = os.path.join(subpath, fle)
        if not re.match(r".*\.tex", fle): 
            if os.path.isfile(path): 
                os.remove(path)
            else: 
                shutil.rmtree(path)
        else: 
            clean_tex_file(path)
    """

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
    
    shards_to_get = []
    yymms = []
    for child in root: 
        if child.tag == "file":
            fle_field = child[1] # the index of filename
            shards_to_get.append(fle_field.text)
            yymms.append(child[9].text)
    
    # delete this line later
    shards_to_get = [shards_to_get[2000]]
    
    format_cutoff = datetime.datetime(2007, 3, 1)
    for shard, yymm in tqdm(zip(shards_to_get, yymms), total=len(yymms)): 
        print("SHARD: ", shard)
        os.system(f"s3cmd get s3://arxiv/" + shard + \
                " --requester-pays " + save_dir) 
        tarball_name=shard[shard.rindex("/")+1:]
        
        # nb this code will stop working in 2051 ;) 
        print(yymm)
        year = int("19" + yymm[:2]) if int(yymm[:2])>50 else int("20"+yymm[:2])
        print("YEAR: ", year)
        if datetime.datetime(year, int(yymm[2:]), 1)<=format_cutoff: 
            print("GOT TO IF")
            process_tarball_old_scheme(tarball_name, save_dir)
        else: 
            print("GOT TO ELSE")
            process_tarball(tarball_name, save_dir) 

    #os.remove(manifest_path)

if __name__=="__main__": 
    main()
