import json,math,numpy as np
from PIL import Image,ImageDraw
src=open('build3.py',encoding='utf-8').read()
O=json.load(open('build.json'))
exec(src[src.index("C=O['colors']"):src.index("_bp=np.array")])
exec(open('fitcam.py').read().split('def md')[0].split("G=json.load")[0])
def R(yaw,pitch_,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch_),math.sin(pitch_);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    C=p[:3];M=R(*p[3:6]);fo=p[6];d=(X-C)@M.T
    return np.stack([p[7]+fo*d[:,0]/d[:,2],p[8]-fo*d[:,1]/d[:,2]],1)
cam=np.array(O['cam']);S=3
im=Image.open('A.jpg').convert('RGB');im=im.resize((im.width*S,im.height*S),Image.LANCZOS);dr=ImageDraw.Draw(im)
A=np.linspace(-math.pi,math.pi,721)
for fr,col in [(0,(255,255,0)),(0.25,(0,255,255)),(0.5,(255,0,255)),(0.75,(0,255,255)),(1.0,(255,0,0))]:
    X=np.array([pt(a,0.3+fr*(d_out(a)-0.3),0) for a in A]);q=proj(cam,X)*S
    for i in range(len(q)-1):
        if in_stand(A[i]) and fr>0:continue
        dr.line([tuple(q[i]),tuple(q[i+1])],fill=col,width=1)
for deg in range(-180,180,15):
    a=math.radians(deg)
    X=np.array([pt(a,0,0),pt(a,d_out(a),0)]);q=proj(cam,X)*S
    dr.line([tuple(q[0]),tuple(q[1])],fill=(255,255,255),width=1);dr.text(tuple(q[1]+[3,0]),str(deg),fill=(255,255,0))
im.save('chk/ringover.png')
im.crop((600,350,2400,1350)).save('chk/ringover_c.png')
