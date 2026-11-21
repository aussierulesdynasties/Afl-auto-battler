from PIL import Image,ImageDraw,ImageFont
import glob
ref=Image.open('photo.png').convert('RGB')
try:F=ImageFont.truetype('arial.ttf',26);f=ImageFont.truetype('arial.ttf',20)
except:F=f=ImageFont.load_default()
# hidden faces in the reference (photo px boxes)
faces=[('1  Media Centre lower facade (behind the big tree)',(250,880,520,1080)),
       ('2  Pavilion south face (behind trees)',(500,930,720,1060)),
       ('3  Sign building left half (behind a tree)',(800,960,1000,1060))]
W=1920;rows=[]
for t,b in faces:
    c=ref.crop(b);k=360/c.height;c=c.resize((int(c.width*k),360),Image.LANCZOS);rows.append((t,c))
thumbs=sorted(glob.glob('j26/Manuka_Oval_*.jpg'))
lab={'January_2026_01':'gate + ticket wall','January_2026_02':'gate + ticket wall','January_2026_03':'Main Gate',
'January_2026_04':'stand A-frames','January_2026_05':'stand A-frames','January_2026_06':'A-frame, green roof',
'January_2026_07':'stand A-frames','January_2026_08':'sign tower at a gate','January_2026_09':'VIP Gate',
'January_2026_10':'louvred pavilion','January_2026_11':'temp Hill Stand','January_2026_12':'box + hill',
'January_2026_13':'box + hill','January_2026_14':'temp Hill Stand 2','January_2026_15':'gate','January_2026_16':'gate',
'December_2019_01':'2019 site fence','December_2019_02':'2019 pavilion','December_2019_03':'2019 gate','December_2019_04':'2019 gate',
'December_2019_05':'2019 A-frames','December_2019_06':'2019 car park'}
tw,th=310,232
H=60+410+60+((len(thumbs)+5)//6)*(th+34)+20
B=Image.new('RGB',(W,H),(24,24,28));d=ImageDraw.Draw(B);y=14
d.text((16,y),'Reference (Region Media, Oct 2021): the three faces trees hide',fill=(255,255,255),font=F);y+=46
x=16
for t,c in rows:
    pass
x=16;mh=0
for t,c in rows:
    if x+c.width>W:x=16;y+=mh+50;mh=0
    d.text((x,y),t,fill=(255,220,120),font=f);B.paste(c,(x,y+28));x+=c.width+20;mh=max(mh,c.height)
y+=mh+50
d.text((16,y),'All 22 Commons photos (DaHuzyBru, CC BY-SA 4.0): what each one shows. None shows faces 1-3.',fill=(255,255,255),font=F);y+=46
for i,p in enumerate(thumbs):
    im=Image.open(p).convert('RGB').resize((tw,th),Image.LANCZOS);xx=16+(i%6)*(tw+8);yy=y+(i//6)*(th+34)
    B.paste(im,(xx,yy));key=p.split('Oval_')[1][:-4];d.text((xx,yy+th+4),('J26-' if key.startswith('Jan') else 'D19-')+key[-2:]+' '+lab.get(key,'').replace('2019 ',''),fill=(220,220,220),font=f)
B.save('z/hidden_faces_search.png');print(B.size)
