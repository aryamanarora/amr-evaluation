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

concepts_pred = defaultdict(int)
concepts_gold = defaultdict(int)
concepts_inters = defaultdict(int)

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

def pretty_print(score, i, p, g):
    pr, rc, f = get_scores(i, p, g)
    with open('out.html', 'a') as fout:
        fout.write(f"""<tr>
            <th scope="row">{score}</th>
            <td>{i}</td>
            <td>{p}</td>
            <td>{g}</td>
            <td>{pr}</td>
            <td>{rc}</td>
            <td>{f}</td>
        </tr>""")

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

    conc_pred = disambig(concepts(dict_pred))
    conc_gold = disambig(concepts(dict_gold))
    for concept in conc_pred:
        concepts_inters[concept[:-2]] += 0
        if concept in conc_gold:
            concepts_inters[concept[:-2]] += 1
        concepts_pred[concept[:-2]] += 1
    for concept in conc_gold:
        concepts_inters[concept[:-2]] += 0
        concepts_gold[concept[:-2]] += 1
    

    reentrancies_pred.append(reentrancies(dict_pred, triples_pred))
    reentrancies_gold.append(reentrancies(dict_gold, triples_gold))
    
    srl_pred.append(srl(dict_pred, triples_pred))
    srl_gold.append(srl(dict_gold, triples_gold))

    unlabelled_pred.append(unlabelled(dict_pred, triples_pred))
    unlabelled_gold.append(unlabelled(dict_gold, triples_gold))

with open('out.html', 'w') as fout:
    fout.write("""<html>
    <head>
        <meta charset="utf-8" />
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <title>Results</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <!-- bootstrap -->
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">
        <script defer src="https://use.fontawesome.com/releases/v5.0.8/js/all.js"></script>
    </head>
    <body>
        <table class="table">
            <tr>
                <th scope="col">Metric</th>
                <th scope="col">Intersection</th>
                <th scope="col">Pred</th>
                <th scope="col">Gold</th>
                <th scope="col">Precision</th>
                <th scope="col">Recall</th>
                <th scope="col">F1</th>
            </tr>""")

for score in sorted(preds, key = lambda key: golds[key]):
    pretty_print(score, inters[score], preds[score], golds[score])

# pr, rc, f = smatch.main(reentrancies_pred, reentrancies_gold, True)
# pretty_print('Reentrancies', '?', '?', '?', pr, rc, f)

# pr, rc, f = smatch.main(srl_pred, srl_gold, True)
# pretty_print('SRL', '?', '?', '?', pr, rc, f)

# pr, rc, f = smatch.main(unlabelled_pred, unlabelled_gold, True)
# pretty_print('Unlabelled', '?', '?', '?', pr, rc, f)

with open('out.html', 'a') as fout:
    fout.write("""</table>
        <table class="table">
            <tr>
                <th scope="col">Metric</th>
                <th scope="col">Intersection</th>
                <th scope="col">Pred</th>
                <th scope="col">Gold</th>
                <th scope="col">Precision</th>
                <th scope="col">Recall</th>
                <th scope="col">F1</th>
            </tr>""")

for score in sorted(concepts_inters, key = lambda key: -concepts_gold[key]):
    pretty_print(score, concepts_inters[score], concepts_pred[score], concepts_gold[score])
with open('out.html', 'a') as fout:
    fout.write('</table></body></html>')
