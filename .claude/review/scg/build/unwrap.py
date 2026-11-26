# unwrap the outer facade cylinder (r=hi(d), z 0..zmax) seen by a camera into an elevation image (px per metre = ppm)
import io,contextlib,cv2,sys
with contextlib.redirect_stdout(io.StringIO()):exec(open('geo.py').read())
cjx=json.load(open(sys.argv[1]));px=cjx['p'];im=cv2.imread(cjx['img'])
d0,d1,zmax,ppm=map(float,sys.argv[3:7])
ds=[d for d in sorted(OUT) if d0<=d<=d1]
# arc length along outer edge
pts=[];s=[0.0]
for d in ds:
    lo,hi,zf,zo,_=OUT[d];a=math.radians(d);pts.append(PC+hi*np.array([math.cos(a),math.sin(a)]))
for i in range(1,len(pts)):s.append(s[-1]+np.linalg.norm(pts[i]-pts[i-1]))
L=s[-1];Wd=int(L*ppm);Hd=int(zmax*ppm)
ss=np.linspace(0,L,Wd);X=np.interp(ss,s,[q[0] for q in pts]);Y=np.interp(ss,s,[q[1] for q in pts])
zz=np.linspace(zmax,0,Hd)
P3=np.stack(np.broadcast_arrays(X[None,:],Y[None,:],zz[:,None]),-1).reshape(-1,3)
uv=proj(px,P3).reshape(Hd,Wd,2).astype(np.float32)
out=cv2.remap(im,uv[...,0],uv[...,1],cv2.INTER_LINEAR,borderValue=(40,0,40))
for i,d in enumerate(ds):
    if d%2==0:
        xx=int(np.interp(s[i],[0,L],[0,Wd-1]));cv2.line(out,(xx,Hd-1),(xx,Hd-8),(0,255,255),1);cv2.putText(out,str(int(d)),(xx-8,Hd-10),0,0.35,(0,255,255),1)
for m in range(0,int(L),10):
    xx=int(m*ppm);cv2.line(out,(xx,0),(xx,6),(255,255,0),1)
cv2.imwrite(sys.argv[2],out);json.dump({'ds':ds,'s':s},open(sys.argv[2]+'.json','w'));print(Wd,Hd,round(L,1))
