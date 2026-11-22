# hand-made matte pale-grey trapezoidal sheet: 4 m x 4 m tile, 1024 px
from PIL import Image,ImageDraw,ImageFilter
import random
random.seed(3);N=1024;im=Image.new('RGB',(N,N),(176,180,182));d=ImageDraw.Draw(im)
for x in range(N):  # trapezoidal ribs every 0.25 m (64 px): crest light, flank shade
    m=x%64
    if m<6:c=(196,199,201)
    elif m<10:c=(150,154,157)
    elif 34<m<38:c=(186,189,191)
    else:c=(174+((x*7)%5),178,181)
    d.line([(x,0),(x,N)],fill=c)
for y in (0,512):  # end laps of sheets
    d.rectangle([0,y,N,y+3],fill=(140,144,147))
for i in range(260):  # fixings
    x=random.randrange(0,N//64)*64+3;y=random.randrange(0,N);d.point((x,y),fill=(120,122,124))
im=im.filter(ImageFilter.GaussianBlur(0.6));im.save('jss_sheet.png')
st=Image.new('RGB',(256,256),(78,82,86));d=ImageDraw.Draw(st)
for y in range(0,256,32):d.line([(0,y),(256,y)],fill=(66,70,74),width=2)
st.save('jss_steel.png')
fa=Image.new('RGB',(512,256),(156,160,163));d=ImageDraw.Draw(fa)
for x in range(0,512,8):d.line([(x,0),(x,256)],fill=(146,150,153))
for x in range(0,512,256):d.rectangle([x,0,x+2,256],fill=(110,114,117))
d.rectangle([0,0,512,6],fill=(185,188,190));fa.save('jss_fascia.png')
