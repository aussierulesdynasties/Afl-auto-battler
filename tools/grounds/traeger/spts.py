# label stand-frame points on a photo: python spts.py camjson photo x0 y0 x1 y1 scale out
import sys,json,numpy as np
from PIL import Image,ImageDraw
from cam import proj
import stand
cj,ph=sys.argv[1],sys.argv[2];x0,y0,x1,y1,sc=map(int,sys.argv[3:8]);out=sys.argv[8]
p=np.array(json.load(open(cj))['p']);P=stand.P;L=stand.L;W=stand.W;rz=stand.roof_z
pts={'F0':W(0,0,rz(0,0)),'FL':W(L,0,rz(L,0)),'C0':W(0,P['tC'],rz(0,P['tC'])),'CL':W(L,P['tC'],rz(L,P['tC'])),
'K0':W(0,P['tB'],P['zBack']),'KL':W(L,P['tB'],P['zBack']),'Fm':W(L/2,0,rz(L/2,0)),'Cm':W(L/2,P['tC'],rz(L/2,P['tC']))}
im=Image.open(ph).convert('RGB').crop((x0,y0,x1,y1));im=im.resize((im.width*sc,im.height*sc),Image.LANCZOS);d=ImageDraw.Draw(im)
for k,X in pts.items():
    u,v=proj(p,X)[0];U,V=(u-x0)*sc,(v-y0)*sc;d.ellipse([U-5,V-5,U+5,V+5],outline=(0,255,255),width=2);d.text((U+7,V-7),k,fill=(0,255,255));print(k,round(u,1),round(v,1))
im.save(out)
