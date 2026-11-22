import json, numpy as np
S=json.load(open('data/adelaide/prep/surfaces.json')); near=np.load('data/adelaide/prep/near_h.npy'); NEAR=1500; NS=2*NEAR/(near.shape[0]-1)
for w in S['water']:
    v=np.array(w['v']); i=np.clip(np.round((v[:,1]+NEAR)/NS).astype(int),0,400); j=np.clip(np.round((v[:,0]+NEAR)/NS).astype(int),0,400)
    h=near[i,j]; print(round(w['z'],2), 'n',len(v),'bbox',v.min(0).round(),v.max(0).round(),'h pct 5/50/95',np.percentile(h,[5,50,95]).round(2))
