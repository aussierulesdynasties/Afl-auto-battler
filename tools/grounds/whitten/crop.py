# python crop.py RENDER OUT x0 y0 x1 y1 [k]: photo crop | render-only crop | render over photo, regions in photo px (800x581)
import sys;from PIL import Image,ImageDraw
r=Image.open(sys.argv[1]).convert('RGBA');x0,y0,x1,y1=map(int,sys.argv[3:7]);k=float(sys.argv[7]) if len(sys.argv)>7 else 4
s=r.width/800;ph=Image.open('e86_l.jpg').convert('RGBA').resize(r.size,Image.LANCZOS)
box=(int(x0*s),int(y0*s),int(x1*s),int(y1*s));W=int((x1-x0)*k);H=int((y1-y0)*k)
a=ph.crop(box).resize((W,H),Image.LANCZOS)
grey=Image.new('RGBA',r.size,(255,0,255,255));grey.alpha_composite(r);b=grey.crop(box).resize((W,H),Image.LANCZOS)
c=ph.copy();c.alpha_composite(r);c=c.crop(box).resize((W,H),Image.LANCZOS)
o=Image.new('RGB',(W*3+20,H),'white')
for i,im in enumerate((a,b,c)):o.paste(im.convert('RGB'),(i*(W+10),0))
o.save(sys.argv[2])
