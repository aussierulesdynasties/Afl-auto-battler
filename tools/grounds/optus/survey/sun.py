"""The sun's direction in Google Earth's Optus imagery, from the east roof's shadow on the turf.

Walks rays from the oval's centre at turf height through the six straight-down shots (gtrace.py), finds where the lit
turf drops into shadow, and fits the shift that carries the roof's inner edge (survey/inner_c.json, 41 m up) onto that
shadow line. Shift length L gives the elevation atan(41/L); its direction the bearing. Result in sun.json; captures
take it as PREINSPECT_SUN=az,el (tools/visual/preinspect_look.gd) so colours compare under Google Earth's light.
"""
import sys,math,json,numpy as np
sys.path.insert(0,'/home/user/Afl-auto-battler/tools/grounds/optus/survey');sys.path.insert(0,'/home/user/Afl-auto-battler/tools/grounds/optus')
import gtrace as G, shape as SH
from scipy.optimize import least_squares
IC=np.array(json.load(open('/home/user/Afl-auto-battler/tools/grounds/optus/survey/inner_c.json')));IZ=41.0
S=G.shots()
pts=[]
for s in S:
  for th in np.radians(np.arange(-80,81,2)):
    rs=np.arange(20,90,0.05);L,ok=G.ray_profile(s,th,rs,0.0)
    if not ok.all():continue
    # first sustained drop: bright turf (median of 3 m before) to dark (median of 3 m after), dark run 2 m
    for i in range(60,len(rs)-60):
      a=np.median(L[i-60:i]);b=np.median(L[i+20:i+60])
      if a>70 and b<0.55*a and (L[i:i+40]<(a+b)/2).all():
        t=(a+b)/2;k=i-20
        while L[k]>t:k+=1
        pts.append((s['name'],th,rs[k]));break
print(len(pts))
P=np.array([[G.OC[0]+r*math.cos(th),G.OC[1]+r*math.sin(th)] for _,th,r in pts])
TH=np.radians(np.arange(0,360,0.25));R=np.array([SH.fourier(IC,t) for t in TH]) if hasattr(SH,'fourier') else None
C=np.stack([G.OC[0]+R*np.cos(TH),G.OC[1]+R*np.sin(TH)],1)
def res(t):
  Q=C+t;d=np.sqrt(((P[:,None,:]-Q[None])**2).sum(2)).min(1);return d
r=least_squares(res,[-10,0],loss='soft_l1',f_scale=0.5);t=r.x;d=res(t)
L=np.hypot(*t);el=math.degrees(math.atan2(IZ,L));az=math.degrees(math.atan2(-t[0],-t[1]))%360
print('shift',t.round(2),'len',round(L,2),'sun elevation %.1f azimuth (model frame, from north) %.1f'%(el,az),'fit med %.2f p90 %.2f m n %d'%(np.median(d),np.percentile(d,90),len(d)))
for it in range(3):
  keep=d<max(1.5,np.percentile(d,60));P0=P;P=P0[keep]
  r=least_squares(res,t,loss='soft_l1',f_scale=0.3);t=r.x;d=res(t)
  L=np.hypot(*t);el=math.degrees(math.atan2(IZ,L));az=math.degrees(math.atan2(-t[0],-t[1]))%360
  out=dict(az=round(az,1),el=round(el,1),n=int(len(P)),med_m=round(float(np.median(d)),2),p90_m=round(float(np.percentile(d,90)),2));print('trim',len(P),'shift',t.round(2),'el %.1f az %.1f med %.2f p90 %.2f'%(el,az,np.median(d),np.percentile(d,90)))
  P=P0 if False else P;d=res(t)
json.dump(out,open(__file__.replace('sun.py','sun.json'),'w'),indent=1)
