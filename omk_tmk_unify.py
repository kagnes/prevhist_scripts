# -*- coding: utf-8 -*-

# author: kagnes
# created: 2026/02/20

import os
import re


def get_omk_morf(inpath):
    relevant_files = []
    with open(inpath+'ohc_meta.tsv', 'r', encoding='utf-8') as fr:
        for line in fr:
            line = line.strip()
            if line.endswith('morf'):
                relevant_files.append(line.split('\t')[0])
    return relevant_files


def check_omk_cells(inpath, files):
    file_dt = {}
    to_delete = re.compile(r'^(ERROR|FAIL|FRAG|LANG|STRIKE)')
    for f in files:
        file_dt[f] = []
        with open(inpath+'ohc/'+f, 'r', encoding='utf-8') as fr:
            for line in fr:
                cells = line.rstrip('\n').split('\t')
                if len(cells) == 1:
                    pass
                elif len(cells) == 9:
                    cells = [''] if to_delete.search(cells[6]) else [cells[2], cells[3], cells[7], cells[8]]
                else:
                    cells = cells[:-1]
                    cells = [''] if to_delete.search(cells[6]) else [cells[2], cells[3], cells[7], cells[8]]
                file_dt[f].append(cells)
    return file_dt


def reorder_omk_cells(file_dt):
    for fname, content in file_dt.items():
        new_content = []
        for item in content:
            if len(item) == 1:
                pass
            elif re.search(r'\.QPtl', item[-1]):
                item1 = [item[0], item[1].rstrip('-e'), item[2], item[3].rstrip('.QPtl')]
                new_content.append(item1)
                item2 = ['', '-e', '-e', 'QPtl']
                new_content.append(item2)
            elif re.search(r'^[\.\,\!\?\;\:\"\'\u201c\u201d\u2018\u2019\u2014\-\(\)].', item[1]) and item[-1] != 'QPtl':
                punct_type = re.search(r'^([\.\,\!\?\;\:\"\'\u201c\u201d\u2018\u2019\u2014\-\(\)]).', item[1]).group(1)
                item2 = ['', punct_type, punct_type, 'Punct']
                item[1] = item[1][1:]
                new_content.append(item2)
                new_content.append(item)
            elif re.search(r'.[\.\,\!\?\;\:\"\'\u201c\u201d\u2018\u2019\u2014\-\(\)]$', item[1]):
                punct_type = re.search(r'.([\.\,\!\?\;\:\"\'\u201c\u201d\u2018\u2019\u2014\-\(\)])$', item[1]).group(1)
                item2 = ['', punct_type, punct_type, 'Punct']
                item[1] = item[1][:-1]
                new_content.append(item)
                new_content.append(item2)
            elif re.search(r'^[\.\,\!\?\;\:\"\'\u201c\u201d\u2018\u2019\u2014\-\(\)]$', item[1]):
                item[2] = item[1]
                item[-1] = 'Punct'
                new_content.append(item)
            else:
                new_content.append(item)

        newer_content = []
        for item in new_content:
            newer_content.append(item)
            if item[-1] == 'Punct' and item[-2] in '.?!':
                newer_content.append([''])

        newest_content = []
        id_num = 0
        for i, item in enumerate(newer_content):
            if i == 0 and len(item) == 1:
                pass
            elif i == len(newer_content)-1 and len(item) == 1:
                pass
            elif len(item) == 1:
                newest_content.append(item)
            else:
                id_num += 1
                new_item = [str(id_num)]
                new_item.extend(item)
                newest_content.append(new_item)
        file_dt[fname] = newest_content
    return file_dt


def check_tmk_cells(inpath, files):
    tmk_file_dt = {}
    for f in files:
        tmk_file_dt[f] = []
        with open(inpath+f, 'r', encoding='utf-8') as fr:
            for line in fr:
                cells = line.rstrip('\n').split('\t')
                if len(cells) == 1:
                    tmk_file_dt[f].append(cells)
                else:
                    new_cells = [cells[1], cells[3], cells[4], cells[5]]
                    tmk_file_dt[f].append(new_cells)

    return tmk_file_dt


def reorder_tmk_cells(tmk_file_dt):
    for fname, content in tmk_file_dt.items():
        new_content = []
        for item in content:
            if len(item) == 1:
                pass
            elif re.search(r'\.QPtl', item[-1]):
                item1 = [item[0], item[1].rstrip('-e'), item[2], item[3].rstrip('.QPtl')]
                new_content.append(item1)
                item2 = ['', '-e', '-e', 'QPtl']
                new_content.append(item2)
            elif re.search(r'^[\.\,\!\?\;\:\"\'\u201c\u201d\u2018\u2019\u2014\-\(\)].', item[1]) and item[-1] != 'QPtl':
                punct_type = re.search(r'^([\.\,\!\?\;\:\"\'\u201c\u201d\u2018\u2019\u2014\-\(\)]).', item[1]).group(1)
                item2 = ['', punct_type, punct_type, 'Punct']
                item[1] = item[1][1:]
                new_content.append(item2)
                new_content.append(item)
            elif re.search(r'.[\.\,\!\?\;\:\"\'\u201c\u201d\u2018\u2019\u2014\-\(\)]$', item[1]):
                punct_type = re.search(r'.([\.\,\!\?\;\:\"\'\u201c\u201d\u2018\u2019\u2014\-\(\)])$', item[1]).group(1)
                item2 = ['', punct_type, punct_type, 'Punct']
                item[1] = item[1][:-1]
                new_content.append(item)
                new_content.append(item2)
            elif re.search(r'^[\.\,\!\?\;\:\"\'\u201c\u201d\u2018\u2019\u2014\-\(\)]$', item[1]):
                item[2] = item[1]
                item[-1] = 'Punct'
                new_content.append(item)
            elif item[0].startswith('{\\!'):
                pass
            else:
                new_content.append(item)

        newer_content = []
        for item in new_content:
            newer_content.append(item)
            if item[-1] == 'Punct' and item[-2] in '.?!':
                newer_content.append([''])

        newest_content = []
        id_num = 0
        for i, item in enumerate(newer_content):
            if i == 0 and len(item) == 1:
                pass
            elif i == len(newer_content)-1 and len(item) == 1:
                pass
            elif len(item) == 1:
                newest_content.append(item)
            else:
                id_num += 1
                new_item = [str(id_num)]
                new_item.extend(item)
                newest_content.append(new_item)
        tmk_file_dt[fname] = newest_content
        
    return tmk_file_dt


def unify_meta(omk_files, tmk_files, omk_path, tmk_path):
    omk_ls = omk_files.keys()
    omk_metadt = {}
    with open(omk_path+'ohc_meta.tsv', 'r', encoding='utf-8') as fr:
        for i, line in enumerate(fr):
            if i > 0:
                fname, fid, title, orig_date, mod_date, filetype = line.rstrip('\n').split('\t')
                if fname in omk_ls:
                    omk_metadt[fname] = {"fname": fname, "fid": fid, "title": title, "address_rel": "_", 
                                     "address_sex": "_", 
                                     "address_socstat": "_", 
                                     "address_name": "_", "author_name": "_", 
                                     "hunmeta": "_", "orig_date": orig_date, 
                                     "orig_place": "_", "profile": "_", 
                                     "year": mod_date.strip('~'), "corpus": "ÓMK"}
    
    collided_metadt = {}
    with open(tmk_path+'tmk/treebank_like_mhc/mhc_meta.tsv', 'r', encoding='utf-8') as fr:
        for i, line in enumerate(fr):
            if i > 0:
                fname, fid, address_rel, address_sex, address_socstat, address_name, author_name, hunmeta, orig_date, orig_place, profile, year = line.rstrip('\n').split('\t')
                collided_metadt[fname] = {"fname": fname, "fid": fid, "title": "_", "address_rel": address_rel, 
                                     "address_sex": address_sex, 
                                     "address_socstat": address_socstat, 
                                     "address_name": address_name, "author_name": author_name, 
                                     "hunmeta": hunmeta, "orig_date": orig_date, 
                                     "orig_place": orig_place, "profile": profile, 
                                     "year": year, "corpus": "TMK"}
    
    for fname, data in omk_metadt.items():
        collided_metadt[fname] = data

    with open('omk_tmk_meta.tsv', 'a', encoding='utf-8') as fw:
        print("fname\tfid\ttitle\taddress_rel\taddress_sex\taddress_socstat\taddress_name\tauthor_name\thunmeta\torig_date\torig_place\tprofile\tyear\tcorpus", file=fw)
        for k, data in collided_metadt.items():
            row = '\t'.join(data.values())
            print(row, file=fw)


def write_unified_corpus(outpath, omk, tmk):

    for fname, data in omk.items():
        with open(outpath+fname, 'a', encoding='utf-8') as fw:
            for item in data:
                row = '\t'.join(item)
                print(row, file=fw)

    for fname, data in tmk.items():
        with open(outpath+fname, 'a', encoding='utf-8') as fw:
            for item in data:
                row = '\t'.join(item)
                print(row, file=fw)


""" MAIN """

inpath = './'
omk_path = 'omk/treebank_like_ohc/'
tmk_path = 'tmk/treebank_like_mhc/mhc/'
outpath = './unified_omk_tmk/'

relevant_files = get_omk_morf(inpath+omk_path)
file_dt = check_omk_cells(inpath+omk_path, relevant_files)
file_dt = reorder_omk_cells(file_dt)

relevant_files = os.listdir(inpath+tmk_path)
tmk_file_dt = check_tmk_cells(inpath+tmk_path, relevant_files)
tmk_file_dt = reorder_tmk_cells(tmk_file_dt)

# unify_meta(file_dt, tmk_file_dt, inpath+omk_path, inpath)
write_unified_corpus(outpath, file_dt, tmk_file_dt)
