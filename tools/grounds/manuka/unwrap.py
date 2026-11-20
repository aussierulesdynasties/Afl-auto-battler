# unwrap a tier of the photo into (angle, profile) so aisles become vertical stripes; label every 2 deg
import numpy as np, math, io, contextlib, sys
with contextlib.redirect_stdout(io.StringIO()):
    import model as M
import cam
from PIL import Image, ImageDraw
ph=np.array(Image.open('photo.png').convert('RGB'))
def unwrap(name,t0,t1,p0,p1,dt=0.1,nz=40):
    A=np.arange(t0,t1,dt);out=np.zeros((nz,len(A),3),np.uint8)
    for i,t in enumerate(A):
        a=math.radians(t)
        pts=[M.P(a,p0[0]+f*(p1[0]-p0[0]),p0[1]+f*(p1[1]-p0[1])) for f in np.linspace(1,0,nz)]
        uv=cam.proj(pts)
        for j,(u,v) in enumerate(uv):
            if 0<=u<1919 and 0<=v<1279:out[j,i]=ph[int(v),int(u)]
    im=Image.fromarray(out[:,::-1]).resize((len(A)*4,nz*4),Image.NEAREST)   # angle decreasing left->right (as seen)
    big=Image.new('RGB',(im.width,im.height+16),(0,0,0));big.paste(im,(0,16));d=ImageDraw.Draw(big)
    for t in range(int(math.ceil(t0)),int(t1)+1):
        x=(t1-t)/dt*4
        d.line([x,8,x,16],fill=(255,255,0));
        if t%2==0:d.text((x+1,0),str(t),fill=(255,255,255))
    big.save(f'z/uw_{name}.png');return big.size
TIERS={'n_lower':(50,100,(-1.5,1.1),(4.5,2.3)),'n_lower2':(100,152,(-1.5,1.1),(4.5,2.3)),
       'n_upper':(57,105,(7,3.3),(16,8.0)),'n_upper2':(105,152,(7,3.3),(16,8.0)),
       'w_lower':(190,237,(0.3,1.1),(9,3.0)),'w_upper':(190,237,(11,3.6),(20,8.0)),'b_seats':(156,192,(0.3,1.1),(13,6.5)),'p_seats':(268,298,(0.3,1.1),(9,1.6)),'se_seats':(312,346,(6,0.3),(12,5.0))}
for k in sys.argv[1:]:print(k,unwrap(k,*TIERS[k]))
