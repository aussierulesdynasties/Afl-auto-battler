# Textures for the GMHBA exterior: procedural surfaces and hand-drawn signs (signs.py); the photo is reference only
import random,json,math,numpy as np
from PIL import Image,ImageDraw,ImageFilter
from meas import PC,rpitch,rout
random.seed(4);O='tex/'
from signs import cats,gmhba,band,screen
def noise(im,a):
    arr=np.array(im).astype(int);arr+=np.random.RandomState(1).randint(-a,a+1,arr.shape[:2])[...,None];return Image.fromarray(np.clip(arr,0,255).astype('uint8'))
# turf: mown stripes
im=Image.new('RGB',(1024,1024));d=ImageDraw.Draw(im)
for i in range(16):d.rectangle([i*64,0,i*64+64,1024],fill=(60,70,32) if i%2 else (72,82,38))   # p1 pitch averages (71,81,38) in sun
noise(im,6).save(O+'turf.png')
# seats: white seats, navy rows (Reg Hickey / near side); dark navy bowl with white speckle (Selwood, crowd)
for nm,base,spk,frac in(('seats',(226,230,236),(30,42,78),0.35),('seats_dark',(28,34,58),(214,218,226),0.30)):
    im=Image.new('RGB',(256,256),base);px=im.load()
    for y in range(256):
        for x in range(256):
            if random.random()<frac:px[x,y]=spk
    d=ImageDraw.Draw(im)
    for y in range(0,256,16):d.line([(0,y),(256,y)],fill=(70,74,84),width=3)
    im.save(O+nm+'.png')
# roof sheet: white metal with seams, underside light grey
for nm,c,s in(('roof',(214,218,222),(188,192,198)),('under',(176,180,186),(150,154,160)),('roofdark',(70,72,76),(58,60,64)),('wall',(196,196,192),(176,176,172)),('fascia',(236,238,240),(220,222,226)),('tower',(238,240,242),(226,228,232))):
    im=Image.new('RGB',(256,256),c);d=ImageDraw.Draw(im)
    for x in range(0,256,32):d.line([(x,0),(x,256)],fill=s,width=2)
    noise(im,3).save(O+nm+'.png')
# solar panels (Joel Selwood Stand roof): dark cells, pale frames
im=Image.new('RGB',(256,256),(40,48,66));d=ImageDraw.Draw(im)
for x in range(0,256,32):d.line([(x,0),(x,256)],fill=(150,156,166),width=3)
for y in range(0,256,64):d.line([(0,y),(256,y)],fill=(150,156,166),width=3)
noise(im,4).save(O+'solar.png')
# glass: dark glazing with mullions
im=Image.new('RGB',(256,256),(46,56,70));d=ImageDraw.Draw(im)
for x in range(0,256,32):d.line([(x,0),(x,256)],fill=(120,126,134),width=3)
d.line([(0,128),(256,128)],fill=(120,126,134),width=3);noise(im,3).save(O+'glass.png')
# facade layout along the outline: (name, a0, a1) in degrees, unwrapped 100..298 for the west side
L={}
def arc(a0,a1):
    s=0;a=a0
    while a<a1:r=rout(math.radians(a));s+=r*math.radians(0.5);a+=0.5
    return s
# Premiership Stand: beige ribbed block 169.2..192.6, 23.6 m, blue band and glazing below 5.8 m, Cats logo, name sign
a0,a1=169.2,192.6;Lm=arc(a0,a1);H=24.0;S=20;W=int(Lm*S);Hh=int(H*S)
im=Image.new('RGB',(W,Hh),(224,220,204));d=ImageDraw.Draw(im)
for x in range(0,W,int(1.2*S)):d.line([(x,0),(x,Hh)],fill=(206,202,186),width=2)
yb=Hh-int(5.8*S);d.rectangle([0,yb,W,yb+int(0.8*S)],fill=(36,62,120));d.rectangle([0,yb+int(0.8*S),W,Hh],fill=(70,74,80))
for x in range(0,W,int(3*S)):d.rectangle([x+6,yb+int(1.6*S),x+int(3*S)-6,Hh-int(0.6*S)],fill=(44,50,60))
def at(a,z):return int(arc(a0,a)*S),int((H-z)*S)
# director 2026-11-18: "C: no lettering" - every sign a blank panel
# director 2026-11-19: the ground's own signs go back on, copied from p1 (crest a 174.59-178.62, z 7.88-16.09, measured on
# the p1 grid against the band's known a 183.6; band lettering PREMIERSHIP STAND)
cx0,cy0=at(174.273,16.38);cx1,cy1=at(179.271,6.504);cr=cats(cx1-cx0,cy1-cy0).convert('RGBA');im=im.convert('RGBA');im.alpha_composite(cr,(cx0,cy0));im=im.convert('RGB');d=ImageDraw.Draw(im)
x0,yt=at(-176.4+360,5.2);x1,_=at(-167.5+360,5.2);im.paste(band(x1-x0,int(0.9*S)),(x0,yt))   # stand-name band
noise(im,3).save(O+'beige.png');L['beige']=(a0,a1,H)
# GMHBA block on the outline 154..169.2 (behind the wedge): grey cladding box to 22.6 m, ground-floor glazing below 5 m
a0,a1=154.0,169.2;Lm=arc(a0,a1);H=22.6;W=int(Lm*S);Hh=int(H*S)
im=Image.new('RGB',(W,Hh),(139,142,150));d=ImageDraw.Draw(im)   # p1 box front reads (99,100,106); render was 74 at (104,106,112) -> x1.34
for x in range(0,W,int(1.5*S)):d.line([(x,0),(x,Hh)],fill=(118,121,129),width=2)
for z in(8.0,12.0,16.0,20.0):d.line([(0,int((H-z)*S)),(W,int((H-z)*S))],fill=(123,126,134),width=2)
d.rectangle([0,Hh-int(5.0*S),W,Hh],fill=(44,54,66))
for x in range(0,W,int(2*S)):d.line([(x,Hh-int(5.0*S)),(x,Hh)],fill=(110,116,124),width=2)
noise(im,3).save(O+'wedge.png');L['wedge']=(a0,a1,H)
# GMHBA wedge front (vertical plane A->B, s 0..L along it, z 0..16.5): dark cladding, sign where p1 shows it
WJ=json.load(open('wedge.json'));WL=WJ['L'];WH=16.5;W=int(WL*S);Hh=int(WH*S)
im=Image.new('RGB',(W,Hh),(54,54,60));d=ImageDraw.Draw(im)
for x in range(0,W,int(1.25*S)):d.line([(x,0),(x,Hh)],fill=(47,47,53),width=2)
for z in(6.0,9.5,13.0):d.line([(0,int((WH-z)*S)),(W,int((WH-z)*S))],fill=(54,54,60),width=2)
sg=WJ['sign'];s0=min(q[0] for q in sg);s1=max(q[0] for q in sg);z0=min(q[1] for q in sg);z1=max(q[1] for q in sg)
ang=math.degrees(math.atan2(sg[1][1]-sg[0][1],sg[1][0]-sg[0][0]))
lg=gmhba(int((s1-s0)*S),int((sg[0][1]-sg[3][1]+sg[1][1]-sg[2][1])/2*S)).rotate(ang,expand=True,resample=Image.BICUBIC)
pass   # GMHBA STADIUM letters on the cladding: left out, cladding plain
noise(im,3).save(O+'wedgef.png')
# slats: white and blue vertical slats 7.0..24.2 m (photo), blue band 5.5..7.0, dark open concourse below
a0,a1=193.9,209.0;Lm=arc(a0,a1);H=24.2;W=int(Lm*S);Hh=int(H*S)
im=Image.new('RGB',(W,Hh),(60,66,78));d=ImageDraw.Draw(im);ys=int((H-7.0)*S)
for x in range(0,W,10):d.rectangle([x,0,x+5,ys],fill=(232,236,240) if (x//10)%3 else (64,92,150))
for x in range(int(2*S),W,int(6*S)):d.rectangle([x,int(6*S),x+int(0.6*S),int(9*S)],fill=(30,34,44))
d.rectangle([0,ys,W,int((H-5.5)*S)],fill=(40,70,130))
noise(im,3).save(O+'slats.png');L['slats']=(a0,a1,H)
# Players Stand: white curved balcony bands, dark open concourses, blue columns
im=Image.new('RGB',(512,440),(70,76,88));d=ImageDraw.Draw(im)
for yt,h in((0,60),(150,70),(300,60)):d.rectangle([0,yt,512,yt+h],fill=(236,238,240))
for x in range(40,512,128):d.rectangle([x,0,x+10,440],fill=(46,86,150))
noise(im,3).save(O+'players.png')
# Reg Hickey south end wall at a=298 (p1 x 847-975, measured on that plane in d,z metres): glass stair bay d 3.1-14.5
# z 5.8-15.6, white block d 14.5-20.4 to 16 m, white floors with dark glazing bands d 20.4-46.7 to 14.5 m
S2=20;W,Hh=int(47*S2),int(17*S2);im=Image.new('RGB',(W,Hh),(178,182,188));d=ImageDraw.Draw(im)
def R_(d0,d1,z0,z1,c):d.rectangle([int(d0*S2),int((17-z1)*S2),int(d1*S2),int((17-z0)*S2)],fill=c)
R_(3.1,14.5,0,15.6,(236,238,238));R_(3.4,14.2,5.8,15.0,(72,84,98))   # p1 zoom: grey-blue glass, ~17 white mullions
for k in range(17):x=3.4+k*(14.2-3.4)/16;R_(x-0.17,x+0.17,5.8,15.0,(226,230,232))
for z in(8.9,12.0):R_(3.4,14.2,z-0.15,z+0.15,(226,230,232))
R_(14.5,20.4,0,16.0,(234,236,236));R_(20.4,46.7,0,14.5,(232,234,234))
for z0,z1 in((12.4,13.6),(9.0,10.2),(6.5,7.7),(4.3,5.5)):
    R_(20.4,46.7,z0,z1,(38,42,50))
    for x in np.arange(21.0,46.7,1.6):R_(x,x+0.12,z0,z1,(150,156,164))
noise(im,3).save(O+'rhend.png')
# GMHBA rooftop (p1 zoom x 262-395, y 425-452): cream precast parapet with joints, beige deck, plant enclosure
im=Image.new('RGB',(256,256),(222,219,212));d=ImageDraw.Draw(im)
for x in range(0,256,64):d.line([(x,0),(x,256)],fill=(196,192,184),width=2)
noise(im,2).save(O+'cream.png')
im=Image.new('RGB',(256,256),(168,159,148));noise(im,4).save(O+'deck.png')
im=Image.new('RGB',(512,256),(58,64,74));d=ImageDraw.Draw(im)   # dark units, white pipe runs and frame posts
for x0 in(10,150,300,420):d.rectangle([x0,90,x0+90,256],fill=(84,92,104));d.rectangle([x0,90,x0+90,104],fill=(120,128,138))
for y in(60,130,180):d.rectangle([0,y,512,y+10],fill=(214,218,222))
for x in range(0,512,64):d.rectangle([x,0,x+8,256],fill=(226,228,230))
noise(im,3).save(O+'plant.png')
# Brownlow annex next to the wedge (p1 zoom x 203-268, y 500-540): grey vertical fins 0.25 m on 0.45 m, dark behind;
# blue concourse band (82,93,110) under them. Tile 8 m wide.
im=Image.new('RGB',(512,256),(22,25,30));d=ImageDraw.Draw(im);pp=512*0.45/8
x=0.0
while x<512:d.rectangle([int(x),0,int(x+pp*0.42),256],fill=(112,116,122));d.line([(int(x),0),(int(x),256)],fill=(150,154,160));x+=pp
noise(im,2).save(O+'fins.png')
im=Image.new('RGB',(256,64),(82,93,110));d=ImageDraw.Draw(im);d.rectangle([0,0,256,4],fill=(140,150,165));noise(im,2).save(O+'blueband.png')
# scoreboard: red frame, live picture and score panel, drawn by hand
screen(724,384).save(O+'screen.png')
_sp=Image.new('RGB',(1600,200),(148,218,240));ImageDraw.Draw(_sp).rectangle([872,0,1600,200],fill=(152,153,158));_sp=noise(_sp,3).convert('RGBA')
from signs import roofsign;_sp.alpha_composite(roofsign(1600,200,872));_sp.convert('RGB').save(O+'sign.png')   # roof sign: gmhba STADIUM (p1)
json.dump(L,open('layout.json','w'))
print(L)
