# Hand-made WACA textures (no photo pixels). python tex.py OUTDIR
# Each texture covers SIZE[name] metres square; build.py maps UVs in world metres.
import sys,os,random
from PIL import Image,ImageDraw,ImageFilter,ImageChops
out=sys.argv[1];os.makedirs(out,exist_ok=True);N=1024;random.seed(7)
def c255(t):
    if max(t)>1:return tuple(int(v) for v in t)
    return tuple(int(max(0,min(1,v))**(1/2.2)*255) for v in t)  # linear -> sRGB
def noise(img,amt):
    n=Image.effect_noise((N,N),amt).convert('RGB');return ImageChops.add(ImageChops.subtract(img,Image.new('RGB',(N,N),(int(amt),)*3)),n,1,0) if False else Image.blend(img,ImageChops.multiply(img,Image.merge('RGB',[n]*3).point(lambda v:200+v*55//255)),0.5)
def grain(img,amt=10):
    n=Image.effect_noise((N,N),amt).convert('L').point(lambda v:v-128+128)
    return Image.blend(img,ImageChops.overlay(img,Image.merge('RGB',[n]*3)),0.6)
SIZE={}
def save(name,img,size):img.save(os.path.join(out,name+'.png'));SIZE[name]=size
px=lambda m,size:int(round(m*N/size))
# brick: 230x76 mm, 10 mm mortar, stretcher bond. 4 m square
s=4.0;base=c255((143,44,16));img=Image.new('RGB',(N,N),c255((175,165,150)));d=ImageDraw.Draw(img)
bh,bw,mo=0.086,0.24,0.010
for r in range(int(s/bh)+1):
    y0=r*bh;off=(bw/2)*(r%2)
    for k in range(-1,int(s/bw)+2):
        x0=k*bw+off;j=random.uniform(-0.05,0.05)
        col=tuple(max(0,min(255,int(v*(1+j)))) for v in base)
        d.rectangle([px(x0,s),px(y0,s),px(x0+bw-mo,s)-1,px(y0+bh-mo,s)-1],fill=col)
save('brick',grain(img,14),s)
# off-white render with panel joints every 3 m. 6 m
def render(name,rgb,s=6.0,joint=3.0):
    img=Image.new('RGB',(N,N),c255(rgb));d=ImageDraw.Draw(img);jc=c255(tuple(v*0.8 for v in rgb))
    for k in range(int(s/joint)+1):
        d.line([(px(k*joint,s),0),(px(k*joint,s),N)],fill=jc,width=2);d.line([(0,px(k*joint,s)),(N,px(k*joint,s))],fill=jc,width=2)
    save(name,grain(img,8),s)
render('white',(233,236,248));render('concrete',(190,184,172));render('path',(196,188,170),6,6)
render('yellow',(252,210,74),6,6);render('blue',(60,90,160),6,6);render('aisle',(225,225,225),6,6)
# roof deck: trapezoidal ribs every 0.19 m (u), sheet laps every 6 m (v). 4 m
def deck(name,rgb,s=4.0,rib=0.19,hk=1.25,lk=0.7):
    img=Image.new('RGB',(N,N),c255(rgb));d=ImageDraw.Draw(img)
    hi=c255(tuple(min(255 if max(rgb)>1 else 1,v*hk) for v in rgb));lo=c255(tuple(v*lk for v in rgb))
    for k in range(int(s/rib)+1):
        x=px(k*rib,s);d.rectangle([x,0,x+3,N],fill=hi);d.rectangle([x+4,0,x+6,N],fill=lo)
    save(name,grain(img,6),s)
deck('roof',(232,232,238));deck('loft',(150,150,155))
# terrace: 0.8 m concrete steps, a row of red tip-up seats on each, 0.48 m seat pitch. 4 m
s=4.0;img=Image.new('RGB',(N,N),c255((190,184,172)));d=ImageDraw.Draw(img)
red=c255((196,113,75));red2=c255((150,80,52));sh=c255((120,115,108))
for r in range(int(s/0.8)+1):
    y=r*0.8;d.rectangle([0,px(y,s),N,px(y,s)+3],fill=sh)
    for k in range(int(s/0.48)+1):
        x=k*0.48;d.rectangle([px(x+0.03,s),px(y+0.12,s),px(x+0.45,s),px(y+0.55,s)],fill=red)
        d.rectangle([px(x+0.03,s),px(y+0.12,s),px(x+0.45,s),px(y+0.20,s)],fill=red2)
save('red',grain(img,8),s);save('terrace',grain(img,8),s)
# glass bands: 1.5 m mullions, transom at 1.1 m. 6 m
s=6.0;img=Image.new('RGB',(N,N),c255((29,28,40)));d=ImageDraw.Draw(img);m=c255((150,150,155))
for k in range(5):d.rectangle([px(k*1.5,s),0,px(k*1.5,s)+4,N],fill=m)
for z in (0,1.1,3,4.1):d.rectangle([0,px(z,s),N,px(z,s)+4],fill=m)
for nm in('glass','dark'):save(nm,grain(img,5),s)
# tent membrane: white fabric, seams every 1.2 m. 6 m
s=6.0;img=Image.new('RGB',(N,N),c255((238,236,232)));d=ImageDraw.Draw(img)
for k in range(6):d.line([(px(k*1.2,s),0),(px(k*1.2,s),N)],fill=c255((205,202,198)),width=3)
save('tent',grain(img,5),s)
# grass: mowing stripes 6 m wide. 24 m
s=24.0;img=Image.new('RGB',(N,N),c255((141,160,85)));d=ImageDraw.Draw(img)
for k in range(0,4,2):d.rectangle([px(k*6,s),0,px((k+1)*6,s)-1,N],fill=c255((128,150,76)))
save('grass',grain(img,12),s)
s=6.0;img=Image.new('RGB',(N,N),c255((0.42,0.40,0.33)));save('land',grain(img,20),s)
s=6.0;img=Image.new('RGB',(N,N),c255((0.03,0.03,0.04)));save('board',grain(img,4),s)
s=6.0;img=Image.new('RGB',(N,N),c255((0.02,0.30,0.12)));save('green',grain(img,8),s)
s=6.0;img=Image.new('RGB',(N,N),c255((88,88,92)));save('road',grain(img,14),s)
def seats(name,seat,conc=(150,146,140)):
    s=4.0;img=Image.new('RGB',(N,N),c255(conc));d=ImageDraw.Draw(img)
    a=c255(seat);b=c255(tuple(int(v*0.72) for v in seat));sh=c255(tuple(int(v*0.65) for v in conc))
    for r in range(int(s/0.8)+1):
        y=r*0.8;d.rectangle([0,px(y,s),N,px(y,s)+3],fill=sh)
        for k in range(int(s/0.48)+1):
            x=k*0.48;d.rectangle([px(x+0.03,s),px(y+0.12,s),px(x+0.45,s),px(y+0.55,s)],fill=a)
            d.rectangle([px(x+0.03,s),px(y+0.12,s),px(x+0.45,s),px(y+0.20,s)],fill=b)
    save(name,grain(img,8),s)
seats('greenseat',(40,140,85));seats('navyseat',(45,70,88),(120,118,114))
# EMU Club (colours sampled from p92): light orange brick, deck, fascia, band, ledge, ground floor, chairs, steel
def brick2(name,rgb,s=4.0):
    img=Image.new('RGB',(N,N),(200,190,175));d=ImageDraw.Draw(img)
    for r in range(int(s/bh)+1):
        y0=r*bh;off=(bw/2)*(r%2)
        for k in range(-1,int(s/bw)+2):
            x0=k*bw+off;j=random.uniform(-0.05,0.05);col=tuple(max(0,min(255,int(v*(1+j)))) for v in rgb)
            d.rectangle([px(x0,s),px(y0,s),px(x0+bw-mo,s)-1,px(y0+bh-mo,s)-1],fill=col)
    save(name,grain(img,12),s)
brick2('emubrick',(214,150,106))
deck('emuroof',(150,144,148),hk=1.08,lk=0.9)
render('emufascia',(172,150,142),6,6);render('emuband',(185,179,177),6,3);render('ledge',(185,150,111),6,6)
render('gf',(126,119,123),6,2);render('chair',(190,150,70),6,6);render('emutruss',(150,130,120),6,6)
# EMU CLUB sign board, 18.7 m x 2.1 m, drawn left to right as seen from the street
from PIL import ImageFont
SW,SH=2048,250;img=Image.new('RGB',(SW,SH),(40,40,48));d=ImageDraw.Draw(img);m2=lambda m:int(m/18.7*SW)
d.rectangle([m2(0)+6,14,m2(18.7)-6,SH-14],fill=(236,232,220))
f=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',150)
def ctext(t,x0,x1):
    bb=d.textbbox((0,0),t,font=f);w=bb[2]-bb[0];h=bb[3]-bb[1];d.text(((x0+x1-w)//2-bb[0],(SH-h)//2-bb[1]),t,font=f,fill=(22,18,16))
ctext('W.A.C.A.',m2(0),m2(18.7))  # ground's own name; no sponsors (director)
img.save(os.path.join(out,'emusign.png'));SIZE['emusign']=18.7
# scoreboard and billboards (layouts read off p92 u 887-1248), drawn by hand
render('crownred',(205,30,22),6,6);render('bbframe',(150,120,60),6,6)
def canvas(wm,hm,ppm,bg):
    im=Image.new('RGB',(int(wm*ppm),int(hm*ppm)),bg);return im,ImageDraw.Draw(im),(lambda x,y:(int(x*ppm),int(y*ppm)))
# face 15.2 x 6.3 m: black, white name bars (left), white/pink name panels (middle), yellow score panels (right)
im,d,q=canvas(15.2,6.3,128,(22,22,28))
for r in range(8):
    y=0.7+r*0.62
    d.rectangle([q(0.4,y),q(3.0,y+0.18)],fill=(200,200,200))
    if r<7:d.rectangle([q(5.1,y),q(7.1,y+0.42)],fill=(235,225,230) if r%2==0 else (225,120,140))
    else:d.rectangle([q(5.1,y),q(7.1,y+0.42)],fill=(245,200,50))
    d.rectangle([q(9.3,y),q(11.3,y+0.42)],fill=(245,200,50))
for x in (12.3,12.8,13.3):d.rectangle([q(x,5.75),q(x+0.25,5.95)],fill=(230,230,230))
im.save(os.path.join(out,'sbface.png'));SIZE['sbface']=15.2
# crown 16.7 x 2.6 m: red, yellow diagonal stripes at the left, yellow EMU EXPORT LAGER
im,d,q=canvas(16.7,2.6,128,(205,30,22))
for k in range(-2,8):x=k*0.75;d.polygon([q(x,2.6),q(x+0.4,2.6),q(x+0.4+2.2,0.4),q(x+2.2,0.4)],fill=(250,195,45))
d.rectangle([q(4.6,0),q(16.7,2.6)],fill=(205,30,22))
d.rectangle([q(0,0),q(16.7,0.28)],fill=(250,195,45));d.rectangle([q(0,2.45),q(16.7,2.6)],fill=(250,195,45))
f2=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',150)
bb=d.textbbox((0,0),'EMU EXPORT LAGER',font=f2);sx=(q(16.2,0)[0]-q(5.0,0)[0])/(bb[2]-bb[0])
tx=Image.new('RGBA',(bb[2]-bb[0]+4,bb[3]-bb[1]+4),(0,0,0,0));ImageDraw.Draw(tx).text((-bb[0]+2,-bb[1]+2),'EMU EXPORT LAGER',font=f2,fill=(250,205,60,255))
bb=d.textbbox((0,0),'WACA',font=f2);d.text(((q(5.0,0)[0]+q(16.2,0)[0]-(bb[2]-bb[0]))//2-bb[0],(q(0,2.6)[1]-(bb[3]-bb[1]))//2-bb[1]),'WACA',font=f2,fill=(250,205,60))
im.save(os.path.join(out,'sbcrown.png'));SIZE['sbcrown']=16.7
# billboard 1, 14.8 x 6.6 m (mostly behind a light tower): white, a blue O at the right
im,d,q=canvas(14.8,6.6,96,(238,236,230))
im.save(os.path.join(out,'bb1.png'));SIZE['bb1']=14.8
# billboard 2, 14.4 x 6.9 m: gold star at the left, GOLD STAR ACCOUNT, three text lines, red logo bar
im,d,q=canvas(14.4,6.9,96,(240,236,226));g=(185,150,60)
import math as _m
# sponsor art removed (director: no sponsors); plain board
im.save(os.path.join(out,'bb2.png'));SIZE['bb2']=14.4
brick2('hallbrick',(118,40,28));brick2('ebrick',(196,70,30))
deck('hallroofA',(174,191,214),hk=1.08,lk=0.9);deck('hallroofB',(226,236,248),hk=1.04,lk=0.92)
render('hallfascia',(91,79,103),6,6);render('hallwin',(60,85,130),1.5,0.75);render('croof',(198,167,135),6,6);render('droof',(224,85,22),6,6);render('eroof',(218,203,225),6,6)
# light-tower heads (11 x 17 m): back lattice, lamp face, side lattice. Drawn from the 1992 photo's head shapes.
def headtex():
    W,Hm,pp=11.0,17.0,60;w,h=int(W*pp),int(Hm*pp);M=lambda m:int(round(m*pp))
    WH=(244,246,250);GAP=(226,229,234);LB=(150,156,164)
    im=Image.new('RGB',(w,h),GAP);d=ImageDraw.Draw(im)
    for r in range(9):
        for c in range(5):
            cx,cy=M(1.1+c*2.2),M(0.95+r*1.9);R=M(0.45);d.ellipse([cx-R,cy-R,cx+R,cy+R],fill=LB)
    m=M(0.32);rows=[0,4.25,8.5,12.75,17.0]
    for y in rows:d.rectangle([0,M(y)-m,w,M(y)+m],fill=WH)
    for x in (0,5.5,11.0):d.rectangle([M(x)-m,0,M(x)+m,h],fill=WH)
    for i in range(4):
        y0,y1=M(rows[i]),M(rows[i+1])
        d.line([(M(0),y1),(M(5.5),y0)],fill=WH,width=m);d.line([(M(5.5),y0),(M(11),y1)],fill=WH,width=m)
    save('headb',grain(im,6),W)
    im=Image.new('RGB',(w,h),WH);d=ImageDraw.Draw(im)
    for r in range(9):
        for c in range(5):
            x0,y0=M(0.25+c*2.15),M(0.2+r*1.88);d.rectangle([x0,y0,x0+M(2.0),y0+M(1.7)],fill=(232,235,240))
            cx,cy=x0+M(1.0),y0+M(0.85);R=M(0.72);d.ellipse([cx-R,cy-R,cx+R,cy+R],fill=(92,98,108));R=M(0.55);d.ellipse([cx-R,cy-R,cx+R,cy+R],fill=(168,176,186))
    save('headf',grain(im,6),W)
    s=2.0;im=Image.new('RGB',(N,N),c255(GAP));d=ImageDraw.Draw(im);k=px(0.3,s)
    for v in (0,s):d.rectangle([0,px(v,s)-k,N,px(v,s)+k],fill=WH);d.rectangle([px(v,s)-k,0,px(v,s)+k,N],fill=WH)
    d.line([(0,N),(N,0)],fill=WH,width=k)
    save('headside',grain(im,6),s)
headtex()
import json;json.dump(SIZE,open(os.path.join(out,'size.json'),'w'))
print(SIZE)
