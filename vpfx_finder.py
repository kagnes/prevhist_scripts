# -*- coding: utf-8 -*-

# author: kagnes
# created: 2026/03/28

import os
import re
import requests


def constype_converter(norm, ana):
    if 'Inf' in ana:
        constype = '-ni'
    elif 'vÁn' in ana:
        constype = '-vÁn'
    elif '=iglAn' in ana:
        constype = '-iglAn'
    elif '_Nact=tA' in ana or '_Subj=tA' in ana:
        constype = '-tA'
    elif 'PartPrf' in ana:
        constype = '-(O)(t)t'
    elif 'PartAdv' in ana:
        constype = '-vA'
    elif 'PartPrs' in ana:
        constype = '-Ó'
    elif 'PartFut' in ana:
        constype = '-AndÓ'
    elif 'V.' in ana and re.search(r'[SP][123]', ana):
        constype = 'FIN'
    elif 'For_keppen' in ana:
        constype = '-képpen'
    elif 'Abil' in ana:
        constype = '-hAtÓ'
    else:
        constype = '?'

    return constype


def constype_str_converter(norm, ana, verb_lemma):
    if re.search(r'[óő]$', verb_lemma):
        constype = '-Ó'
        verb_lemma = verb_lemma[:-1]
    elif re.search(r's[áé]g$', verb_lemma):
        constype = '-sÁg'
        verb_lemma = re.sub(r's[áé]g$', '', verb_lemma)
    elif re.search(r'(hatatlan|hetetlen)$', verb_lemma):
        constype = '-hAtAtlAn'
        verb_lemma = re.sub(r'(hatatlan|hetetlen)$', '', verb_lemma)
    elif re.search(r'(atlan|etlen)$', verb_lemma):
        constype = '-AtlAn'
        verb_lemma = re.sub(r'(atlan|etlen)$', '', verb_lemma)
    elif re.search(r'[áé]s$', verb_lemma):
        constype = '-Ás'
        verb_lemma = re.sub(r'[áé]s$', '', verb_lemma)
    else:
        constype = '?'

    return constype, verb_lemma


def vpfx_marker(tid, orig, norm, lemma, ana, prevs, vpfx_standardizer, prev_by_len):
    lemma = re.sub(r"_'.*'$", "", lemma)
    lemma = lemma.replace('jő_jön', 'jön')
    lemma = lemma.replace('hí_hív', 'hív')
    lemma = lemma.replace('szí_szív', 'szív')

    pv_list = '(' + '|'.join(prevs) + ')'
    prev_filter = re.compile(r'^'+pv_list, flags=re.IGNORECASE)
    prev_type = ''

    if (ana == 'VPfx' or ana == '?VPfx' or ana == 'Vpfx') and prev_filter.search(lemma):
        prev_standard = vpfx_standardizer[lemma]
        prev_type = 'detached{' + prev_standard + '|?|?|?|?|?}'

    elif ana.startswith('VPfx.') and prev_filter.search(lemma):
        prev_standard = ''
        verb_lemma = ''
        lemma = lemma.replace('|+', '')
        lemma = lemma.replace('+', '')
        lemma = lemma.rstrip('-')
        for item in prev_by_len:
            if lemma.startswith(item) and lemma not in ['eléltet', 'belép', 'belény', 'beleny', 'megy']:
                verb_lemma = lemma[len(item):]
                prev_standard = vpfx_standardizer[item]
                break
        cons_type = constype_converter(norm, ana)
        if prev_standard != '':
            prev_type = 'prefixed{' + prev_standard + '|' + verb_lemma + '|' + cons_type + '|prefixed_' + cons_type + '|0|-}'

    elif '|+' in lemma and not re.search(r'^(#|az|a|ő)?\|\+', lemma) and not ana.startswith('PP.'):
        lemma = lemma.replace('#', '')
        lemma = lemma.rstrip('-')

        incorporation = '-'
        incorp_true = re.search(r'^(hely|ágyék|cséza|ágyék|hely|levél|tányér|tej-|leány|ganéj|szalonna|ház|marha|gabona|ajtó|pálinka|ing|sertés\+epe-|száj-|fonal|répa)\+', lemma)
        if incorp_true:
            incorporation = incorp_true.group(1)
            incorporation = incorporation.replace('+', '')
            incorporation = incorporation.replace('-', '')
            lemma = re.sub(r'^(hely|ágyék|cséza|ágyék|hely|levél|tányér|tej-|leány|ganéj|szalonna|ház|marha|gabona|ajtó|pálinka|ing|sertés\+epe-|száj-|fonal|répa)\+', '', lemma)
        
        lemma = lemma.replace('?', '')
        lemma = lemma.replace('+', '')
        orig_prev, verb_lemma = lemma.split('|')
        prev_standard = vpfx_standardizer[orig_prev]
        verb_lemma = verb_lemma.split('_')[0]

        if 'V.' in ana:
            cons_type = constype_converter(norm, ana)
        else:
            cons_type, verb_lemma = constype_str_converter(norm, ana, verb_lemma)

        if cons_type != '?':
            prev_type = 'prefixed_unmarked{' + prev_standard + '|' + verb_lemma + '|' + cons_type + '|prefixed_' + cons_type + '|0|' + incorporation + '}'

    elif re.search(r'^(leg|leges\+?leg|leges\+?leges\+?leg)', lemma):
        pass

    return prev_type


""" MAIN """

inpath = './unified_omk_tmk/'
outpath = './unified_omk_tmk_vpfx/'
helpdict = 'vpfx_helpdict.txt'

vpfx_variations = set()
vpfx_standardizer = {}
with open(helpdict, 'r', encoding='utf-8') as fr:
    for line in fr:
        line = line.rstrip('\n')
        if not line.startswith('*'):
            orig_lemma, standard_lemma, variations = line.split('\t')
            if len(variations) != 0:
                vpfx_variations.add(variations)
            if orig_lemma not in vpfx_standardizer.keys():
                vpfx_standardizer[orig_lemma] = standard_lemma
vpfx_list = list(vpfx_variations)
prev_by_len = sorted(vpfx_standardizer.keys(), key=len, reverse=True)

files = sorted(os.listdir(inpath))

for f in files:
    with open(outpath+f, 'w', encoding='utf-8') as fw:
        with open(inpath+f, 'r', encoding='utf-8') as fr:
            for line in fr:
                line = line.rstrip('\n')
                if len(line) == 0:
                    print(line, file=fw)
                else:
                    tid, orig, norm, lemma, ana = line.split('\t')
                    prev_type = vpfx_marker(tid, orig, norm, lemma, ana, vpfx_list, vpfx_standardizer, prev_by_len)
                    print(line + '\t' + prev_type, file=fw)
