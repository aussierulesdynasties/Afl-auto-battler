# python work/ovl.py view out lx ly "name:z,z,..." ... : draw satellite-apparent polylines (work/trace.json, xy as seen on Esri)
# lean-corrected (true = apparent - lean*z) at each z into a GE view. lean (lx,ly) m per m of height.
import sys,json,cv2,numpy as np;sys.path.insert(0,'work');import tri as T,earthcam as E
Tr=json.load(open('work/trace.json'));v,out=sys.argv[1],sys.argv[2];lx,ly=float(sys.argv[3]),float(sys.argv[4])
im=cv2.imread(f'ge/{v}.png');c=T.camv(v);cols=[(255,0,255),(0,255,255),(0,128,255),(0,255,0),(255,255,0),(0,0,255)]
for k,a in enumerate(sys.argv[5:]):
  n,zs=a.split(':')
  for j,z in enumerate(map(float,zs.split(','))):
    P=np.array([E.proj(c,[x-lx*z,y-ly*z,z]) for x,y in Tr[n]],np.int32);cv2.polylines(im,[P],False,cols[(k+j)%6],2)
cv2.imwrite(out,im)
