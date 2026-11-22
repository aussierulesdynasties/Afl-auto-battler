# Run from a work folder holding the Google Earth shots in ge/ (never committed; looking and measuring only).
import numpy as np, json, math
import os; ENGIE_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'model', 'engie.json')
FIT=json.load(open('fit.json')); p=np.array(FIT['p']); K=FIT['K']
T=np.linspace(0,2*np.pi,7200,endpoint=False)
r=p[2]+sum(p[2+2*k-1]*np.cos(k*T)+p[2+2*k]*np.sin(k*T) for k in range(1,K+1))
x=p[0]+r*np.sin(T); y=p[1]+r*np.cos(T)
dx=np.gradient(x); dy=np.gradient(y); L=np.hypot(dx,dy); nx,ny=-dy/L,dx/L   # outward
def polar(d):
    X=x+d*nx; Y=y+d*ny; b=np.degrees(np.arctan2(X,Y))%360; R=np.hypot(X,Y)
    o=np.argsort(b); b,R=b[o],R[o]
    q=np.arange(0,360,1.0); return [[float(a),round(float(v),2)] for a,v in zip(q,np.interp(q,np.r_[b-360,b,b+360],np.r_[R,R,R]))]
dF,dB=-p[-2],-p[-1]
P=ENGIE_JSON
D=json.load(open(P))
old={k:D[k] for k in ('fence','rf','rb')}
D['fence']=polar(0.0); D['rf']=polar(dF); D['rb']=polar(dB)
D['outline']={'_note':'One smooth curve fitted to a trace of Google Earth top-down (tools/grounds/engie/fit): r(t) = a0 + sum_k a_k cos kt + b_k sin kt about (cx, cy), t clockwise from north; the field edge is the curve, every other ring an exact normal offset of it.',
              'cx':float(p[0]),'cy':float(p[1]),'K':K,'coef':[float(v) for v in p[2:3+2*K]],'offsets':{'field_edge':0.0,'stand_front':5.0,'open_stand_front':8.4,'roof_front':round(float(dF),2),'roof_back':round(float(dB),2)}}
json.dump(D,open(P,'w'),indent=1)
def per(t,q):
    t=np.array(sorted(t),float); return np.interp(q,np.r_[t[:,0]-360,t[:,0],t[:,0]+360],np.r_[t[:,1],t[:,1],t[:,1]])
for b in range(0,360,30):
    print(b,' '.join('%s %.1f->%.1f'%(k,per(old[k],b),per(D[k],b)) for k in ('fence','rf','rb')))
print('offsets',dF,dB)
