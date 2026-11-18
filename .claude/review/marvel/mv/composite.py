# atlas texels -> photo colour: own view if the camera sees the point, else its 180 deg twin's view, else a flat colour
import numpy as np,cv2,sys
MV='.';PH=cv2.imread('mu_full.png');PR=cv2.imread('mu_roof.png')
EXC=np.zeros(PH.shape[:2],np.uint8)   # photo pixels that show things we do not model (city buildings in front)
for poly in ([(1565,600),(1600,560),(1760,555),(1900,580),(1920,600),(1920,1080),(1600,1080),(1570,950)],
             [(0,690),(150,700),(210,800),(210,980),(0,1000)]):
    cv2.fillPoly(EXC,[np.int32(np.array(poly)*2)],1)
def samp(img,uv):
    x=(uv[...,0]*3840-0.5).astype(np.float32);y=(uv[...,1]*2160-0.5).astype(np.float32)
    c=cv2.remap(img,x,y,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    e=cv2.remap(EXC,x,y,cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT,borderValue=1)
    inside=(x>=0)&(y>=0)&(x<3839)&(y<2159)&(uv[...,2]>0.5)&(e==0);return c,inside
for g in ('front','sym','roof'):
    d=np.load('bake_%s.npz'%g);img=PR if g=='roof' else PH
    out=None;have=None
    for k in (('0',) if g=='front' else ('0','1')):
        uv=d['uv'+k][::-1];vis=d['vis'+k][::-1,:,0]   # Blender pixel rows start at the bottom
        c,ins=samp(img,uv);ok=ins&(vis>1e-3*vis.max())
        if out is None:out=np.zeros_like(c);have=np.zeros(ok.shape,bool)
        new=ok&~have;out[new]=c[new];have|=ok
        print(g,k,'texels seen',int(ok.sum()))
    flat=np.median(out[have],0) if have.any() else np.array([60,60,60]);out[~have]=flat
    cv2.imwrite('tex_%s.png'%g,out);print(g,'fallback flat',flat,'cover',have.mean().round(3))
