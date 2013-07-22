import re
from math import log
from string import ascii_lowercase
from heapq import nlargest
import marshal

py_freq= {}
p2c = {}
py_short = {}
re_eng = re.compile('([a-zA-Z\n]+)')
MAX_SEARCH_ENTRIES = 1000
MAX_SHOW_ENTRIES = 15

py_freq = marshal.load(file('data/py.freq','rb'))
p2c = marshal.load(file('data/p2c.map','rb'))
py_short = marshal.load(file('data/short.map','rb'))
chn_freq = marshal.load(file('data/chn.freq','rb'))

min_freq = min(py_freq.values())
single_letters = set(ascii_lowercase)

print "data loaded."

def word_rank(word):
    if word in single_letters:
        return min_freq-1.0
    elif len(word)==1:
        return 0.0
    return py_freq.get(word,min_freq*20.0)

def dp_cut(sentence):
     max_word_len=20
     best_hop = {}
     N = len(sentence)
     best_hop[N] = [(0,N)]
     for i in xrange(N-1,-1,-1):
          best_hop[i] = nlargest(2,[ (word_rank(sentence[i:hop]) + best_hop[hop][0][0],hop) for hop in xrange(i+1,min(i+max_word_len+1,N+1)) ])
     start  = 0
     top1 = []
     while start<N:
          top1.append(sentence[start:best_hop[start][0][1]])
          start = best_hop[start][0][1]
     top2 = []
     start = 0
     while start<N:
        if start==0 and len(best_hop[start])>1:
            top2.append(sentence[start:best_hop[start][1][1]])
            start = best_hop[start][1][1]
        else:
            top2.append(sentence[start:best_hop[start][0][1]])
            start = best_hop[start][0][1]
     return [top1,top2]


def all_combine_idx(m,idx,tb):
    if idx==len(m)-1:
        for i in xrange(0,len(m[idx])):
            if tb['n']>MAX_SEARCH_ENTRIES:
                return
            yield [i]
            tb['n']=tb.get('n',0)+1  
    else:
        for w in xrange(0,len(m[idx])):
            if tb['n']>MAX_SEARCH_ENTRIES:
                    return
            for sub in all_combine_idx(m,idx+1,tb):
                if tb['n']>MAX_SEARCH_ENTRIES:
                    return
                yield [w]+sub

def chn_rank(word):
    q = chn_freq.get(word,min_freq*10)
    return q

def all_combine(m,idx):
    tb = {'n':0}
    all_index_list = sorted(all_combine_idx(m,idx,tb),key=lambda L: sum(chn_rank(m[i][j]) for i,j in enumerate(L) ) ,reverse=True)
    if len(m)>1:
        all_index_list = all_index_list[:MAX_SHOW_ENTRIES]
    for column in all_index_list:
        yield "\n".join(m[i][column[i]] for i in xrange(len(m)))


def pyshort_filter(mixed,ct):
    mixed = mixed.replace("'","")
    m = []
    for chunk in re_eng.split(mixed):
        chunk = chunk.replace("\n","")
        if not (chunk in py_short):
            m.append([chunk])
        else:
            m.append(py_short[chunk][:ct])
    for c in all_combine(m,0):
        yield c

def guess_words_no_sort(sentence):
    if len(sentence)>0:
        bucket = {}
        showed = 0
        py_list = dp_cut(sentence)
        for py_list in dp_cut(sentence):
            sub_showed = 0
            if showed>=MAX_SHOW_ENTRIES:
                break
            m=[]
            for p in py_list:
                if len(p)<6:
                    if len(py_list)==1: #single character, show all candidates
                        span = MAX_SEARCH_ENTRIES
                    else:
                        span = 6
                else:
                    span = 3
                m.append( p2c.get(p,[p])[:span] )
            
            for c in all_combine(m,0):
                if sub_showed>=MAX_SHOW_ENTRIES/2:
                    break
                for cc in pyshort_filter(c, 6):
                    if not cc in bucket:
                        yield cc
                        bucket[cc]=1
                        if len(cc)>1:
                            showed+=1
                            sub_showed+=1
                        if sub_showed>=MAX_SHOW_ENTRIES/2:
                            break
        del bucket

def guess_words(sentence):
    result = guess_words_no_sort(sentence)
    st_list = sorted( [(sum(chn_rank(word) for word in s.split('\n')),s) for s in result], reverse=True)
    return [x[1].replace("\n",'') for x in st_list]

if __name__ == "__main__":
    while True:
        py_sentence = raw_input("")
        gussed_words = guess_words(py_sentence)
        print ",  ".join(gussed_words )

