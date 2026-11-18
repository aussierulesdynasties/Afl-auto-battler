# near-side roofs: front edge solved on the ray at 1 m beyond the fence (the roof overhangs the front rows);
# back edge solved at the front height + 2 m (nearest front point by pixel x). Left white roof at 15 m.
import json
from subB import *
C=np.array(CAM[:3])
def at_d(u,v,dt=1.0):
    w=ray(CAM,u,v,CX,CY)
    def f(t):X=C+t*w;d=X[:2]-C0;ad=math.degrees(math.atan2(d[1],d[0]));return math.hypot(*d)-rf(ad)-dt
    ts=np.linspace(10,3000,3000);fs=[f(t) for t in ts]
    for i in range(len(ts)-1):
        if fs[i]>0>=fs[i+1]:
            a,b=ts[i],ts[i+1]
            for _ in range(50):
                m=(a+b)/2
                if f(m)>0:a=m
                else:b=m
            X=C+a*w;d=X[:2]-C0;return [float(math.degrees(math.atan2(d[1],d[0]))),float(dt),float(X[2])]
def back(pts,front_pix,front):
    out=[]
    for u,v in pts:
        k=min(range(len(front_pix)),key=lambda i:abs(front_pix[i][0]-u));z=front[k][2]+2.0
        a,d,_=pol(u,v,z);out.append([float(a),float(d),float(z)])
    return out
J=json.load(open('layoutB.json'))
sfp=[(276,370),(300,405),(340,425),(415,455),(490,472),(565,480),(640,482),(668,482)]
SF=[[float(a),float(d),15.0] for a,d,_ in (pol(u,v,15.0) for u,v in((205,250),(235,300)))]+[at_d(u,v) for u,v in sfp]
sbp=[(147,265),(175,330),(230,400),(315,455),(390,490),(465,505),(540,517),(615,522),(690,525)]
J['SF']=SF;J['SB']=back(sbp,[(205,250),(235,300)]+sfp,SF)
nfp=[(670,457),(720,446),(768,430)];NF=[at_d(u,v) for u,v in nfp]
NF+= [list(map(float,pol_rake(u,v,0.5,0.5,5.0))) for u,v in((830,415),(855,400),(852,365),(850,325))]
J['NF']=NF;J['NB']=back([(690,495),(790,475),(880,450),(912,400),(910,330)],nfp+[(830,415),(855,400),(852,365),(850,325)],NF)
for k in('SF','SB','NF','NB'):print(k,[(round(a,1),round(d,1),round(z,1)) for a,d,z in J[k]])
json.dump(J,open('layoutB.json','w',newline=''))
