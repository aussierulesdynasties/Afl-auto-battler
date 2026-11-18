import numpy as np,json,math
from PIL import Image
from subA import *
im=np.array(Image.open('refs/c/01.jpg').convert('RGB')).astype(float);Lm=im.mean(2);sat=im.max(2)-im.min(2)
roof=(Lm>165)&(sat<45)
HR=18.0;GS=[]
for x in range(200,612,6):
    runs=[];s=None
    for y in range(60,260):
        if roof[y,x] and s is None:s=y
        if not roof[y,x] and s is not None:runs.append((s,y-1));s=None
    runs=[r for r in runs if r[1]-r[0]>=10]
    if not runs:continue
    yb,yf=runs[-1]
    ab,db,_=pol(x,yb,HR);af,df,_=pol(x,yf+1,HR);GS.append((float(ab),float(db),float(af),float(df)))
RAKE=0.15
OUT=[(775,175),(800,165),(850,160),(900,165),(945,175),(990,200),(1030,228),(1060,240),(1100,245),(1105,255),(1110,320),(1120,380),(1130,440),(1133,467),(1100,503),(1030,533),(990,556)]
OUTP=[pol_rake(u,v,RAKE) for u,v in OUT]
WALL=[(921,545),(850,552),(800,555),(700,556),(614,552),(550,549),(479,545),(386,538),(307,527),(243,506),(193,441)]
WALLP=[pol_rake(u,v,RAKE,dz=1.2) for u,v in WALL]
PAN=[pol_rake(u,v,RAKE,dz=3.0) for u,v in((933,550),(973,515),(1020,475))]
NS=[pol(u,v,14) for u,v in((634.5,148),(642.5,112),(770,121),(767.5,158))]
NSF=[pol_rake(u,v,RAKE,dz=1.5) for u,v in((630,174),(700,176),(772,180))]
RIBF=[pol(u,v,10) for u,v in((190,232),(186,280),(188,330),(192,370))]
RIBB=[pol(u,v,12) for u,v in((120,245),(121,280),(122,305),(126,335),(130,365))]
ADM=[pol(u,v,10) for u,v in((108,147),(225,160),(200,195),(165,205),(140,235),(135,258),(62,242))]
# embedded buildings on the south side (roof corners, roof heights)
B1=[pol(u,v,5) for u,v in((705,548),(840,530),(845,553),(712,572))]
B2=[pol(u,v,4) for u,v in((545,541),(632,546),(630,560),(545,556))]
B3=[pol(u,v,4) for u,v in((615,548),(705,552),(703,565),(613,562))]
CAN=pol(806,522,8)
# SE light pole: base on the ground, top on the same vertical
Xb=at_z(CAM,924,554,CX,CY,0.0);Xt=on_vline(CAM,941,470,CX,CY,Xb[:2])
POLE=[float(Xb[0]),float(Xb[1]),float(Xt[2])]
J=dict(C0=list(map(float,C0)),U=list(map(float,U)),L=float(L),fence=FJ,GS=GS,HR=HR,RAKE=RAKE,OUT=OUTP,WALL=WALLP,PAN=PAN,NS=NS,NSF=NSF,RIBF=RIBF,RIBB=RIBB,ADM=ADM,B1=B1,B2=B2,B3=B3,CAN=CAN,POLE=POLE)
json.dump(J,open('layoutA.json','w'),default=float)
for k in('OUT','WALL','PAN','NS','NSF','RIBF','RIBB','ADM','B1','CAN','POLE'):print(k,J[k])
print('GS',len(GS),GS[0],GS[-1])
