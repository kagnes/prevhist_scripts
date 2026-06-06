# -*- coding: utf-8 -*-

# author: kagnes
# created: 2026/04/15

import re


def handle_multihits(actsent):
    sents = []
    tempie = []
    if 'hits="1"' not in actsent[0]:
        ids = re.search(r'ids="([^"]+)"', actsent[0]).group(1)
        hits = ids.split(' ')
        for hit in hits:
            actheader = re.sub(r' hits="[^"]+" ids="[^"]+"', r' id="' + hit + '"', actsent[0])
            tempie.append(actheader)
            for line in actsent[1:]:
                tempie.append(line)
            sents.append(tempie)
            tempie = []
    else:
        actheader = re.sub(r' hits="[^"]+" ids=', r' id=', actsent[0])
        tempie.append(actheader)
        for line in actsent[1:]:
            tempie.append(line)
        sents.append(tempie)
    return sents


def get_basic_meta(sents):
    dt = {}
    for i, sent in enumerate(sents):
        _, docid, hunmeta, profile, year, corpus, hit_id = re.findall(r'"([^"]*)"', sent[0])
        dt[i] = {'docid': docid, 'hunmeta': hunmeta, 'profile': profile, 'year': year, 'corpus': corpus, 'hit_id': hit_id, 'todo': sent[1:]}
    return dt


def standardize_sent_structure(dt):
    for i, data in dt.items():
        token_lines = {}
        for row in data['todo']:
            cells = row.split('\t')

            orig_id = cells[0]
            orig = cells[1]
            norm = cells[2]
            lemma = cells[3]
            ana = cells[4]
            previnfo = cells[5]
            extras = []
            token_lines[int(orig_id)] = {'orig_id': orig_id, 'orig': orig, 'norm': norm,
                                     'lemma': lemma, 'ana': ana, 'previnfo': previnfo, 'extras': extras}
        dt[i]['todo'] = token_lines
    return dt


def get_tense_info(dt):
    for i, data in dt.items():
        # kopulák, (komplex) igeidők azonosítása, felannotálása
        copula_id = 1000000  # random nagy szám, ami sose következik be
        for token_id, row in data['todo'].items():
            # ha kiderült közben, hogy complex tense részeként kopula az adott token, azt itt jelezzük
            if token_id == copula_id:
                copula_id = 1000000
                data['todo'][token_id]['extras'].append('copula')

            if re.search(r'V\..*[SP][123]', row['ana']) and '.Inf' not in row['ana'] and 'copula' not in row['extras']:
                if '.Fut' in row['ana']:
                    tense = '-And'
                elif '.Past' in row['ana']:
                    tense = '-t'
                elif '.Ipf' in row['ana']:
                    tense = '-A'
                elif '.Cond' in row['ana']:
                    tense = '-nA'
                else:
                    tense = '-'

                keep_right = ''
                for k in data['todo'].keys():
                    if k > token_id:
                        keep = '{}/{}/{} '.format(str(k), data['todo'][k]['norm'].lower(), data['todo'][k]['ana'])
                        keep_right += keep
                keep_right.strip()

                if re.search(r'^[0-9]+/(van|lesz|lehet|vala|volt|volna|legyen|légyen)/', keep_right):
                    copula = re.search(r'^([0-9]+)/(van|lesz|lehet|vala|volt|volna|legyen|légyen)/', keep_right)
                    tense += ' '+copula.group(2)
                    copula_id = int(copula.group(1))
                    data['todo'][token_id]['extras'].append('check_copula')
                    data['todo'][token_id]['extras'].append('has_copula:' + str(copula_id))

                elif re.search(r'^([0-9]+/[^ /]+/[^ ]*V\.[^ ]*[SP][123][^ ]* )?([^ ]+/VPfx |[^ ]+/-e/[^ ]+ |[^ ]+/is/[^ ]+ ){0,3}[0-9]+/(van|lesz|lehet|vala|volt|volna|legyen|légyen)/', keep_right):
                    copula = re.search(r'^([0-9]+/[^ /]+/[^ ]*V\.[^ ]*[SP][123][^ ]* )?([^ ]+/VPfx |[^ ]+/-e/[^ ]+ |[^ ]+/is/[^ ]+ ){0,3}([0-9]+)/(van|lesz|lehet|vala|volt|volna|legyen|légyen)/', keep_right)
                    tense += ' '+copula.group(4)
                    copula_id = int(copula.group(3))
                    data['todo'][token_id]['extras'].append('check_copula')
                    data['todo'][token_id]['extras'].append('has_copula:' + str(copula_id))
                    if '/VPfx ' in keep_right:
                        data['todo'][token_id]['extras'].append('unexpected_prevpos')
                data['todo'][token_id]['extras'].append('tense:' + tense)
    return dt


def get_preverb_data(dt):

    rows = []
    for i, data in dt.items():
        done = False  # detachedekhez kell
        valid_hit = False  # final DS-hez kell
        hit_id = int(data['hit_id'])
        hit = data['todo'][hit_id]
        
        if hit['previnfo'].startswith('prefixed'):
            valid_hit = True
            tempval = re.sub(r'^prefixed(_unmarked)?\{', '', hit['previnfo'])
            prev, verb, constype, subtype, prevpos, incorporation = tempval.rstrip('}').split('|')
            intervening = '_'
            
            if 'check_copula' in hit['extras']:
                for item in hit['extras']:
                    if item.startswith('has_copula'):
                        copula_id = int(item.split(':')[-1])
                        break
                conc_dt = add_concordance(data['todo'], hit_id, copula_id)
            else:
                conc_dt = add_concordance(data['todo'], hit_id, hit_id)

            act_form = conc_dt['kwic_norm'].lower()
        
        else:
            tempval = re.sub(r'^detached\{', '', hit['previnfo'])
            prev, verb, constype, subtype, prevpos, incorporation = tempval.rstrip('}').split('|')
            incorporation = '_'
            
            hit['token_id'] = int(hit['orig_id'])
            sentence_ids = list(data['todo'].keys())
            leftrange = list(range(sentence_ids[0], hit_id))
            rightrange = list(range(hit_id+1, sentence_ids[-1]))
            left = {k: data['todo'][k] for k in reversed(leftrange)}  # így egységesen kezelhető a két irány! mindig break-elhetünk az első jónál
            right = {k: data['todo'][k] for k in rightrange}
            unsure_right = []
            temp_unsure = []

            likely = []
            for count, item in right.items():
                if item['ana'].startswith('V.') and 'copula' not in item['extras'] and not item['previnfo'].startswith('prefixed'):
                    likely.append(count)

            if len(likely) == 0:
                # nincs találat (másik irányban lehet), megvagyunk
                done = False
            elif len(likely) == 1:
                # egy találat jöhet szóba, ezt validáljuk
                count = likely[0]
                intervening = {k: right[k] for k in range(rightrange[0], count)}
                maybe_hit = right[count]
                maybe_hit['token_id'] = count
                intervening_text = ' '.join([v['norm'] for k, v in intervening.items()]).strip()

                tiny_advs = re.search(r'^(nem|ne|sem|se|is|-e|-é|es)( (nem|ne|sem|se|is|-e|-é|es))*$', intervening_text, flags=re.I)
                if tiny_advs:
                    verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'after', 0, intervening)
                    done = True
                    valid_hit = True
                elif re.search(r'[-:,;.?!"><„–|\]\[/]$', intervening_text):
                    done = False 
                else:
                    unsure_right.append(count)
                    done = False
            else:
                # több lehetséges találat, a legnagyobb ID-val kezdve kell validálgatni a dolgot
                rev_likely = list(reversed(likely))
                for count in rev_likely:
                    intervening = {k: right[k] for k in range(rightrange[0], count)}
                    maybe_hit = right[count]
                    maybe_hit['token_id'] = count
                    intervening_text = ' '.join([v['norm'] + '/' + v['lemma'] + '/' + v['ana'] for k, v in intervening.items()]).strip()
                    simple_intervening_text = ' '.join([v['norm'] for k, v in intervening.items()]).strip()
                    if ('.Inf' in maybe_hit['ana'] or 'PartAdv' in maybe_hit['ana']) and re.search(r'^[^ ]+/V\.[^ ]+$', intervening_text):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'after', 0, intervening)
                        valid_hit = True
                        done = True
                        break
                    elif ('.Inf' in maybe_hit['ana'] or 'PartAdv' in maybe_hit['ana']) and re.search(r'^[^ ]+/V\.[^ ]+ (van|lesz|lehet|vala|volt|volna|legyen|légyen)/[^ ]+/V\.[^ ]+$', intervening_text):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'after', -2, intervening)
                        valid_hit = True
                        done = True
                        break
                    elif re.search(r'[-:,;.?!"><„–|\]\[/]$', intervening_text):
                        done = False
                    elif ('.Inf' in maybe_hit['ana'] or 'PartAdv' in maybe_hit['ana']) and re.search(r'^[^ ]+/V\.[^ ]+ -[eé]/[^ ]+/QPtl$', intervening_text):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'after', 0, intervening)
                        valid_hit = True
                        done = True
                        break
                    elif ('.Inf' in maybe_hit['ana'] or 'PartAdv' in maybe_hit['ana']) and re.search(r'^[^ ]+/V\.[^ ]+ [^ ]+/N[:|]Pro[^ ]+$', intervening_text):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'after', 0, intervening)
                        valid_hit = True
                        done = True
                        break
                    elif ('.Inf' in maybe_hit['ana'] or 'PartAdv' in maybe_hit['ana']) and re.search(r'^[^ ]+/V\.[^ ]+ (van|lesz|lehet|vala|volt|volna|legyen|légyen)/[^ ]+/V\.[^ ]+ [^ ]+/N[:|]Pro[^ ]+$', intervening_text):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'after', -3, intervening)
                        valid_hit = True
                        done = True
                        break
                    elif ('.Inf' in maybe_hit['ana'] or 'PartAdv' in maybe_hit['ana']) and re.search(r'^[^ ]+/V\.[^ ]+ [^ ]+/N[:|]Pro[^ ]+ [^ ]+/is/Clit_is$', intervening_text):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'after', 0, intervening)
                        valid_hit = True
                        done = True
                        break
                    elif ('.Inf' in maybe_hit['ana'] or 'PartAdv' in maybe_hit['ana']) and re.search(r'^[^ ]+/nem?/[^ ]+ [^ ]+/V\.[^ ]+$', intervening_text):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'after', 0, intervening)
                        valid_hit = True
                        done = True
                        break
                    elif ('.Inf' in maybe_hit['ana'] or 'PartAdv' in maybe_hit['ana']) and re.search(r'^[^ ]+/nem?/[^ ]+ [^ ]+/V\.[^ ]+ (van|lesz|lehet|vala|volt|volna|legyen|légyen)/[^ ]+/V\.[^ ]+$', intervening_text):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'after', -3, intervening)
                        valid_hit = True
                        done = True
                        break
                    elif ('.Inf' in maybe_hit['ana'] or 'PartAdv' in maybe_hit['ana']) and re.search(r'^[^ ]+/V\.[^ ]+ [^ ]+/Det[:|]Pro[^ ]* [^ ]+/N[^ ]*$', intervening_text):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'after', 0, intervening)
                        valid_hit = True
                        done = True
                        break
                    elif ('.Inf' in maybe_hit['ana'] or 'PartAdv' in maybe_hit['ana']) and re.search(r'^[^ ]+/V\.[^ ]+ [^ ]+/N[:|]Pro[^ ]* (rajta|róla)/[^ ]+$', intervening_text):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'after', 0, intervening)
                        valid_hit = True
                        done = True
                        break
                    elif ('.Inf' in maybe_hit['ana'] or 'PartAdv' in maybe_hit['ana']) and re.search(r'^[^ ]+/V\.[^ ]+ [^ ]+/N[:|]Pro[^ ]* [^ ]+/N[^ ]*$', intervening_text):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'after', 0, intervening)
                        valid_hit = True
                        done = True
                        break
                    elif re.search(r'^(nem|ne|sem|se|is|-e|-é|es)( (nem|ne|sem|se|is|-e|-é|es))*$', simple_intervening_text, flags=re.I):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'after', 0, intervening)
                        valid_hit = True
                        done = True
                        break
                    else:
                        temp_unsure.append(count)
                        done = False

                if not done:
                    unsure_right.extend(temp_unsure)
                    temp_unsure = []

            if not done:
                likely = []
                for count, item in left.items():
                    if item['ana'].startswith('V.') and 'copula' not in item['extras'] and not item['previnfo'].startswith('prefixed'):
                        likely.append(count)

                if len(likely) == 0:
                    # nincs találat, megvagyunk
                    done = False
                elif len(likely) == 1:
                    # egy találat jöhet szóba, ezt validáljuk
                    count = likely[0]
                    maybe_hit = left[count]
                    maybe_hit['token_id'] = count
                    if maybe_hit['token_id']+1 == hit['token_id']:
                        intervening = {}
                        intervening_text = complex_intervening_text = ''
                    else:
                        intervening = {k: data['todo'][k] for k in range(maybe_hit['token_id']+1, hit['token_id'])}
                        intervening_text = ' '.join([v['norm'] for k, v in intervening.items()]).strip()
                        complex_intervening_text = ' '.join([v['norm'] + '/' + v['lemma'] + '/' + v['ana'] for k, v in intervening.items()]).strip()

                    if len(intervening_text) == 0:
                        intervening_type = '_'
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'before', 0, intervening)
                        valid_hit = True
                        done = True
                    elif re.search(r'^(van|lesz|lehet|vala|volt|volna|legyen|légyen)$', intervening_text, flags=re.I):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'before', 1, intervening)
                        valid_hit = True
                        done = True
                    elif re.search(r'^-[eé]$', intervening_text, flags=re.I):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'before', 0, intervening)
                        valid_hit = True
                        done = True
                    elif re.search(r'^[-:,;.?!"><„–|\]\[/]', intervening_text):
                        done = False 
                    elif re.search(r'^[^ ]+/Adv(:[^ ]+)?$', complex_intervening_text, flags=re.I) or intervening_text in ['hát', 'kedig', 'jól']:
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'before', 0, intervening)
                        valid_hit = True
                        done = True
                    elif re.search(r'^[^ ]+/N[:|]Pro[^ ]*$', complex_intervening_text, flags=re.I):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'before', 0, intervening)
                        valid_hit = True
                        done = True
                    elif re.search(r'^([^ ]*/Det[^ /]* )?([^ ]*/Adj[^ /]* )?[^ ]+/N[^ ]*$', complex_intervening_text, flags=re.I):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'before', 0, intervening)
                        valid_hit = True
                        done = True
                    elif intervening_text.count(' ') <= 9 and intervening_text != 'a' and not re.search(r'[\.\,\!\?\;\:\"\'\u201c\u201d\u2018\u2019\u2014\(\)><\*]', intervening_text, flags=re.I):
                        verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'before', 0, intervening)
                        valid_hit = True
                        done = True
                    else:
                        pass

                else:
                    for count in likely:
                        maybe_hit = left[count]
                        maybe_hit['token_id'] = count
                        intervening = {k: left[k] for k in range(maybe_hit['token_id']+1, hit_id)}
                        complex_intervening_text = ' '.join([v['norm'] + '/' + v['lemma'] + '/' + v['ana'] for k, v in intervening.items()]).strip()
                        intervening_text = ' '.join([v['norm'] for k, v in intervening.items()]).strip()
                        
                        if len(intervening_text) == 0:
                            intervening_type = '_'
                            verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'before', 0, intervening)
                            valid_hit = True
                            done = True
                            break
                        elif re.search(r'^(van|lesz|lehet|vala|volt|volna|legyen|légyen)$', intervening_text, flags=re.I):
                            verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'before', 1, intervening)
                            valid_hit = True
                            done = True
                            break
                        elif re.search(r'^-[eé]$', intervening_text, flags=re.I):
                            verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'before', 0, intervening)
                            valid_hit = True
                            done = True
                            break
                        elif re.search(r'^[-:,;.?!"><„–|\]\[/]', intervening_text):
                            done = False
                        elif re.search(r'^[^ ]+/Adv(:[^ ]+)?$', complex_intervening_text, flags=re.I) or intervening_text in ['hát', 'kedig', 'jól']:
                            verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'before', 0, intervening)
                            valid_hit = True
                            done = True
                            break
                        elif re.search(r'^[^ ]+/N[:|]Pro[^ ]*$', complex_intervening_text, flags=re.I):
                            verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'before', 0, intervening)
                            valid_hit = True
                            done = True
                            break
                        elif re.search(r'^([^ ]*/Det[^ /]* )?([^ ]*/Adj[^ /]* )?[^ ]+/N[^ ]*$', complex_intervening_text, flags=re.I):
                            verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'before', 0, intervening)
                            valid_hit = True
                            done = True
                            break
                        elif intervening_text.count(' ') <= 9 and intervening_text != 'a' and not re.search(r'[\.\,\!\?\;\:\"\'\u201c\u201d\u2018\u2019\u2014\(\)><\*]', intervening_text, flags=re.I):
                            verb, constype, subtype, prevpos, conc_dt, act_form, intervening = add_features(data['todo'], hit, maybe_hit, 'before', 0, intervening)
                            valid_hit = True
                            done = True
                            break
                        else:
                            pass

            if not done:
                readable_left = ' '.join([v['norm'] for k, v in left.items()])
                readable_right = ' '.join([v['norm'] for k, v in right.items()])
                print('{}\t{}\t{}'.format(readable_left[-20:], hit['norm'], readable_right[:20]))

            pass

        if constype == '?' or verb == '' or verb.startswith('...') or verb == 'njár' or verb.startswith("'n") or re.search('^ül[hkm]', verb):
            valid_hit = False

        if valid_hit:
            if data['corpus'] == 'OHC' or data['profile'] == '_':
                data['profile'] = 'religious-formal'
            verb = verb.replace('#', '')
            verb = verb.replace('+', '')
            if constype == 'Ó':
                constype = '-Ó'
                subtype = 'prefixed_-Ó'
            if intervening == '':
                intervening = intervening.replace('', '_')
            intervening = intervening.replace('|+', '')
            intervening = intervening.replace('+', '')
            incorporation = incorporation.replace('-', '_')
            final_row = '\t'.join([constype, subtype, str(prevpos), prev, verb, intervening, incorporation, 
                                  act_form, conc_dt['lc_orig'], conc_dt['kwic_orig'], conc_dt['rc_orig'], 
                                  conc_dt['lc_norm'], conc_dt['kwic_norm'], conc_dt['rc_norm'], data['corpus'], str(data['docid']), str(data['year']), data['profile'], data['hunmeta']])
        else:
            final_row = ''
        rows.append(final_row)
    return rows


def add_features(whole_sent, preverb, main_verb, verbpos, prevpos, intervening):
    verb = main_verb['lemma'].lower()
    verb = re.sub(r"_'.*'$", "", verb)
    verb = verb.replace('jő_jön', 'jön')
    verb = verb.replace('hí_hív', 'hív')
    verb = verb.replace('szí_szív', 'szív')

    # megnézzük, nincs-e kopula, mert akkor a konkordanciát kicsit máshogy kell indexelni
    verbal_complex_id = main_verb['token_id']
    for info in main_verb['extras']:
        if info.startswith('has_copula:'):
            cop_id = int(info.split(':')[-1])
            if cop_id > main_verb['token_id']: 
                if verbpos == 'after':  
                    verbal_complex_id = cop_id
            else:
                print("A kopula előbb van, mint a főige")

    if verbpos == 'after':
        if prevpos == 0:  # ennek itt nincs 0 jelentése, csak hogy nem egyedileg kezelendő eset
            prevpos = '-' + str(main_verb['token_id'] - preverb['token_id'])
        else:
            prevpos = str(prevpos)
        cons_subtype = '_discontinuous'
        concordance = add_concordance(whole_sent, preverb['token_id'], verbal_complex_id)
    elif verbpos == 'before':
        if prevpos == 0:
            prevpos = str(preverb['token_id'] - main_verb['token_id'])
        else:
            prevpos = str(prevpos)
        cons_subtype = '_inverted'
        concordance = add_concordance(whole_sent, verbal_complex_id, preverb['token_id'])
        
    intervening_lemmas = ''
    for token_id, dt in intervening.items():
        intervening_lemmas += dt['lemma'].lower() + ' '
    intervening_lemmas = intervening_lemmas.strip()

    ana = main_verb['ana']  # csak mert így a vpfx_finder konverter kódja áthozható

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

    subtype = constype + cons_subtype
    act_form = concordance['kwic_norm'].lower()
    
    return verb, constype, subtype, prevpos, concordance, act_form, intervening_lemmas


def add_concordance(whole_sent, first, second):
    lc_orig = ''
    lc_norm = ''
    kwic_orig = ''
    kwic_norm = ''
    rc_orig = ''
    rc_norm = ''

    leftrange = [i for i in whole_sent.keys() if i < first]
    for p in leftrange:
        lc_orig += whole_sent[p]['orig'] + ' '
        lc_norm += whole_sent[p]['norm'] + ' '
    lc_orig = lc_orig.strip()
    lc_norm = lc_norm.strip()

    kwicrange = list(range(first, second+1))
    for p in kwicrange:
        kwic_orig += whole_sent[p]['orig'] + ' '
        kwic_norm += whole_sent[p]['norm'] + ' '
    kwic_orig = kwic_orig.strip()
    kwic_norm = kwic_norm.strip()

    rightrange = list(range(second+1, len(whole_sent)))
    for p in rightrange:
        rc_orig += whole_sent[p]['orig'] + ' '
        rc_norm += whole_sent[p]['norm'] + ' '
    rc_orig = rc_orig.strip()
    rc_norm = rc_norm.strip()

    lc_orig = lc_orig.replace('-@@', '')
    kwic_orig = kwic_orig.replace('-@@', '')
    rc_orig = rc_orig.replace('-@@', '')

    lc_orig = lc_orig.replace('== ==', ' ')
    kwic_orig = kwic_orig.replace('== ==', ' ')
    rc_orig = rc_orig.replace('== ==', ' ')

    lc_norm = re.sub(r' *[<>] *', ' ', lc_norm).strip()
    kwic_norm = re.sub(r' *[<>] *', ' ', kwic_norm).strip()
    rc_norm = re.sub(r' *[<>] *', ' ', rc_norm).strip()

    return {'lc_orig': lc_orig, 'kwic_orig': kwic_orig, 'rc_orig': rc_orig, 'lc_norm': lc_norm, 'kwic_norm': kwic_norm, 'rc_norm': rc_norm}


""" MAIN """

infile = 'ohc_mhc_hits.txt'
outfile = 'PrevHist.tsv'

copula = ['van', 'lesz', 'lehet', 'vala', 'volt', 'volna', 'van_lesz', 'lesz_van', 'legyen', 'légyen']
clitic = ['is', '-e', '-é']
tiny_adverb = ['nem', 'ne', 'sem', 'se', 'is']
punct = [char for char in ':,;.?!"><„–-|']
punct.append('[...]')

tsv_header = 'sid constype subtype prevpos prev verb intervening incorporation actform orig_left orig_kwic orig_right norm_left norm_kwic norm_right corpus docid year profile hunmeta'.replace(' ', '\t')

sid = 0
with open(outfile, 'w', encoding='utf-8') as fw:
    print(tsv_header, file=fw)
    actsent = []
    with open(infile, 'r', encoding='utf-8') as fr:
        for line in fr:
            line = line.rstrip('\n')
            if len(line) == 0:
                sents = handle_multihits(actsent)
                dt = get_basic_meta(sents)
                dt = standardize_sent_structure(dt)
                dt = get_tense_info(dt)
                rows = get_preverb_data(dt)

                for row in rows:
                    if len(row) > 0:
                        sid += 1
                        row = str(sid) + '\t' + row
                        print(row, file=fw)

                actsent = []
            else:
                actsent.append(line)
