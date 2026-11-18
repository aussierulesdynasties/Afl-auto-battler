"""Put a club's ghost-mannequin photos in the cut's frame (2000x2000), read off each photo:
its armpit row (the bottom of the armhole, read by eye on a pixel grid) sits on body y 1.37, and its
chest width there matches the body's own width at the armpit (905 px = 2 x 0.196 m at 2310 px a
metre). The photo's shoulders and hem then fall where the photo puts them. If the hem would run off
the frame, the whole club moves up (frame_CODE.txt = the photo row of body y 1.62, normally 189).
python norm2.py CODE front_armpit_row back_armpit_row [samecam]
samecam: both photos come from one camera (same neck-top row, same height): the back keeps the
front's vertical scale and position, and only its width is fitted to the chest."""
import sys,glob,os,numpy as np
from PIL import Image
exec(open('C:/kt/guernsey3d_work/measure.py').read().split('for c in sys.argv')[0])
c=sys.argv[1]; A={'front':int(sys.argv[2]),'back':int(sys.argv[3])}
CHEST_PX=905.0; S_PX=2310.0
plan={}
for side in ('front','back'):
    fn=glob.glob(f'ref_raw/{c}_{side}.*')[0]; m=cloth(fn)
    rows=np.where(m.any(1))[0]; top,bot=rows.min(),rows.max(); a=A[side]
    w=np.median([np.ptp(np.nonzero(m[r])[0]) for r in range(a,a+8)])
    cxa=np.median([(lambda z:(z.min()+z.max())/2)(np.nonzero(m[r])[0]) for r in range(a,a+8)])
    s=CHEST_PX/w; plan[side]=(fn,a,s,cxa,top,bot)
SAME=len(sys.argv)>4 and sys.argv[4]=='samecam'
plan={k:v[:6]+(v[2],v[1]) for k,v in plan.items()}
if SAME: plan['back']=plan['back'][:6]+(plan['front'][2],plan['front'][1])
if os.environ.get('FIT'):
    for k,v in plan.items():
        top_row=189.0+(1.62-1.37)*S_PX-(v[7]-v[4])*v[6]
        if top_row<5: plan[k]=v[:6]+((189.0+(1.62-1.37)*S_PX-5)/(v[7]-v[4]),v[7]); print(k,'squeezed to %.3f of the chest scale'%(plan[k][6]/v[2]))
over=max(189+(1.62-1.37)*S_PX+(p[5]-p[7])*p[6]-1985 for p in plan.values())
Y0=189.0-max(0.0,over)
# FIT=1: a photo longer than the frame (GCS: 0.89 m top to hem at the chest's scale) is squeezed top to bottom only as
# much as it takes for the whole garment to sit inside the frame (rows 5-1985); its width stays fitted to the chest.
xf={}
for side,(fn,a,s,cxa,top,bot,sy,ay) in plan.items():
    arow=Y0+(1.62-1.37)*S_PX
    tx=1000-cxa*s; ty=arow-ay*sy
    im=Image.open(fn).convert('RGBA'); bg=Image.new('RGBA',im.size,(255,255,255,255))
    im=Image.alpha_composite(bg,im).convert('RGB')   # a cut-out's hidden background (WCE's grey box) goes white
    out=im.transform((2000,2000),Image.AFFINE,(1/s,0,-tx/s,0,1/sy,-ty/sy),resample=Image.BICUBIC,fillcolor=(255,255,255))
    out.save(f'ref/{c}_{side}.png')
    xf[side]=(s,sy,tx,ty)   # photo px -> frame px: x*s+tx, y*sy+ty (club fixes that map photo features use it)
    print(c,side,'armpit',a,'chest %.0f'%(CHEST_PX/s),'scale %.3f'%s,'top -> %.0f'%(ty+top*sy),'hem -> %.0f'%(ty+bot*sy),
          'hem y %.3f m'%(1.62-(ty+bot*sy-Y0)/S_PX))
if Y0!=189.0: open(f'frame_{c}.txt','w').write('%.1f'%Y0)
elif os.path.exists(f'frame_{c}.txt'): os.remove(f'frame_{c}.txt')
import json; json.dump(xf,open(f'norm_{c}.json','w'))
print(c,'Y0',Y0)
