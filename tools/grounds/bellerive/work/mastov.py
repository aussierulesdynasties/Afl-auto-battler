# python work/mastov.py view... : OSM mast bases with a vertical scale (ticks every 10 m to 70 m) projected into GE views
import sys,json,cv2,numpy as np;sys.path.insert(0,'work');import tri as T,earthcam as E
O=json.load(open('work/osm_xy.json'))
for v in sys.argv[1:]:
  im=cv2.imread(f'ge/{v}.png');c=T.camv(v)
  for x,y in O['masts']:
    P=[E.proj(c,[x,y,z]).astype(int) for z in range(0,71,10)]
    cv2.line(im,tuple(P[0]),tuple(P[-1]),(255,0,255),1)
    for k,p in enumerate(P):cv2.circle(im,tuple(p),3,(0,255,255) if k%5 else (0,0,255),-1)
  P=np.array([E.proj(c,[x,y,0]) for x,y in O['pitch']],np.int32);cv2.polylines(im,[P],True,(255,0,255),1)
  cv2.imwrite(f'work/mv_{v}.png',im)
