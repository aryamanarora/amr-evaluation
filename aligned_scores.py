# finds the percentage of instances of a word that get aligned
import amr
import re
import sys
import stanfordnlp

# stanfordnlp.download('en')
nlp = stanfordnlp.Pipeline()

amrs = open(sys.argv[1]).read().strip().split('\n\n')

aligned, total = {}, {}

with open(sys.argv[1] + '2', 'w') as fout:
    for i, amr in enumerate(amrs):
        if i % 100 == 0:
            print(i)
        doc = None
        for line in amr.split('\n'):

            # the sentence itself needs to be stored
            if line.startswith('# ::tok'):
                doc = nlp(line[8:])
                res = [word.text + '|' + word.dependency_relation + '|' + str(word.governor) for word in doc.sentences[0].words]
                fout.write('# ::tok' + ' '.join(res) + '\n')
            else:
                fout.write(line + '\n')
        fout.write('\n')