# project prims.json onto the photo: wireframe overlay
import json,sys,numpy as np,math
from PIL import Image,ImageDraw
from cam import load,proj
import model
p=load();im=Image.open('refs/ref.jpg').convert('RGB');d=ImageDraw.Draw(im)
C={'roof_white':(255,0,255),'roof_blue':(255,0,0),'tree':(0,255,0),'hoard':(255,128,0),'steel':(0,255,255),'lamps':(255,255,0)}
def poly(pts,c,close=True):
    q=proj(p,np.array(pts));L=[tuple(x) for x in q]+([tuple(q[0])] if close else []);d.line(L,fill=c,width=1)
def lerp2(a,b):return [(a[0]+b[0])/2,(a[1]+b[1])/2]
def facing(b):
    a=math.atan2(-b[1],-b[0]);return np.array([math.cos(a),math.sin(a)]),np.array([-math.sin(a),math.cos(a)])
for pr in model.prims:
    c=C.get(pr['mat'],(255,128,0));k=pr['kind']
    if k=='slab':poly(pr['pts'],c)
    elif k in('pole','lattice'):
        b=np.array(pr['base']);f,s=facing(b)
        for sg in(-1,1):poly([list(b+sg*s*pr['r0'])+[0],list(b+sg*s*pr['r1'])+[pr['z1']]],c,False)
    elif k=='head':
        b=np.array(pr['base']);f,s=facing(b);w=pr['w']/2
        poly([list(b-s*w)+[pr['z0']],list(b+s*w)+[pr['z0']],list(b+s*w)+[pr['z1']],list(b-s*w)+[pr['z1']]],c)
    elif k=='prism':
        fp=pr['fp'];z0=pr['z0'];zt=pr['ztop'] if isinstance(pr['ztop'],list) else [pr['ztop']]*len(fp)
        poly([q+[z0] for q in fp],c);poly([q+[z] for q,z in zip(fp,zt)],c)
        for q,z in zip(fp,zt):poly([q+[z0],q+[z]],c,False)
    elif k=='tree':
        cx,cy=pr['xy'];r=pr['r'];h=pr['h']
        poly([[cx+r*math.cos(t),cy+r*math.sin(t),h-pr['cd']/2] for t in np.linspace(0,2*math.pi,24)],c)
    elif k=='fence':
        pts=pr['pts']+([] if pr.get('open') else [pr['pts'][0]])
        poly([q+[pr['h']] for q in pts],c,False);poly([q+[0] for q in pts],c,False)
    elif k=='board':
        a,b=pr['a'],pr['b'];poly([a+[pr['z0']],b+[pr['z0']],b+[pr['z1']],a+[pr['z1']]],c)
    elif k=='gable':
        fp=pr['fp'];poly([q+[pr['eave']] for q in fp],c)
        m1=lerp2(fp[0],fp[3]);m2=lerp2(fp[1],fp[2]);poly([m1+[pr['ridge']],m2+[pr['ridge']]],c,False)
    elif k=='poly':poly(pr['pts'],c,pr.get('close',True))
im.save(sys.argv[1] if len(sys.argv)>1 else 'wire.png')
