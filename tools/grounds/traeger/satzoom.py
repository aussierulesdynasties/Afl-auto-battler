import json,sys
from PIL import Image,ImageDraw
J=json.load(open('sat/sat.json'));im0=Image.open('sat/sat.png')
ox=(J['cx']-J['x0'])*256;oy=(J['cy']-J['y0'])*256;m=J['mpp']
x0,y0,x1,y1,k=map(float,sys.argv[2:7])
box=(ox+x0/m,oy-y1/m,ox+x1/m,oy-y0/m)
im=im0.crop(tuple(int(b) for b in box));s=k
im=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS);d=ImageDraw.Draw(im)
bx,by=int(box[0]),int(box[1])
f=lambda x,y:((ox+x/m-bx)*s,(oy-y/m-by)*s)
for r in range(-300,301,5):
    c=(255,0,0) if r%25==0 else (255,170,170)
    if x0<=r<=x1:d.line([f(r,y0),f(r,y1)],fill=c);d.text((f(r,y1)[0]+2,2),str(r),fill=(255,255,0)) if r%25==0 else None
    if y0<=r<=y1:d.line([f(x0,r),f(x1,r)],fill=c);d.text((2,f(x0,r)[1]+2),str(r),fill=(0,255,255)) if r%25==0 else None
im.save(sys.argv[1])
