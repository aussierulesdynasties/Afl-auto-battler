# python board2.py RENDER OVERLAY_OUT PARTS_OUT
# 1) full-res photo | render | 50% overlay   2) per-part board: every part's box from the matched camera, photo | render | overlay
import sys,json,numpy as np
from PIL import Image,ImageDraw,ImageFont
from cam import proj
p=np.array(json.load(open('cam.json'))['p'])
rn=Image.open(sys.argv[1]).convert('RGBA');W,H=rn.size;s=W/800
ph=Image.open('e86_l.jpg').convert('RGBA').resize((W,H),Image.LANCZOS)
try:f=ImageFont.truetype('arial.ttf',30);fs=ImageFont.truetype('arial.ttf',20)
except Exception:f=fs=None
bg=Image.new('RGBA',(W,H),(40,44,52,255));bg.alpha_composite(rn)
a=rn.copy();a.putalpha(rn.split()[3].point(lambda v:v//2));ov=ph.copy();ov.alpha_composite(a)
pad,top=20,60;B=Image.new('RGB',(W*3+pad*4,H+top+pad),(20,22,26));d=ImageDraw.Draw(B)
for i,(im,t) in enumerate(((ph,'Photo, 1986 (Footscray Historical Society), upscaled 2x'),(bg,'Model, matched camera, hand-made textures'),(ov,'Model at 50% over the photo'))):
    x=pad+i*(W+pad);B.paste(im.convert('RGB'),(x,top));d.text((x,14),t,fill=(235,235,235),font=f)
B.save(sys.argv[2])
M=json.load(open('model2.json'));tiles=[]
for name,pt in M.items():
    if 'turf' in name or not pt['v']:continue
    uv=proj(p,np.array(pt['v']))
    x0,y0=uv.min(0)-6;x1,y1=uv.max(0)+6
    x0,y0=max(0,x0),max(0,y0);x1,y1=min(800,x1),min(581,y1)
    if x1-x0<4 or y1-y0<4:continue
    k=min(220/(x1-x0),160/(y1-y0),8);box=tuple(int(v*s) for v in (x0,y0,x1,y1));w,h=int((x1-x0)*k),int((y1-y0)*k)
    tiles.append((name,[im.crop(box).resize((w,h),Image.LANCZOS) for im in (ph,bg,ov)],w,h))
cols=3;cw=3*230+40;rh=200;rows=(len(tiles)+cols-1)//cols
P=Image.new('RGB',(cols*cw,rows*rh),(20,22,26));d=ImageDraw.Draw(P)
for i,(name,ims,w,h) in enumerate(tiles):
    cx,cy=(i%cols)*cw+10,(i//cols)*rh
    d.text((cx,cy+4),name,fill=(235,235,235),font=fs)
    for j,im in enumerate(ims):P.paste(im.convert('RGB'),(cx+j*230,cy+32))
P.save(sys.argv[3]);print(len(tiles),'parts on the board')
