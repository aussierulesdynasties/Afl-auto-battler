# python work/samp.py : median photo colour of the outer roof (between teal band and outer edge) per 30 deg, from the best near-side l/o view
import json,cv2,numpy as np,math,sys
sys.path.insert(0,'work');import earthcam as E
D=json.load(open('model/mcg.json'));C=json.load(open('work/cams.json'))
def per(t,b):
  t=sorted(t);b%=360;t2=t+[[t[0][0]+360,t[0][1]]]
  for (b0,v0),(b1,v1) in zip(t2,t2[1:]):
    bb=b if b>=b0 else b+360
    if b0<=bb<=b1:return v0+(v1-v0)*(bb-b0)/max(b1-b0,1e-6)
ri=lambda b:per([x[:2] for x in D['roof_inner']],b);ro=lambda b:per([x[:2] for x in D['roof_outer']],b);rh=lambda b:per(D['roof_h'],b);tw=lambda b:per(D['roof_teal_w'],b)
def cam(v):
  x,y,a,d,h,t=C[v];return E.cam(h,t,d,tz=a-13,tx=x,ty=y)
for b in range(0,360,30):
  vs=[];best=None
  for v in [f'l{h:03d}' for h in range(0,360,45)]:
    if (b-(int(v[1:])+180))%360 not in range(0,40) and (int(v[1:])+180-b)%360 not in range(0,40):continue
    best=v
  c=cam(best);img=cv2.imread(f'ge/{best}.png');px=[]
  for db in np.linspace(-6,6,13):
    bb=b+db;a,o=ri(bb)+tw(bb)+3,ro(bb)-3
    for r in np.linspace(a,o,10):
      z=rh(bb)-2*(r-ri(bb))/(ro(bb)-ri(bb));u,vv=E.proj(c,(r*math.sin(math.radians(bb)),r*math.cos(math.radians(bb)),z))
      if 0<=u<1920 and 90<=vv<1040:px.append(img[int(vv),int(u)][::-1])
  print(b,best,np.median(px,0).astype(int) if px else None)
