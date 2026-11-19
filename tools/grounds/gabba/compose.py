import numpy as np,json,sys
from PIL import Image,ImageFilter,ImageChops,ImageDraw
exec(open('cam.py').read())
import os;P=np.array(json.load(open(os.environ.get('CAMFIT','camfit8.json')))['p']);k=P[31];fo=P[6];cx,cy=P[7],P[8]
def distort(img):
    a=np.asarray(img).astype(np.float32);H,W=a.shape[:2]
    u,v=np.meshgrid(np.arange(W),np.arange(H));A=(u-cx)/fo;B=-(v-cy)/fo;x,y=A.copy(),B.copy()
    for _ in range(15):g=1+k*(x*x+y*y);x,y=A/g,B/g
    su=cx+fo*x;sv=cy-fo*y
    from scipy.ndimage import map_coordinates
    out=np.stack([map_coordinates(a[...,c],[sv,su],order=1,mode='constant') for c in range(a.shape[2])],-1)
    return Image.fromarray(out.clip(0,255).astype(np.uint8))
mode=sys.argv[1]
if mode=='cam':
    M=R(*P[3:6]);json.dump({'C':P[:3].tolist(),'M':M.tolist(),'f':fo,'cx':cx,'cy':cy},open('camB.json','w'))
else:
    rend,mask,out=sys.argv[2:5]
    from scipy.ndimage import map_coordinates
    ph=Image.open('refs/g49.jpg').convert('RGB');r=distort(Image.open(rend).convert('RGB'));m=distort(Image.open(mask).convert('RGB'))
    r.save(out.replace('.png','_model.png'))
    ma=np.asarray(m).astype(int);e=(np.abs(np.diff(ma,axis=0,prepend=ma[:1])).sum(-1)>60)|(np.abs(np.diff(ma,axis=1,prepend=ma[:,:1])).sum(-1)>60)
    from scipy.ndimage import binary_dilation;e=binary_dilation(e)
    ed=Image.fromarray((e*255).astype(np.uint8))
    ov=Image.blend(ph,r,0.5);ov.paste((255,0,255),mask=ed)
    ov.save(out.replace('.png','_ov.png'))
    phe=ph.copy();phe.paste((255,0,255),mask=ed);phe.save(out.replace('.png','_edges.png'))
