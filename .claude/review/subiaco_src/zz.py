import sys
from PIL import Image,ImageDraw
P=Image.open('refs/c/17.jpg').convert('RGB')
R=Image.open(sys.argv[1]).convert('RGBA');bg=Image.new('RGBA',R.size,(0,0,0,255));bg.alpha_composite(R);R=bg.convert('RGB')
x0,y0,x1,y1,k=map(int,sys.argv[2:7]);tag=sys.argv[7]
for n,I in (('p',P),('r',R)):
  J=I.crop((x0,y0,x1,y1)).resize(((x1-x0)*k,(y1-y0)*k),Image.LANCZOS);d=ImageDraw.Draw(J)
  for x in range(x0-x0%10+10,x1,10):d.line([((x-x0)*k,0),((x-x0)*k,8)],fill=(255,0,0));d.text(((x-x0)*k+2,10),str(x),fill=(255,0,0))
  for y in range(y0-y0%10+10,y1,10):d.line([(0,(y-y0)*k),(8,(y-y0)*k)],fill=(255,0,0));d.text((10,(y-y0)*k-5),str(y),fill=(255,0,0))
  J.save('%s_%s.png'%(tag,n))
