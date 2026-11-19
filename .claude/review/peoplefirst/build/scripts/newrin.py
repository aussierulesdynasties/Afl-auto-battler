# rin from the satellite: per 0.25 deg ray from SH, first run of >=1.5 m membrane white (V>215,S<30) = navy/white line.
# model navy line = rin+0.6+nb*sin(pi*ph)  ->  rin = ws-0.6-nb*sin(pi*ph). Towers masked +-3 deg and filled from old rin + local offset.
import json,numpy as np,cv2,sys
from scipy.ndimage import median_filter
S=json.load(open('sat.json'));m=S['mpp'];D=json.load(open('geo_sat.json'));SH=D['roofshift'];N=1440
sat=cv2.imread('sat.png');hs=cv2.cvtColor(sat,cv2.COLOR_BGR2HSV);sw=(hs[...,2]>215)&(hs[...,1]<30)
RG=np.array(D['RG']);RO=np.array(D['rout']);old=np.array(D['rin']);A0,A1=D['a0'],D['a1']
ang=np.arange(N)/4;inroof=np.array([(A0+1<=a<=A1-1) or (A0+1<=a+360<=A1-1) for a in ang])
ws=np.full(N,np.nan)
for i in np.where(inroof)[0]:
    t=np.radians(ang[i]);rs=np.arange(RG[i]+3,RO[i],0.1)
    u=np.round(S['px']+(rs*np.cos(t)+SH[0])/m).astype(int);v=np.round(S['py']-(rs*np.sin(t)+SH[1])/m).astype(int);on=sw[v,u]
    for k in range(len(rs)-15):
        if on[k:k+15].all():ws[i]=rs[k];break
TA=[np.degrees(np.arctan2(y-SH[1],x-SH[0]))%360 for x,y,h in D['towers']]
for ta in TA:ws[np.abs((ang-ta+180)%360-180)<3]=np.nan
# Hampel 1.5 m on +-2 deg
w2=ws.copy()
for i in np.where(inroof)[0]:
    w=ws[[(i+k)%N for k in range(-8,9)]];md=np.nanmedian(w)
    if np.isnan(ws[i]) or abs(ws[i]-md)>1.5:w2[i]=np.nan
# rib phase, as build5 with SATRIBS
V=sorted(D['valleys']);med=sorted(V[i+1]-V[i] for i in range(len(V)-1))[len(V)//2];R=[A0]
for vv in V+[A1]:
    while vv-R[-1]>1.5*med:R.append(R[-1]+med)
    if vv-R[-1]>0.4*med:R.append(vv)
R[-1]=A1
def phase(a):
    for j in range(len(R)-1):
        if R[j]<=a<=R[j+1]:return (a-R[j])/(R[j+1]-R[j])
    return 0.0
new=old.copy()
for i in np.where(inroof)[0]:
    a=ang[i] if ang[i]>=A0 else ang[i]+360;nb=-0.8 if 126.0<ang[i]<252.5 else 0.2
    if not np.isnan(w2[i]):new[i]=w2[i]-0.6-nb*np.sin(np.pi*phase(a))
gap=inroof&np.isnan(w2)
for i in np.where(gap)[0]:
    w=[(i+k)%N for k in range(-24,25)];d=(new-old)[w][~gap[w]];new[i]=old[i]+(np.median(d) if len(d) else 0)
sm=median_filter(np.r_[new[-10:],new,new[:10]],9)[10:-10];new[inroof]=sm[inroof]
# blend 1 deg at each span end
print('rin change per 6 deg:',' '.join(f'{int(a)}:{new[int(a*4)]-old[int(a*4)]:+.1f}' for a in range(0,360,6) if inroof[int(a*4)]))
D['rin']=[float(x) for x in new];json.dump(D,open('geo_sat.json','w',newline=''))
