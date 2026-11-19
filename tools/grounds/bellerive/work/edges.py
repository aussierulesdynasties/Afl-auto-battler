# python work/edges.py : per-bearing radii from the polar unwrap: field edge (end of green), white roof start/end (longest white run)
import numpy as np,cv2,json
U=np.load('work/unwrap.npy');H=cv2.cvtColor(U,cv2.COLOR_BGR2HSV).astype(int);B=np.arange(0,360,0.5);R=np.arange(50,180,0.25)
g=(H[:,:,0]>25)&(H[:,:,0]<60)&(H[:,:,1]>60)&(H[:,:,2]>50)
w=(H[:,:,2]>190)&(H[:,:,1]<45)
out=[]
for i,b in enumerate(B):
  gg=cv2.morphologyEx(g[i].astype(np.uint8)[None],cv2.MORPH_OPEN,np.ones((1,9)))[0]
  k=np.argmax(gg==0);fe=R[k]
  ww=cv2.morphologyEx(w[i].astype(np.uint8)[None],cv2.MORPH_CLOSE,np.ones((1,9)))[0]
  best=(0,0,0);s=None
  for j in range(len(R)+1):
    v=ww[j] if j<len(R) else 0
    if v and s is None:s=j
    if not v and s is not None:
      if j-s>best[0]:best=(j-s,s,j)
      s=None
  out.append([float(b),float(fe),float(R[best[1]]) if best[0] else None,float(R[best[2]-1]) if best[0] else None])
json.dump(out,open('work/edges.json','w'))
for r in out[::10]:print(r)
