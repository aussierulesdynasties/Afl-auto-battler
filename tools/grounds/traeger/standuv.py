# UVs for stand.json in real metres: tiled materials repeat every TILE metres; panels span their face 0..1.
import json,numpy as np
D=json.load(open('stand.json'));T=json.load(open('tex3/tex.json'));TILE=T['TILE'];PANEL=set(T['PANEL'])
O=np.array(D['O']);a=np.array(D['a']);b=np.array(D['b'])
def sf(V):V=np.array(V,float);d=V[:,:2]-O;return np.c_[d@a,d@b,V[:,2]]   # stand frame s,t,z
for m in D['G']:
    if m['mat'] not in TILE and m['mat'] not in PANEL:continue
    Q=sf(m['V']);UV=[]
    if m['mat'] in PANEL:
        lo=Q.min(0);hi=Q.max(0);span=hi-lo;ax=[i for i in np.argsort(-span)[:2]]
        # u along s (or t for side faces), v along z (or t for horizontal faces)
        if span[2]<1e-6:uax,vax=0,1
        else:uax,vax=(0 if span[0]>=span[1] else 1),2
        for f in m['F']:UV.append([[float((Q[i,uax]-lo[uax])/span[uax]),float((Q[i,vax]-lo[vax])/span[vax])] for i in f])
        if m['mat']=='soffit_box':UV=[[[u,1-v] for u,v in f] for f in UV]
    else:
        tu,tv=TILE[m['mat']]
        for f in m['F']:
            P=Q[f];n=np.cross(P[1]-P[0],P[2]-P[0]);n=np.abs(n)
            if n[2]>=n[0] and n[2]>=n[1]:c=(0,1)      # horizontal: s,t (deck ribs run back along t)
            elif n[1]>=n[0]:c=(0,2)                    # faces looking along t: s,z
            else:c=(1,2)                               # end faces: t,z
            UV.append([[float(P[k,c[0]]/tu),float(P[k,c[1]]/tv)] for k in range(len(f))])
    m['UV']=UV
json.dump(D,open('stand_uv.json','w'));print('uv',sum('UV' in m for m in D['G']),'of',len(D['G']))
