# B north-west members building roof: white roof with the stepped terrace rows and the round canopy, laid out in
# photo B pixel space (traced) and drawn analytically per texel: crisp, no photo pixels.  python nwtex.py OUTDIR
import sys,os,json,numpy as np,importlib.util as u
from PIL import Image
sys.path.insert(0,'../b');from camlib import proj
sp=u.spec_from_file_location('s','spec_B.py');S=u.module_from_spec(sp);sp.loader.exec_module(S)
pB=json.load(open('../b/camB.json'))['p'];top=np.array(S._nwT)
x0,x1,y0,y1=top[:,0].min(),top[:,0].max(),top[:,1].min(),top[:,1].max();N=2048
v,uu=np.mgrid[0:N,0:N];U=(uu+0.5)/N;V=1-(v+0.5)/N
X=np.stack([x0+U*(x1-x0),y0+V*(y1-y0),np.full(U.shape,12.0)],-1).reshape(-1,3)
q=proj(pB,X).reshape(N,N,2);px,py=q[...,0],q[...,1]
rng=np.random.default_rng(3)
a=np.zeros((N,N,3));a[:]=(236,236,232)
# roof sheet seams every 0.5 photo px along the long edge direction
d=np.array([0.906,0.423]);n=np.array([-0.423,0.906]);P0=np.array([417.0,461.0])
A=(px-P0[0])*d[0]+(py-P0[1])*d[1];Sx=(px-P0[0])*n[0]+(py-P0[1])*n[1]
seam=(np.mod(A,2.0)<0.06);a[seam]=(214,214,212)
# terrace: strip measured on photo B (417,461)-(450,483), 8 px wide; 4 stepped rows 2.1 px apart: tread light grey, riser shadow dark, rail line
band=(A>0)&(A<37)&(Sx>-1.0)&(Sx<7.5)
a[band]=(206,204,198)
for k in range(4):
    s0=k*2.1
    r=band&(Sx>s0-0.35)&(Sx<s0+0.35);a[r]=(78,70,62)          # riser shadow
    r=band&(Sx>s0+0.35)&(Sx<s0+0.6);a[r]=(150,120,92)        # timber bench line
a+=rng.standard_normal((N,N,1))*2.0
Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(os.path.join(sys.argv[1],'nw_roof.png'));print('ok',x1-x0,y1-y0)
