import json,math,sys,numpy as np
from PIL import Image
from scipy.ndimage import shift as nshift
S=np.asarray(Image.open('../obuild/sat/sat_025.png').convert('RGB')).astype(int)
W=(S.min(2)>175)&(S.max(2)-S.min(2)<45);M0=np.load(sys.argv[1]).astype(float)
J=json.load(open('../obuild/geom.json'));oc=J['oc'];X0,Y1,R=-260,230,0.25
L=np.array([56,-5])/44.7  # px per metre of height (fit at mean roof height)
Mi=nshift(M0,L*42.8,order=1)>0.5;Mo=nshift(M0,L*46.55,order=1)>0.5
def at(A,a,r):
    u,v=int(round((oc[0]+math.cos(a)*r-X0)/R)),int(round((Y1-oc[1]-math.sin(a)*r)/R));return A[v,u]
def medge(A,a,first):
    rs=np.arange(60,200,R);w=np.array([at(A,a,r) for r in rs]);i=np.where(w)[0];return rs[i[0]] if first else rs[i[-1]]
def run(a,r,step):return all(at(W,a,r+step*k*R) for k in range(8))
rows=[]
for d in range(0,360,2):
    a=math.radians(d);mi=medge(Mi,a,1);mo=medge(Mo,a,0)
    si=next((r for r in np.arange(mi-8,mi+8,R) if run(a,r,1)),None)
    so=next((r for r in np.arange(mo+8,mo-8,-R) if run(a,r,-1)),None)
    rows.append([d,si,so,mi,mo])
json.dump([[float(x) if x is not None else None for x in r] for r in rows],open(sys.argv[2],'w'))
for k,n in((1,'inner'),(2,'outer')):
    d=np.array([r[k+2]-r[k] for r in rows if r[k] is not None]);g=d[abs(d)<4]
    print(n,'readable %d/180 median %+.2f mean|err| %.2f p90 %.2f max %.2f  <=1m %d'%(len(g),np.median(g),np.abs(g).mean(),np.percentile(np.abs(g),90),np.abs(g).max(),(abs(g)<=1).sum()))
