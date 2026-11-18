import json
from subB import *
J=json.load(open('layoutB.json'))
# towers: base at the visible pole bottom on the ground, height to the visible lamp top (per tower)
bot=[(131,288),(679,185),(873,322),(267,505)];top=[(143,92),(683,35),(878,165),(280,262)]
T=[]
for (ub,vb),(ut,vt) in zip(bot,top):
    X=bp(ub,vb,0)[0]
    best=min(np.linspace(20,90,701),key=lambda h:np.hypot(*(pr(np.array([X[0],X[1],h]))[0]-[ut,vt])))
    T.append([float(X[0]),float(X[1]),float(best)])
J['TOW']=T;print('TOW',[[round(x,1) for x in t] for t in T])
J['GB']=[list(pol(u,v,10.0)) for u,v in((597,140),(640,134),(674,150),(670,166),(602,160))]
J['FL1']=[list(pol(u,v,8.0)) for u,v in((165,157),(205,150),(213,195),(172,202))]
J['FL2']=[list(pol(u,v,5.0)) for u,v in((115,208),(158,203),(165,240),(120,246))]
for k in('GB','FL1','FL2'):print(k,J[k])
# where the near facade foot lands for SB outer points (check vs photo)
for a,d,z in J['SB']:
    X=np.array([C0[0]+(rf(a)+d)*math.cos(math.radians(a)),C0[1]+(rf(a)+d)*math.sin(math.radians(a)),0]);print('SBfoot',round(a),pr(X)[0].round())
json.dump(J,open('layoutB.json','w',newline=''))
