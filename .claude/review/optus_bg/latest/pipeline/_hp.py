import json, numpy as np
P='D:/Temp/claude/14b1484a65bfbd74/76476bc6-b87c-4245-8ecb-61de5d49956b/scratchpad/proto/'
S=json.load(open(P+'spec/optus_fc_hand.json'))['south']; H=json.load(open(P+'_hardpts.json'))
def segd(p,a,b):
    ab=b-a; t=np.clip(np.dot(p-a,ab)/max(np.dot(ab,ab),1e-9),0,1); return np.linalg.norm(p-(a+t*ab))
for e in H:
    pts=np.array(S[e['poly']]['pts'],float); ds=[]
    for q in e['px']:
        p=np.array([e['x0']+q[0]/e['s'], e['y1']-q[1]/e['s']])
        ds.append(min(segd(p,a,b) for a,b in zip(pts,np.roll(pts,-1,0))))
    print(e['name'],len(ds),'p90',round(float(np.percentile(ds,90)),2),'max',round(max(ds),2))
