# -*- coding: utf-8 -*-

# author: kagnes
# created: 2026/04/15

import os
import re


def get_meta(f):
    metadt = {}
    with open(f, 'r', encoding='utf-8') as fr:
        for i, line in enumerate(fr):
            docid, hunmeta, profile, year, corpus = line.strip().split('\t')
            metadt[docid] = [docid, hunmeta, profile, year, corpus]
    return metadt


def process_file(cpath, fname, metadata, outfile, feats):
    actsent = []
    with open(outfile, 'a', encoding='utf-8') as fw:
        with open(cpath + '/' + fname, 'r', encoding='utf-8') as fr:
            for line in fr:
                cells = line.rstrip('\n').split('\t')
                if len(cells) == 1:
                    count_hits, hit_cells = get_hits(actsent)
                    if count_hits > 0:
                        zipped = list(zip(feats, metadata))
                        metaline = ' '.join(['{}="{}"'.format(tup[0], tup[1]) for tup in zipped])
                        print('# file="{}" {} hits="{}" ids="{}"'.format(fname, metaline, count_hits, ' '.join(hit_cells)), file=fw)
                        for item in actsent:
                            print('\t'.join(item), file=fw)
                        print('', file=fw)
                    actsent = []
                else:
                    actsent.append(cells)


def get_hits(actsent):
    count_hits = 0
    hit_cells = []
    for cells in actsent:
        hit = re.search(r'^(prefixed|detached).*\}$', cells[-1], flags=re.I)
        if hit:
            count_hits += 1
            hit_cells.append(cells[0])
    return count_hits, hit_cells


""" MAIN """

corpus_path = './unified_omk_tmk_vpfx'
meta_file = './final_meta_needed.tsv'
feats = ['docid', 'hunmeta', 'profile', 'year', 'corpus']
outfile = 'ohc_mhc_hits.txt'

metadt = get_meta(meta_file)
files = sorted(os.listdir(corpus_path))

for i, fname in enumerate(files):
    print('{} : {}'.format(i+1, fname))
    docid = fname.replace('.tsv', '')
    process_file(corpus_path, fname, metadt[docid], outfile, feats)
