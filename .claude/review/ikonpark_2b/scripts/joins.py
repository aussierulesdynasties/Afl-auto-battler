import json,sys,numpy as np
from PIL import Image,ImageDraw
exec(open('w/cam.py').read())
geom,cam,photo,rend,out=sys.argv[1:6]
G=json.load(open(geom));k=mk(json.load(open(cam))['q'])
r=Image.open(rend).convert('RGBA');W,H=r.size
bg=Image.new('RGBA',r.size,(40,40,40,255));bg.alpha_composite(r)
p=Image.open(photo).convert('RGBA').resize((W,H),Image.LANCZOS)
ov=Image.blend(p,Image.alpha_composite(p,r),0.5)
pts=[]
for n in G['stands']:
  s=G[n]
  for e in (0,-1):pts.append((n+(' start' if e==0 else ' end'),np.mean([s['front'][e],s['back'][e]],0)))
for n in G.get('bowlblocks',[]):pts.append((n,np.mean(G['blocks'][n]['poly'],0)))
tiles=[]
for name,X in pts:
  u=k.proj(np.array([X]))[0]
  if not(0<u[0]<W and 0<u[1]<H):continue
  b=(int(u[0]-130),int(u[1]-100),int(u[0]+130),int(u[1]+100))
  row=Image.new('RGB',(3*520+20,420),(20,20,20))
  for j,im in enumerate((bg,p,ov)):row.paste(im.crop(b).resize((520,400),Image.LANCZOS).convert('RGB'),(j*530,20))
  ImageDraw.Draw(row).text((5,3),name+'  render | photo | overlay',fill='white')
  tiles.append(row)
B=Image.new('RGB',(tiles[0].width,420*len(tiles)));[B.paste(t,(0,i*420)) for i,t in enumerate(tiles)];B.save(out);print(out,len(tiles))
