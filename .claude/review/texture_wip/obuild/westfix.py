# West side (166-250 deg) re-fit to photo o2 (camL back-projections) and the Esri satellite (r2/unwW18.png, r2/unw_2.png).
# Measured on 2026-11-19:
#  band base on the 6.4 m deck, photo px -> plan r: (1300,805) 173.6/132.8, (1400,795) 180.5/140.1, (1450,784) 184.3/143.4,
#    (1500,760) 189.8/145.1, (1550,712) 199.1/145.4, (1568,680) 205.3/145.3; satellite dark band edge 212/146, 220/142, 228/138
#  band top at that radius: 18.7 m @170, 18.2 @177, 17.9 @180, 18.4 @184, 17.8 @189 -> 18 m, no step at segment 73
#  podium parapet at 6.4 m: (1563,793) 188.5/158.3, (1593,760) 193.8/157.5, (1623,712) 201.8/156.9; OSM wall 695799453 r 159-160
#    at 180-199; lower pavilion's edge on the satellite r 150-152 at 205-224
#  terrace canopy outer edge at 22.5 m (posts 4.5 m tall on the terrace): (1290,710) 173.7/128.7 ... (1540,610) 203.0/139.4
# The glass storey, the tall white columns and the roof stay on the old drum line (drum0); the band moves out, the terrace
# deck between them widens (o2: people on a wide terrace under a white canopy).
import json,math,numpy as np
g=json.load(open('geom.json'));oc=np.array(g['oc']);D=np.array(g['drum']);P=np.array(g['pod']);HB=list(g['hb'])
N=len(D)
def ang(p):return math.degrees(math.atan2(p[1]-oc[1],p[0]-oc[0]))%360
def rad(p):return float(np.hypot(*(np.array(p)-oc)))
A=[ang(p) for p in D];R0=[rad(p) for p in D];RP=[rad(p) for p in P]
def r_at(L,a):  # model radius at angle a from list L (by nearest segment interpolation)
    i=min(range(N),key=lambda k:abs((A[k]-a+180)%360-180));return L[i]
a0,a1=166.0,250.0
BK=[(a0,r_at(R0,a0)),(173.6,132.8),(180.5,140.1),(184.3,143.4),(189.8,145.1),(199.1,145.4),(205.3,145.3),(212,146),(220,142),(228,138),(a1,r_at(R0,a1))]
PK=[(a0,r_at(RP,a0)),(175,152),(180.3,160.0),(187.8,160.5),(193.8,160.1),(198.9,159.1),(214,153),(224,150),(a1,r_at(RP,a1))]
CK=[(173.7,129.5),(177.7,133.6),(181.7,136.2),(186.2,138.8),(192,140.9),(198.1,140.8),(204.9,137.5),(214.4,135.5)]  # re-read 2026-11-19: bp(u,v,22.5) of (1380,707),(1447,683),(1513,637),(1537,600),(1547,560)
# glass storey base, o2 grid read 2026-11-19 (r2/glassgrid.png), bp at z 22: (1350,697) 179.3/130.2, (1400,690) 183.0/133.9,
#   (1450,676) 187.7/136.7, (1500,652) 193.9/138.8, (1530,625) 200.1/139.3; canopy edge (1350,710) 177.7/133.6 ... (1530,636) 198.1/140.8,
#   (1537,600) 204.9/138.5, (1547,560) 214.4/137.8. Glass limb in o2 at u=1525 -> 134.5 at 205. Past 205 the glass is hidden in o2: it returns to drum0-4.5 by 250 (under the roof).
GK=[(a0,r_at(R0,a0)-4.5),(177,128.5),(179.3,130.2),(183,133.9),(187.7,136.7),(193.9,138.8),(200.1,139.3),(205,134.5),(214,132),(228,130),(a1,r_at(R0,a1)-4.5)]
def itp(K,a):return float(np.interp(a,[k[0] for k in K],[k[1] for k in K]))
nd=[];npd=[];can=[];gl=[]
for i in range(N):
    a=A[i];u=(D[i]-oc)/np.linalg.norm(D[i]-oc);up=(P[i]-oc)/np.linalg.norm(P[i]-oc)
    if a0<=a<=a1:
        nd.append((oc+u*itp(BK,a)).tolist());npd.append((oc+up*max(itp(PK,a),itp(BK,a)+6)).tolist())
    else:nd.append(D[i].tolist());npd.append(P[i].tolist())
    if 173.7<=a<=214.4:can.append([i,itp(CK,a)])
    gl.append((oc+((D[i]-oc)/R0[i])*(itp(GK,a) if a0<=a<=a1 else R0[i]-4.5)).tolist())
# satellite (r2/topov_lean_W.png): the orange-roofed pavilion's east wall is x -183.3 for y -16..18.5; the deck stops at it
for i in range(N):
    q=np.array(npd[i])
    if q[0]<-183.3 and -16<=q[1]<=18.5:
        u=(q-oc)/np.linalg.norm(q-oc);npd[i]=(oc+u*((-183.3-oc[0])/u[0])).tolist()
for i in range(73,82):HB[i]=HB[72]+(HB[82]-HB[72])*(i-72)/10   # the 2.6 m step at 73 is not in o2
g['drum0']=g.get('drum0',D.tolist());g['drum']=nd;g['pod']=npd;g['hb']=HB;g['canopy']={'z':22.0,'r':can};g['glass']=gl
g['note']+='; west 166-250: band, podium, canopy from o2 + satellite, glass on drum0 (r2/westfix.py)'
json.dump(g,open('geom.json','w',newline=''))
print('moved',sum(1 for a,b in zip(nd,D) if np.hypot(*(np.array(a)-b))>0.3),'canopy segs',len(can))
for i in range(60,165,8):print(i,round(A[i],1),'drum %.1f->%.1f pod %.1f->%.1f hb %.1f'%(R0[i],rad(nd[i]),RP[i],rad(npd[i]),HB[i]))
