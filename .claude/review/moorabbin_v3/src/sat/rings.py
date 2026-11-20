import json,math,numpy as np
from PIL import Image,ImageDraw
O=json.load(open('C:/Users/DANTE/AppData/Local/Temp/claude/9f4017b9c485d8cb/fb8d066d-4ddf-4085-adc6-c6288b802d1c/scratchpad/moor/build.json'))
R=json.load(open('reg.json'));MPP=R['mpp'];pm=R['pmean'];cx,cy=833.577,922.026
f=lambda p:(cx+(p[0]-pm[0])/MPP,cy-(p[1]-pm[1])/MPP)
P=np.array(O['pitch']);P=P[:-1] if np.allclose(P[0],P[-1]) else P;PC=P.mean(0)
ang=np.arctan2(P[:,1]-PC[1],P[:,0]-PC[0]);rad=np.hypot(P[:,0]-PC[0],P[:,1]-PC[1]);o_=np.argsort(ang)
rp=lambda a:np.interp(a,ang[o_],rad[o_],period=2*math.pi)
def polar(xy):
    xy=np.array(xy);a=np.arctan2(xy[:,1]-PC[1],xy[:,0]-PC[0]);return a,np.hypot(xy[:,0]-PC[0],xy[:,1]-PC[1])-rp(a)
pt=lambda a,d:(PC[0]+(rp(a)+d)*math.cos(a),PC[1]+(rp(a)+d)*math.sin(a))
sf=np.array(O['stand']['front']);sr=np.array(O['stand']['rear']);fa,fd=polar(sf);ra,rd=polar(sr);fa=np.unwrap(fa);ra=np.unwrap(ra)
lo,hi=min(fa.min(),ra.min()),max(fa.max(),ra.max());wrap=lambda a:np.mod(a-lo,2*math.pi)+lo
iu=lambda a,A,V:np.interp(a,A[np.argsort(A)],V[np.argsort(A)])
ta,td=polar(O['terr_out']);ta=wrap(ta)
AA=np.concatenate([ta,fa]);VV=np.concatenate([td,iu(fa,ra,rd)]);oo=np.argsort(AA);AA=AA[oo];VV=VV[oo]
d_out=lambda a:float(np.interp(wrap(a),AA,VV,period=2*math.pi))
A=np.linspace(-math.pi,math.pi,720,endpoint=False)
im=Image.open('wb_3026_z19.png').convert('RGB');d=ImageDraw.Draw(im)
for off,c in ((0,(0,255,255)),(6,(255,255,0))):
    L=[f(pt(a,d_out(a)+off)) for a in A if not wrap(a)<=hi];d.point(L,fill=c)
L=[f(pt(a,0)) for a in A];d.point(L,fill=(255,0,255))
for p in O['terr_out']:x,y=f(p);d.ellipse((x-3,y-3,x+3,y+3),outline=(255,80,0))
im.save('ov_rings.png')
S=Image.new('RGB',(4*400,2*400));dd=ImageDraw.Draw(S)
for i,a in enumerate(range(0,360,45)):
    r=430 if a in (0,180) else 400
    x=cx+r*math.cos(math.radians(a));y=cy-r*math.sin(math.radians(a))*1.05
    S.paste(im.crop((int(x-190),int(y-190),int(x+190),int(y+190))),((i%4)*400+10,(i//4)*400+10));dd.text(((i%4)*400+14,(i//4)*400+12),'%d'%a,fill=(255,255,0))
S.save('ov_rings_sheet.png')
print('PC',PC,'terr_out deg/d',[(round(math.degrees(a)),round(v,1)) for a,v in zip(*polar(O['terr_out']))])
