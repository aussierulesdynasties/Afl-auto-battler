exec(open('wproj.py').read().split("JB=json.load")[0])
JB=json.load(open('layoutB.json'))
def fP(S,c):
    S=sorted(S);return lambda a:float(np.interp(a,[s[0] for s in S],[s[c] for s in S]))
SF=[[a,max(d,0.5),z] for a,d,z in JB['SF']];SB=JB['SB']
sfd,sfz,sbd,sbz=fP(SF,1),fP(SF,2),fP(SB,1),fP(SB,2)
print('SF',sorted(SF)[:3]);print('SB',sorted(SB)[:3])
p0,p1=np.array([148.,277.]),np.array([227.,273.]);u=(p1-p0)/np.linalg.norm(p1-p0);n=np.array([-u[1],u[0]])
for a in np.arange(-141.4,-125,1.0):
    f=proj(cam,np.array([P(a,sfd(a),sfz(a))]),500,300)[0];b=proj(cam,np.array([P(a,sbd(a),sbz(a))]),500,300)[0]
    print('%.1f front %s off %.1f   back %s off %.1f'%(a,np.round(f,1),(f-p0)@n,np.round(b,1),(b-p0)@n))
