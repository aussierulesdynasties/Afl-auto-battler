# Arena edge from the GE views: walk from the field centre outwards in each view until the grass ends; the edge pixel
# is cast onto the field plane (z=-5.3). Output: bearing -> radius samples, median per 2 degrees.
import sys,cv2,numpy as np,json;sys.path.insert(0,'work');import earthcam as E,tri as T
ZF=-5.3;V=sys.argv[1:] or ['o%03d'%h for h in range(0,360,45)]+['l%03d'%h for h in range(0,360,45)]
S=[]
for v in V:
    im=cv2.imread(f'ge/{v}.png');hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
    g=(hsv[...,0]>8)&(hsv[...,0]<80)&(hsv[...,1]>45)&(hsv[...,2]>22)
    g=cv2.morphologyEx(g.astype(np.uint8),cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    c=T.camv(v);o=E.proj(c,(0,0,ZF))
    hd=float(v[1:])
    for b in np.arange(0,360,1.0):
        if abs(((b-hd+180)%360)-180)>55: continue
        a=np.radians(b);last=None
        for r in np.arange(40,100,0.25):
            p=E.proj(c,(r*np.sin(a),r*np.cos(a),ZF));u,w=int(p[0]),int(p[1])
            if not(0<=u<1920 and 90<=w<1040): break
            if g[w,u]: last=r
            elif last is not None and r-last>4.0: break
        if last: S.append((v,b,last))
json.dump(S,open('work/fence_s.json','w'))
A=np.array([(b,r) for _,b,r in S]);out=[]
for b in np.arange(0,360,2):
    rr=A[np.abs(((A[:,0]-b+180)%360)-180)<=1.0,1]
    if len(rr): out.append((int(b),float(np.median(rr)),float(np.percentile(rr,25)),float(np.percentile(rr,75)),len(rr)))
for o in out[::5]: print(o)
json.dump(out,open('work/fence.json','w'))
