import numpy as np,json
from cam import *
p=load();J=json.load(open('cam.json'));t=J['towers']
names=[('NL_pole',4),('NL_lat',4),('FL_pole',3),('FL_2',3),('FR_pole',3),('FR_2',3),('R_pole',3),('R_lat',3)]
HT={'NL_pole':((150,503),(145,602)),'NL_lat':((197,670),(197,720)),'FL_pole':((396,282),(396,311)),'FL_2':((342,384),(342,410)),
'FR_pole':((896,281),(896,300)),'FR_2':((941,352),(941,371)),'R_pole':((1358,460),(1355,512)),'R_lat':((1297,537),(1297,580))}
BASEPX={'NL_pole':(211,1039),'NL_lat':(220,847),'FL_pole':(411,500),'FL_2':(357,528),'FR_pole':(894,484),'FR_2':(935,496),'R_lat':(1272,750)}
out={};k=0
for nm,n in names:
    k+=2+n;zb=None
    b=at_z(p,*BASEPX[nm])[:2] if nm in BASEPX else None
    if b is None:
        # base hidden: vertical plane of the visible pole meets the ground; take the point nearest the satellite shadow foot
        w1=ray(p,1360,511.7);w2=ray(p,1338.3,706.7);nn=np.cross(w1,w2);C=p[:3];q=np.array([63.5,-77.0])
        nxy=nn[:2];d=np.array([-nxy[1],nxy[0]]);x0=nxy*(nn@C)/(nxy@nxy);b=x0+((q-x0)@d)/(d@d)*d
    out[nm]=dict(base=b.round(2).tolist(),top=round(float(at_vline(p,*HT[nm][0],b)[2]),2),hbot=round(float(at_vline(p,*HT[nm][1],b)[2]),2),basepx_z=None if zb is None else round(float(zb),2))
    print(nm,out[nm])
json.dump(out,open('towers.json','w'),indent=1)
