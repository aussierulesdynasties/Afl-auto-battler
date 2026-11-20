import sys,json,numpy as np
sys.path.insert(0,'C:/kt/bruce1990/.claude/review/bruce_model')
import aerial90 as A
from PIL import Image,ImageDraw
P=json.load(open('C:/kt/bruce1990/.claude/review/bruce_model/parts.json'))
TH=np.array(P['ring_th']);zo=np.array([p[2] for p in P['rings']['top_out']])
z=dict(toe_a=0.6,toe=1.0,top_in=zo,top_out=zo,foot=0.0,path_out=0.0,conc_out=0.0)
R=A.rings(TH,z)
# walkway heights along the rake
for k in('walk_a','walk_b'):
    s=(R[k]-R['toe'])/(R['top_in']-R['toe']);z[k]=1.0+s*(zo-1.0)
R=A.rings(TH,z)
im=Image.open('bruce/legacy/src90.png').convert('RGB');d=ImageDraw.Draw(im)
C={'fence':(255,0,255),'toe_a':(255,255,255),'toe':(255,255,0),'walk_a':(0,255,255),'walk_b':(0,160,255),'top_in':(255,128,0),'top_out':(255,0,0),'foot':(0,255,0),'path_out':(128,0,255),'conc_out':(0,0,255)}
for k,c in C.items():
    zz=np.broadcast_to(np.asarray(z.get(k,0.4),float),TH.shape)
    Q=np.c_[A.CX+R[k]*np.cos(TH),A.CY+R[k]*np.sin(TH)]
    d.line([tuple(p) for p in A.m2px(Q,zz)],fill=c,width=1)
im.crop((450,400,1650,1600)).save('chk90.png')
for n,b in {'NE':(1150,520,1450,820),'E':(1250,800,1550,1100),'SE':(1100,1050,1400,1350),'S':(800,1200,1100,1500),'SW':(560,1000,860,1300),'N':(850,480,1150,780)}.items():
    im.crop(b).resize((600,600),Image.LANCZOS).save('c90_%s.png'%n)
