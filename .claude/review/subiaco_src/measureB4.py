import json
exec(open('measureB2.py').read().split("J=json.load")[0])   # at_d, back helpers
J=json.load(open('layoutB.json'))
nfp=[(668,457),(720,446),(768,430),(800,418),(835,405)];NF=[at_d(u,v) for u,v in nfp];print(NF)
nfp=[p for p,q in zip(nfp,NF) if q];NF=[q for q in NF if q]
nbp=[(680,472),(760,452),(850,426),(902,412)]
NB=[];
for u,v in nbp:
    k=min(range(len(nfp)),key=lambda i:abs(nfp[i][0]-u));z=NF[k][2]+1.0;a,d,_=pol(u,v,z);NB.append([float(a),float(d),float(z)])
J['NRF']=NF;J['NRB']=NB
# grey corner roof outline at 18 m
J['CR']=[[float(x) for x in pol(u,v,18.0)] for u,v in((850,322),(905,330),(910,400),(880,410),(855,405),(848,360))]
for k in('NRF','NRB','CR'):print(k,[(round(a,1),round(d,1),round(z,1)) for a,d,z in J[k]])
json.dump(J,open('layoutB.json','w',newline=''))
