# Director 2026-11-19 via lead: "1: follow photo" - near roof outer edge follows the photo's yellow edge on 163-186 deg; lead 2026-11-19: smooth photo edge over the whole near side 126-236 (238+ trace unreliable, left on satellite).
import json,math,numpy as np
D=json.load(open('geo_j.json'));ang,out,sm,sat=np.load('nearsolve.npy')
R=np.array(D['rout'],float);n=0;mx=0
for i in range(1440):
    a=i/4
    if not 126<=a<=236:continue
    w=1.0 if 130<=a<=232 else (0.5-0.5*math.cos(math.pi*((a-126)/4 if a<130 else (236-a)/4)))
    v=np.interp(a,ang,sm);d=w*(v-R[i]);R[i]+=d;n+=1;mx=max(mx,abs(d))
D['rout']=R.tolist();json.dump(D,open('geo_n.json','w',newline=''))
print('changed',n,'samples, max move %.2f m'%mx)
