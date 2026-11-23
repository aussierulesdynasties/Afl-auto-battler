import json, numpy as np, collections
D='data/gmhba/prep/'
f=np.load(D+'far_h.npy'); print('far', f.shape, f.min(), f.max(), np.percentile(f,[5,50,95]))
B=json.load(open(D+'buildings.json')); print(len(B), B[0].keys())
print(collections.Counter(b['c'] for b in B))
T=[b for b in B if b['c']=='tower']
T.sort(key=lambda b:-b['h'])
for b in T[:25]:
    P=np.array(b['p']); print(round(b['h']), P.mean(0).round(), {k:v for k,v in b.items() if k not in('p',)})
tr=json.load(open(D+'trees.json')); print('trees', len(tr), collections.Counter(t[2] for t in tr))
