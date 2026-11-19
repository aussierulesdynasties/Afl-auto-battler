# python work/osmov.py view tz [out]: OSM outlines projected into a GE view (cams.json), z=0 at field level, tz = GE 'a' minus field altitude
import sys,json,cv2,numpy as np;sys.path.insert(0,'work');import earthcam as E
C=json.load(open('work/cams.json'));O=json.load(open('work/osm_xy.json'))
v=sys.argv[1];dz=float(sys.argv[2]);x0,y0,a,d,h,t=C[v];c=E.cam(h,t,d,tz=a-dz,tx=x0,ty=y0)
im=cv2.imread(f'ge/{v}.png')
for k,col in (('pitch',(255,0,255)),('south_stand',(0,255,0)),('west_stand',(0,128,255))):
    P=np.array([E.proj(c,[x,y,0]) for x,y in O[k]],np.int32);cv2.polylines(im,[P],False,col,2)
cv2.imwrite(sys.argv[3] if len(sys.argv)>3 else f'work/osmov_{v}.png',im)
