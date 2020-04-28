#!/usr/bin/env python
#coding=utf-8

'''
Computes AMR scores for concept identification, named entity recognition, wikification,
negation detection, reentrancy detection and SRL.

@author: Marco Damonte (m.damonte@sms.ed.ac.uk)
@since: 03-10-16
'''

import sys
import smatch.amr as amr
import smatch.smatch_fromlists as smatch
from collections import defaultdict
from utils import *
import stanza
import re
import jinja2 as j2

file_loader = j2.FileSystemLoader('templates')
env = j2.Environment(loader=file_loader)

output = env.get_template('output.html.jinja')
output2 = env.get_template('output2.html.jinja')

nlp = stanza.Pipeline(lang='en', processors='tokenize,pos,lemma,depparse')

notes = {
    'Predicates': 'all numbered concepts, e.g. throw-01',
    'Relations (ignoring nodes)': 'all relations ignoring whether the nodes they connect match',
    'Ops (ignoring order)': 'all :opX roles ignoring whether they are :op1, :op2, etc',
    'Mods+Domains': 'all :mod and :domain, treating :domain as the inverse relation of :mod',
    'Quantities (ignoring kind)': 'treating :date-quantity etc. all as one relation',
    'Reification': 'all -91 roles treated as a single class'
}

dict_pred, dict_gold = None, None

# from https://www.isi.edu/~ulf/amr/lib/roles.html
roles = ['ARG0', 'ARG1', 'ARG2', 'ARG3', 'ARG4', 'ARG5', 'ARG6',
    'ARG7', 'ARG8', 'ARG9',
    'accompanier', 'age', 'beneficiary', 'cause', 'concession',
    'condition', 'consist-of', 'cost', 'degree', 'destination',
    'direction', 'domain', 'duration', 'employed-by', 'example',
    'extent', 'frequency', 'instrument', 'li', 'location',
    'manner', 'meaning', 'medium', 'mod', 'mode', 'name', 'ord',
    'part', 'path', 'polarity', 'polite', 'poss', 'purpose',
    'role', 'source', 'subevent', 'subset', 'superset', 'time',
    'topic', 'value',
    'quant', 'unit', 'scale',
    'day', 'month', 'year', 'weekday', 'time', 'timezone', 'quarter',
    'dayperiod', 'season', 'year2', 'decade', 'century', 'calendar',
    'calendar', 'era',
    'op1', 'op2', 'op3', 'op4', 'op5', 'op6', 'op7', 'op8', 'op9', 'op10',
    'prep-against', 'prep-along-with', 'prep-amid', 'prep-among',
    'prep-as', 'prep-at', 'prep-by', 'prep-for', 'prep-from', 'prep-in',
    'prep-in-addition-to', 'prep-into', 'prep-on', 'prep-on-behalf-of',
    'prep-out-of', 'prep-to', 'prep-toward', 'prep-under', 'prep-with',
    'prep-without',
    'conj-as-if']

# calculates precision, recall, and f1 score
def get_scores(inter, pred, gold):
    pr, rc, f = 0.0, 0.0, 0.0
    if pred > 0:
        pr = inter / pred
    else:
        pr = 0
    if gold > 0:
        rc = inter / gold
    else:
        rc = 0
    if pr + rc > 0:
        f = 2 * (pr * rc) / (pr + rc)
    else: 
        f = 0
    return (pr, rc, f)

remove = re.compile('#.*?\n')

def unaligned(pred, gold, output_file):
    print(pred, gold)
    # input files
    pred = open(pred).read().strip().split('\n\n')
    gold = open(gold).read().strip().split('\n\n')

    # this is where all objects used for scoring will be kept
    # inters are nodes/connections present in both
    concepts_preds = defaultdict(int)
    concepts_golds = defaultdict(int)
    concepts_inters = defaultdict(int)

    reentrancies_pred = []
    reentrancies_gold = []
    srl_pred = []
    srl_gold = []
    unlabelled_pred, unlabelled_gold = [], []

    inters = defaultdict(int)
    golds = defaultdict(int)
    preds = defaultdict(int)

    count = len(pred)
    progress = 0
    for amr_pred, amr_gold in zip(pred, gold):
        sentence, doc, words = None, None, []
        pos_to_concept = defaultdict(list)
        
        progress += 1
        if progress % 1000 == 0:
            print(progress, '/', count)

        # get triples and concepts from predicted
        amr_pred = amr.AMR.parse_AMR_line(amr_pred.replace('\n',''))
        if amr_pred is None:
            continue
        dict_pred = var2concept(amr_pred)
        triples_pred = []
        for t in amr_pred.get_triples()[1] + amr_pred.get_triples()[2]:
            if t[0].endswith('-of'):
                triples_pred.append((t[0][:-3], t[2], t[1]))
            else:
                triples_pred.append((t[0], t[1], t[2]))

        # triples and concepts from gold
        amr_gold = amr.AMR.parse_AMR_line(amr_gold.replace('\n',''))
        dict_gold = var2concept(amr_gold)
        triples_gold = []
        for t in amr_gold.get_triples()[1] + amr_gold.get_triples()[2]:
            if t[0].endswith('-of'):
                triples_gold.append((t[0][:-3], t[2], t[1]))
            else:
                triples_gold.append((t[0], t[1], t[2]))
        
        # generate all the data for the different metrics considered in utils.py
        # e.g. "Ops (ignoring order)" finds all :op connections between two nodes
        # in predicted and gold, and the overlapping ones are stored in `inters`
        preds, golds, inters = evaluate2((dict_pred, dict_gold), (triples_pred, triples_gold), (preds, golds, inters))

        conc_pred = disambig(concepts(dict_pred))
        conc_gold = disambig(concepts(dict_gold))
        for concept in conc_pred:
            concepts_preds[concept[:-2]] += 1
        for concept in conc_gold:
            concepts_golds[concept[:-2]] += 1
            if concept in conc_pred:
                concepts_inters[concept[:-2]] += 1

        
        # the scores that require smatch
        reentrancies_pred.append(reentrancies(dict_pred, triples_pred))
        reentrancies_gold.append(reentrancies(dict_gold, triples_gold))
        
        srl_pred.append(srl(dict_pred, triples_pred))
        srl_gold.append(srl(dict_gold, triples_gold))

        unlabelled_pred.append(unlabelled(dict_pred, triples_pred))
        unlabelled_gold.append(unlabelled(dict_gold, triples_gold))

    scores_roles = []
    for score in sorted(preds, key = lambda key: -golds[key]):
        pr, rc, f1 = get_scores(inters[score], preds[score], golds[score])
        res = {
                'name': score,
                'inter': inters[score],
                'pred': preds[score],
                'gold': golds[score],
                'pr': pr,
                'rc': rc,
                'f1': f1
            }
        if score in notes:
            res['note'] = notes[score]
        scores_roles.append(res)

    # pr, rc, f = smatch.main(reentrancies_pred, reentrancies_gold, True)
    # pretty_print('Reentrancies', '?', '?', '?', pr, rc, f)

    # pr, rc, f = smatch.main(srl_pred, srl_gold, True)
    # pretty_print('SRL', '?', '?', '?', pr, rc, f)

    # pr, rc, f = smatch.main(unlabelled_pred, unlabelled_gold, True)
    # pretty_print('Unlabelled', '?', '?', '?', pr, rc, f)

    scores_concepts = []
    for score in sorted(concepts_inters, key = lambda key: -concepts_golds[key]):
        pr, rc, f1 = get_scores(concepts_inters[score], concepts_preds[score], concepts_golds[score])
        scores_concepts.append(
            {
                'name': score,
                'inter': concepts_inters[score],
                'pred': concepts_preds[score],
                'gold': concepts_golds[score],
                'pr': pr,
                'rc': rc,
                'f1': f1
            }
        )
    
    with open(output_file, 'w') as fout:
        fout.write(output.render(roles=scores_roles, concepts=scores_concepts))

def aligned(pred, gold, output_file, limit=-1):
    print(pred, gold)
    # input files
    pred = open(pred).read().strip().split('\n\n')
    gold = open(gold).read().strip().split('\n\n')

    pos_golds = defaultdict(int)
    pos_inters = defaultdict(int)
    dep_golds = defaultdict(int)
    dep_inters = defaultdict(int)

    count = len(pred)
    progress = 0
    for amr_pred, amr_gold in zip(pred, gold):
        sentence, doc, words = None, None, []
        pos_to_concept = defaultdict(list)
        dep_to_concept = defaultdict(list)

        # get the sentence for the AMR for analysis
        counts = [0] * 26
        for i, line in enumerate(amr_gold.split('\n')):
            if i == 1:
                sentence = line[8:]
                doc = nlp(sentence)
                for sent in doc.sentences:
                    for word in sent.words:
                        words.append(word)
            elif line.startswith('# ::node'):
                if len(list(sentence.split(' '))) != len(words):
                    break
                line = line.split('\t')

                variable = line[2][0]
                if not variable.islower(): continue
                counts[ord(variable) - ord('a')] += 1
                if counts[ord(variable) - ord('a')] != 1:
                    variable += str(counts[ord(variable) - ord('a')])

                start, end = map(int, line[-2].split('-'))
                for word in range(start, end):
                    pos_to_concept[(words[word].upos)].append(variable)
                    dep_to_concept[(words[word].deprel)].append(variable)
        
        amr_gold = remove.sub(r'', amr_gold)
        
        progress += 1
        if progress == limit:
            break
        if progress % 10 == 0:
            print(progress, '/', count)

        # get triples and concepts from predicted
        amr_pred = amr.AMR.parse_AMR_line(amr_pred.replace('\n',''))
        if amr_pred is None:
            continue
        dict_pred = var2concept(amr_pred)

        # triples and concepts from gold
        amr_gold = amr.AMR.parse_AMR_line(amr_gold.replace('\n',''))
        dict_gold = var2concept(amr_gold)

        conc_pred = disambig(concepts(dict_pred))
        conc_gold = disambig(concepts(dict_gold))
        
        for pos in pos_to_concept:
            for var in pos_to_concept[pos]:
                pos_golds[pos] += 1
                try:
                    if dict_gold[var] + '_0' in conc_pred:
                        pos_inters[pos] += 1
                except:
                    pass
        
        for dep in dep_to_concept:
            for var in dep_to_concept[dep]:
                dep_golds[dep] += 1
                try:
                    if dict_gold[var] + '_0' in conc_pred:
                        dep_inters[dep] += 1
                except:
                    pass
    
    scores_pos = []
    for score in sorted(pos_golds, key = lambda key: -pos_golds[key]):
        res = {
                'name': score,
                'inter': pos_inters[score],
                'gold': pos_golds[score],
                'rc': pos_inters[score] / pos_golds[score],
            }
        if score in notes:
            res['note'] = notes[score]
        scores_pos.append(res)
    
    scores_deps = []
    for score in sorted(dep_golds, key = lambda key: -dep_golds[key]):
        res = {
                'name': score,
                'inter': dep_inters[score],
                'gold': dep_golds[score],
                'rc': dep_inters[score] / dep_golds[score],
            }
        if score in notes:
            res['note'] = notes[score]
        scores_deps.append(res)
    
    with open(output_file, 'w') as fout:
        fout.write(output2.render(pos=scores_pos, deps=scores_deps))

if __name__ == '__main__':
    if len(sys.argv) != 4 and len(sys.argv) != 1:
        print('Incorrect number of args, read the README.')
        exit(1)
    if len(sys.argv) == 1:
        unaligned(
            'train_pred/unaligned/train_pred.txt',
            'train_pred/unaligned/train_gold.txt',
            'out.html'
        )
        aligned(
            'train_pred/unaligned/train_pred.txt',
            'train_pred/aligned/train.aligned.txt',
            'out2.html'
        )
    else:
        unaligned(sys.argv[1], sys.argv[2], 'out.html')
        aligned(sys.argv[1], sys.argv[3], 'out2.html')