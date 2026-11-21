# hand-made JSS textures (no photo pixels). 1 tile = 4 m unless noted.
from PIL import Image,ImageDraw,ImageFilter
import random,sys
out=sys.argv[1] if len(sys.argv)>1 else '.'
random.seed(7);N=1024
def ribs(base,crest,shade,name,lap=True):
    im=Image.new('RGB',(N,N),base);d=ImageDraw.Draw(im)
    for x in range(N):
        m=x%64
        c=crest if m<6 else shade if m<10 else tuple(b+((x*7)%3) for b in base)
        d.line([(x,0),(x,N)],fill=c)
    if lap:
        for y in(0,512):d.rectangle([0,y,N,y+3],fill=shade)
    im.filter(ImageFilter.GaussianBlur(0.6)).save(out+'/'+name)
ribs((190,196,200),(212,217,220),(160,166,171),'jss_top.png')    # roof top: silver-white ribbed sheet (GE 3D sunlit roof 170-200)
ribs((222,224,225),(236,238,239),(196,199,201),'jss_soffit.png')  # roof underside: white ribbed liner
# skylight triangles: white translucent sheet with glazing bars every 1 m
im=Image.new('RGB',(N,N),(232,236,238));d=ImageDraw.Draw(im)
for x in range(0,N,256):d.rectangle([x,0,x+6,N],fill=(205,210,213))
for x in range(N):
    if x%32<3:d.line([(x,0),(x,N)],fill=(222,226,229))
im.save(out+'/jss_sky.png')
# white fin band, 4 m wide x 8 m tall tile: vertical folded fins 0.5 m, perforated screen panels in the lower half
W,H=512,1024;im=Image.new('RGB',(W,H),(226,228,229));d=ImageDraw.Draw(im)
for x in range(0,W,64):
    d.rectangle([x,0,x+20,H],fill=(238,240,241));d.rectangle([x+44,0,x+63,H],fill=(206,209,211))
for k,x in enumerate(range(0,W,128)):
    if k%2==0:
        for yy in range(int(H*0.42),int(H*0.86),10):
            for xx in range(x+8,x+120,10):d.ellipse([xx,yy,xx+4,yy+4],fill=(150,154,157))
im.save(out+'/jss_fins.png')
# brick base, 4 m x 4 m: dark red-brown stretcher bond, 0.25 x 0.086 m courses
im=Image.new('RGB',(N,N),(70,56,52));d=ImageDraw.Draw(im);ch=22;bw=64
for r_,y in enumerate(range(0,N,ch)):
    off=(bw//2) if r_%2 else 0
    for x in range(-bw,N,bw):
        c=random.choice([(98,62,54),(90,58,51),(104,68,58),(84,55,50)])
        d.rectangle([x+off+2,y+2,x+off+bw-2,y+ch-2],fill=c)
im.save(out+'/jss_brick.png')
# glazing strip, 4 m x 4 m: dark blue-grey glass, mullions every 1.33 m, transom
im=Image.new('RGB',(N,N),(52,62,72));d=ImageDraw.Draw(im)
for y in range(N):d.line([(0,y),(N,y)],fill=(52+y*14//N,62+y*14//N,72+y*12//N))
for x in range(0,N,341):d.rectangle([x,0,x+10,N],fill=(38,40,43))
d.rectangle([0,N//2-5,N,N//2+5],fill=(38,40,43));im.save(out+'/jss_glass.png')
# dark grey cladding, 4 m x 4 m: vertical standing seams every 0.4 m
im=Image.new('RGB',(N,N),(72,77,82));d=ImageDraw.Draw(im)
for x in range(0,N,102):d.rectangle([x,0,x+4,N],fill=(58,62,66));d.rectangle([x+5,0,x+7,N],fill=(90,95,99))
for y in(0,N//2):d.line([(0,y),(N,y)],fill=(62,66,70),width=3)
im.save(out+'/jss_clad.png')
print('ok')
