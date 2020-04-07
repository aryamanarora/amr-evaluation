#!/usr/bin/env python
#coding=utf-8
from collections import defaultdict

'''
Various routines used by scores.py
'''

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

def disambig(lst):
    lst2 = []
    for v in lst:
        idx = 1
        v_idx = v + '_0'
        while str(v_idx) in lst2:
            v_idx = v + '_' + str(idx)
            idx += 1
        lst2.append(str(v_idx))
    return lst2

def concepts(v2c_dict):
    return [str(v) for v in v2c_dict.values()]

def evaluate2(v2c_dicts, tripleses, rels):
    comps = [defaultdict(list), defaultdict(list), defaultdict(list)]
    for i in range(2):
        for (l, v1, v2) in tripleses[i]:
            c1 = v2c_dicts[i][v1] if v1 in v2c_dicts[i] else v1
            c2 = v2c_dicts[i][v2] if v2 in v2c_dicts[i] else v2

            # per-role
            if l in roles:
                comps[i][':' + l].append(c1 + ' ' + c2)
            elif l[:-3] in roles and l.endswith('-of'):
                comps[i][':' + l].append(c2 + ' ' + c1)
            
            # constants
            if v2.endswith('_'):
                comps[i]['Constants'].append(l + ' ' + c1 + ' ' + c2)
            
            # mod+domain
            if l == 'mod':
                comps[i]['Mods+Domains'].append(c1 + ' ' + c2)
            elif l == 'domain':
                comps[i]['Mods+Domains'].append(c2 + ' ' + c1)
            
            # quantitites
            if c1.endswith('quantity'):
                comps[i]['Quantities'].append(l + ' ' + c1 + ' ' + c2)
                comps[i]['Quantities (ignoring kind)'].append(c1 + ' ' + c2)

            # reification
            if c2.endswith('91'):
                comps[i]['Reification'].append(l + ' ' + c1 + ' ' + c2)
            # predicate (numbered concept)
            elif c1[-2:].isdigit():
                comps[i]['Predicates'].append(c1)
            
            # ops
            if l.startswith('op'):
                comps[i]['Ops (ignoring order)'].append(c1 + ' ' + c2)
            
            # args
            if l.startswith('ARG'):
                if l.endswith('of'):
                    comps[i]['ARGs (ignoring order)'].append(c2 + ' ' + c1)
                else:
                    comps[i]['ARGs (ignoring order)'].append(c1 + ' ' + c2)
            
            # relations
            comps[i]['Relations (ignoring nodes)'].append(l)
            
            
    
    for key in set(comps[0]) | set(comps[1]):
        rels[2][key] += len(set(comps[0][key]) & set(comps[1][key]))
        rels[0][key] += len(set(comps[0][key]))
        rels[1][key] += len(set(comps[1][key]))
    
    return rels

def reentrancies(v2c_dict, triples):
    lst = []
    vrs = []
    for n in v2c_dict.keys():
        parents = [(l, v1, v2) for (l, v1, v2) in triples if v2 == n and l != "instance"]
        if len(parents) > 1:
            #extract triples involving this (multi-parent) node
            for t in parents:
                lst.append(t)
                vrs.extend([t[1], t[2]])
    #collect var/concept pairs for all extracted nodes
    dict1 = {}
    for i in v2c_dict:
         if i in vrs:
            dict1[i] = v2c_dict[i]
    return (lst, dict1)

def srl(v2c_dict, triples):
    lst = []
    vrs = []
    for t in triples:
        if t[0].startswith("ARG"):
            #although the smatch code we use inverts the -of relations
            #there seems to be cases where this is not done so we invert
            #them here
            if t[0].endswith("of"):
                lst.append((t[0][0:-3], t[2], t[1]))
                vrs.extend([t[2], t[1]])
            else:
                lst.append(t)
                vrs.extend([t[1], t[2]])

    #collect var/concept pairs for all extracted nodes            
    dict1 = {}
    for i in v2c_dict:
        if i in vrs:
            dict1[i] = v2c_dict[i]
    return (lst, dict1)

def unlabelled(v2c_dict, triples):
    lst = []
    vrs = []
    for t in triples:
        if t[0] != 'TOP':
            if t[0].endswith("of"):
                lst.append(('ARG0', t[2], t[1]))
                vrs.extend([t[2], t[1]])
            else:
                lst.append(('ARG0', t[1], t[2]))
                vrs.extend([t[1], t[2]])
        else:
            lst.append(t)
            vrs.extend([t[1], t[2]])

    #collect var/concept pairs for all extracted nodes            
    dict1 = {}
    for i in v2c_dict:
        if i in vrs:
            dict1[i] = v2c_dict[i]
    return (lst, dict1)

def var2concept(amr):
    v2c = {}
    try:
        for n, v in zip(amr.nodes, amr.node_values):
            v2c[n] = v
    except:
        pass
    return v2c
