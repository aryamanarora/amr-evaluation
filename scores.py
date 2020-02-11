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

pred = open(sys.argv[1]).read().strip().split('\n\n')
gold = open(sys.argv[2]).read().strip().split('\n\n')

inters = defaultdict(int)
golds = defaultdict(int)
preds = defaultdict(int)
reentrancies_pred = []
reentrancies_gold = []
srl_pred = []
srl_gold = []
unlabelled_pred, unlabelled_gold = [], []

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

def pretty_print(score, i, p, g, pr, rc, f):
    print(f'{score:>20} {i:>10} {p:>10} {g:>10} {pr:.2f} {rc:.2f} {f:.2f}')

count = len(pred)
progress = 0
for amr_pred, amr_gold in zip(pred, gold):
    progress += 1
    if progress % 100 == 0: print(progress, '/', count)
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

    amr_gold = amr.AMR.parse_AMR_line(amr_gold.replace('\n',''))
    dict_gold = var2concept(amr_gold)
    triples_gold = []
    for t in amr_gold.get_triples()[1] + amr_gold.get_triples()[2]:
        if t[0].endswith('-of'):
            triples_gold.append((t[0][:-3], t[2], t[1]))
        else:
            triples_gold.append((t[0], t[1], t[2]))
    
    preds, golds, inters = evaluate2((dict_pred, dict_gold), (triples_pred, triples_gold), (preds, golds, inters))

    reentrancies_pred.append(reentrancies(dict_pred, triples_pred))
    reentrancies_gold.append(reentrancies(dict_gold, triples_gold))
    
    srl_pred.append(srl(dict_pred, triples_pred))
    srl_gold.append(srl(dict_gold, triples_gold))

    unlabelled_pred.append(unlabelled(dict_pred, triples_pred))
    unlabelled_gold.append(unlabelled(dict_gold, triples_gold))

pr, rc, f = defaultdict(float), defaultdict(float), defaultdict(float)
for score in preds:
    if preds[score] > 0:
        pr[score] = inters[score] / preds[score]
    else:
        pr[score] = 0
    if golds[score] > 0:
        rc[score] = inters[score] / golds[score]
    else:
        rc[score] = 0
    if pr[score] + rc[score] > 0:
        f[score] = 2 * (pr[score] * rc[score]) / (pr[score] + rc[score])
    else: 
        f[score] = 0

for score in sorted(preds, key = lambda key: f[key]):
    pretty_print(score, inters[score], preds[score], golds[score], pr[score], rc[score], f[score])

pr, rc, f = smatch.main(reentrancies_pred, reentrancies_gold, True)
pretty_print('Reentrancies', '?', '?', '?', pr, rc, f)

pr, rc, f = smatch.main(srl_pred, srl_gold, True)
pretty_print('SRL', '?', '?', '?', pr, rc, f)

pr, rc, f = smatch.main(unlabelled_pred, unlabelled_gold, True)
pretty_print('Unlabelled', '?', '?', '?', pr, rc, f)
