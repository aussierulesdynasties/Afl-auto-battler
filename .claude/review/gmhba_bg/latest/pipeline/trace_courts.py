import numpy as np, json
from PIL import Image
from scipy import ndimage
s=np.asarray(Image.open('data/gmhba/sat.png').convert('RGB')).astype(int)
y0,x0=1500-330,1500-200; sub=s[y0:1500-120,x0:1500-60]; r,g,b=sub[...,0],sub[...,1],sub[...,2]
m=ndimage.binary_opening((b>r+40)&(b>g+25),iterations=1); m=ndimage.binary_closing(m,iterations=1)
lab,n=ndimage.label(m); out=[]
for i in range(1,n+1):
    ys,xs=np.nonzero(lab==i)
    if len(ys)<150: continue
    P=np.c_[xs+x0-1500,1500-(ys+y0)].astype(float); c=P.mean(0); U,S,Vt=np.linalg.svd(P-c,full_matrices=False)
    q=(P-c)@Vt.T; lo,hi=q.min(0),q.max(0)
    box=[list(map(lambda v:round(float(v),1),c+Vt.T@np.array([a,b_]))) for a,b_ in [(lo[0],lo[1]),(hi[0],lo[1]),(hi[0],hi[1]),(lo[0],hi[1])]]
    print(len(ys),[round(float(v)) for v in c],round(float(hi[0]-lo[0])),round(float(hi[1]-lo[1]))); out.append(box)
json.dump(out,open('out/gmhba/court_boxes.json','w'))
