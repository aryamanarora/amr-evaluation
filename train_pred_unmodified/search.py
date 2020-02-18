import sys, re

preds = open('train_pred.txt').read().strip().split('\n\n')
golds = open('train_gold.txt').read().strip().split('\n\n')

red = '#dfb2b2'
green = '#B1CBBA'

reg = re.compile('# ::tok(.*?)\n')
reg2 = re.compile(f'({sys.argv[1]})')

if sys.argv[1][0] == ':':
    with open('res.html', 'w') as fout:
        fout.write('<head><style>\n#data{border:1px solid black; font-size:10px;}\n</style></head>')
        fout.write('<body><table>\n')
        for i in range(len(preds)):
            golds[i] = golds[i].split('\n(')
            preds[i] = preds[i].split('\n(')
            found = reg2.search(golds[i][1])
            found2 = reg2.search(preds[i][1])
            if found or found2:
                golds[i][1] = re.sub(reg2, r'<b style="font-size: 20">\1</b>', golds[i][1])
                preds[i][1] = re.sub(reg2, r'<b style="font-size: 20">\1</b>', preds[i][1])
                result = reg.search(preds[i][0])
                fout.write(f'<tr><td colspan=2>{result.group(1)}</tr></td>')
                fout.write(f'<tr><td id="data" valign="top" style="background-color:{green if found else red}"><pre style="margin:0;padding:0;width:400px;overflow:auto;">({golds[i][1]}</pre></td> \
                    <td id="data" valign="top" style="background-color:{green if found2 else red}"><pre style="margin:0;padding:0;width:400px;overflow:auto;">({preds[i][1]}</pre></td></tr>\n')
        fout.write('</table></body>')
else:
    with open('res.html', 'w') as fout:
        fout.write('<head><style>\n#data{border:1px solid black; font-size:10px;}\n</style></head>')
        fout.write('<body><table>\n')
        for i in range(len(preds)):
            golds[i] = golds[i].split('\n(')
            preds[i] = preds[i].split('\n(')
            result = reg.search(preds[i][0]).group(1)
            found = reg2.search(result)
            if found:
                result = re.sub(reg2, r'<b>\1</b>', result)
                fout.write(f'<tr><td colspan=2>{result}</tr></td>')
                fout.write(f'<tr><td id="data" valign="top"><pre style="margin:0;padding:0;width:400px;overflow:auto;">({golds[i][1]}</pre></td> \
                    <td id="data" valign="top"><pre style="margin:0;padding:0;width:400px;overflow:auto;">({preds[i][1]}</pre></td></tr>\n')
        fout.write('</table></body>')
