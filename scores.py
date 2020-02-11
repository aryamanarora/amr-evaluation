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

def evaluate(name, list_pred, list_gold):
    inters[name] += len(set(list_pred) & set(list_gold))
    preds[name] += len(set(list_pred))
    golds[name] += len(set(list_gold))

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
    
    for i in roles:
        evaluate(i, disambig(role(i, dict_pred, triples_pred)),
            disambig(role(i, dict_gold, triples_gold)))
        # if i == 'op1':
        #     print(i)
        #     print(disambig(role(i, dict_gold, triples_gold)), disambig(role(i, dict_gold, triples_gold)))
        #     input()
    
    evaluate('Concepts', disambig(concepts(dict_pred)),
        disambig(concepts(dict_gold)))
    evaluate('Named Ent.', disambig(namedent(dict_pred, triples_pred)),
        disambig(namedent(dict_gold, triples_gold)))
    evaluate('Negations', disambig(negations(dict_pred, triples_pred)),
        disambig(negations(dict_gold, triples_gold)))
    evaluate('Wikification', disambig(wikification(triples_pred)),
        disambig(wikification(triples_gold)))
    evaluate('Constants', disambig(constants(dict_pred, triples_pred)),
        disambig(constants(dict_gold, triples_gold)))
    evaluate('Quantities', disambig(quantities(dict_pred, triples_pred)),
        disambig(quantities(dict_gold, triples_gold)))

    reentrancies_pred.append(reentrancies(dict_pred, triples_pred))
    reentrancies_gold.append(reentrancies(dict_gold, triples_gold))
    
    srl_pred.append(srl(dict_pred, triples_pred))
    srl_gold.append(srl(dict_gold, triples_gold))

for score in preds:
    if preds[score] > 0:
        pr = inters[score] / preds[score]
    else:
        pr = 0
    if golds[score] > 0:
        rc = inters[score] / golds[score]
    else:
        rc = 0
    if pr + rc > 0:
        f = 2 * (pr * rc) / (pr + rc)
        print(f'{score:>20} {inters[score]:>10} {preds[score]:>10} {golds[score]:>10} -> P: {pr:.2f}, R: {rc:.2f}, F: {f:.2f}')
    else: 
        print(f'{score:>20} {inters[score]:>10} {preds[score]:>10} {golds[score]:>10} -> P: {pr:.2f}, R: {rc:.2f}, F: 0.00')

pr, rc, f = smatch.main(reentrancies_pred, reentrancies_gold, True)
print(f'Reentrancies -> P: {pr:.2f}, R: {rc:.2f}, F: {f:.2f}')
pr, rc, f = smatch.main(srl_pred, srl_gold, True)
print(f'SRL -> P: {pr:.2f}, R: {rc:.2f}, F: {f:.2f}')
