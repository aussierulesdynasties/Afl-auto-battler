import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont
rng=np.random.default_rng(7)
O='tex2/'
def noise(h,w,sc,amp):   # seamless: the coarse grid wraps, so the tile repeats without a seam
    gh,gw=max(2,h//sc),max(2,w//sc);n=rng.normal(0,1,(gh,gw));t=np.tile(n,(3,3))
    im=Image.fromarray(((t-t.min())/(t.max()-t.min())*255).astype(np.uint8)).resize((3*w,3*h),Image.BICUBIC)
    return (np.asarray(im)[h:2*h,w:2*w]/255.0-0.5)*amp
def save(a,n):Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(O+n+'.png')
# concrete: 4 m tile at 128 px/m -> 512
h=w=512;c=np.ones((h,w,3))*np.array([178,174,166])
c+=(noise(h,w,64,30)+noise(h,w,8,10)+rng.normal(0,4,(h,w)))[...,None]
for y in range(0,h,128):c[y:y+2]*=0.82   # form joints every 1 m
save(c,'concrete')
# seat-bowl aisles and risers (photo: dark grey, barely lighter than the seats)
ca=np.ones((h,w,3))*np.array([50,48,48])+(noise(h,w,64,10)+noise(h,w,8,5)+rng.normal(0,2,(h,w)))[...,None]
for y in range(0,h,128):ca[y:y+2]*=0.8
save(ca,'aislec')
# weathered terrace concrete for the upper bowl (photo: browner and darker than the walkways)
c2=np.ones((h,w,3))*np.array([104,88,86])+(noise(h,w,64,20)+noise(h,w,8,8)+rng.normal(0,3,(h,w)))[...,None]
for y in range(0,h,128):c2[y:y+2]*=0.82
save(c2,'bowlconc')
# open-end terrace treads (photo s 30-100 and the gap: light pink-grey between dark benches)
c3=np.ones((h,w,3))*np.array([200,178,174])+(noise(h,w,64,14)+noise(h,w,8,6)+rng.normal(0,3,(h,w)))[...,None]
for y in range(0,h,128):c3[y:y+2]*=0.85
save(c3,'bowllight')
# dark concrete for facades/back walls with column every 2 m
# open dark framework (photo: dark voids between pale columns and floor beams under the roof edge)
c=np.ones((h,w,3))*np.array([26,24,24])+(noise(h,w,64,10)+rng.normal(0,2,(h,w)))[...,None]
for y in (0,256):c[y:y+30]=np.array([64,62,58])+rng.normal(0,3,(30,w,1))
for x in range(0,w,256):c[:,x:x+34]=np.array([70,67,63])+rng.normal(0,3,(h,34,1))
for x in range(128,w,256):c[:,x:x+10]=np.array([52,50,48])
save(c,'facade')
# facade frame as geometry: plain materials for the void, columns and slabs
for nm,col,a in(('fvoid',(26,24,24),6),('fcol',(70,67,63),5),('fslab',(64,62,58),5)):
    save(np.ones((h,w,3))*np.array(col)+(noise(h,w,64,a*2)+rng.normal(0,a/2,(h,w)))[...,None],nm)
# seat texture: tile = 2 m along row (u) x 1 m (v); seats 0.5 m apart, white shells (tinted by vertex colour)
h,w=128,256;s=np.ones((h,w,3))*np.array([70,70,72])  # gaps (shadow between seats)
im=Image.fromarray(s.astype(np.uint8));d=ImageDraw.Draw(im)
for k in range(4):
    x0=k*64+5;d.rounded_rectangle([x0,8,x0+54,h-8],radius=14,fill=(238,238,238))
    d.rounded_rectangle([x0+4,h-40,x0+50,h-14],radius=8,fill=(214,214,214))
a=np.asarray(im).astype(float)+rng.normal(0,3,(h,w,1));save(a,'seat')
# roof deck: profiled metal sheeting, ribs every 0.25 m, tile 4 m (u along slope? v across) 512px
h=w=512;r=np.ones((h,w,3))*np.array([214,216,218])+(noise(h,w,64,10))[...,None]
for x in range(0,w,32):r[:,x:x+4]*=0.86;r[:,x+4:x+6]*=1.05
for y in range(0,h,256):r[y:y+3]*=0.8
save(r,'roof')
# white painted steel / fascia
a=np.ones((128,128,3))*np.array([236,236,233])+rng.normal(0,2,(128,128,1));save(a,'white')
# steel (galvanised lattice members)
a=np.ones((64,64,3))*np.array([186,190,192])+rng.normal(0,4,(64,64,1));save(a,'steel')
# roof underside
a=np.ones((256,256,3))*np.array([120,122,124])+noise(256,256,32,12)[...,None]
for x in range(0,256,32):a[:,x:x+3]*=0.75
save(a,'underside')
# glass: dark tinted panes 1.5 m wide with mullions, tile 6 m x 3 m (512x256)
a=np.ones((256,512,3))*np.array([38,48,58])+noise(256,512,64,14)[...,None]
for x in range(0,512,128):a[:,x:x+6]=[150,152,154]
a[:6]=[150,152,154];a[-6:]=[150,152,154];a[120:126]=[120,122,124]
save(a,'glass')
# lamp head face: 10 x 7 m frame, lamps in 6 rows x 10
h,w=448,640;a=np.ones((h,w,3))*np.array([60,62,66]);im=Image.fromarray(a.astype(np.uint8));d=ImageDraw.Draw(im)
d.rectangle([0,0,w-1,h-1],outline=(190,192,194),width=10)
for i in range(10):
    for j in range(6):
        cx=32+i*64;cy=37+j*70;d.ellipse([cx-24,cy-24,cx+24,cy+24],fill=(150,152,150));d.ellipse([cx-17,cy-17,cx+17,cy+17],fill=(236,236,228))
im.save(O+'lamps.png')
# lamp head back: the backs of the lamp cans in a steel frame, one column of 6 cans per panel strip
im=Image.new('RGB',(64,256),(74,75,78));d=ImageDraw.Draw(im)
for j in range(6):
    cy=21+j*42;d.ellipse([10,cy-19,54,cy+19],fill=(118,119,122));d.ellipse([16,cy-13,48,cy+13],fill=(152,153,156))
im.save(O+'lampback.png')
# race roof (brown-red painted sheet)
a=np.ones((128,256,3))*np.array([128,78,66])+rng.normal(0,3,(128,256,1))
for x in range(0,256,16):a[:,x:x+2]*=0.85
save(a,'race')
# blue roof sheet (end building)
a=np.ones((128,256,3))*np.array([84,98,116])+rng.normal(0,3,(128,256,1))
for x in range(0,256,16):a[:,x:x+2]*=0.85
save(a,'blueroof')
# navy shed wall (dark painted sheet, vertical seams)
a=np.ones((128,128,3))*np.array([16,24,54])+rng.normal(0,2,(128,128,1))
for x in range(0,128,16):a[:,x:x+2]*=0.7
save(a,'navywall')
a=np.ones((64,64,3))*np.array([196,36,40])+rng.normal(0,3,(64,64,1));save(a,'redpaint')
a=np.ones((64,64,3))*np.array([22,22,24]);save(a,'black')
print('ok')
