import sys;from PIL import Image
x0,y0,x1,y1=map(int,sys.argv[1].split(','));k=600/(x1-x0)
a=Image.open('refs/scg.jpg').convert('RGB').crop((x0,y0,x1,y1));b=Image.open('out/r0.png').convert('RGB').crop((x0,y0,x1,y1))
sz=(600,int((y1-y0)*k));c=Image.new('RGB',(1200,sz[1]));c.paste(a.resize(sz,Image.LANCZOS),(0,0));c.paste(b.resize(sz,Image.LANCZOS),(600,0));c.save(sys.argv[2])
