from polar import *
from PIL import Image,ImageDraw
im=np.array(Image.open('photo.png').convert('RGB')).astype(int)
res=[]
for deg in np.arange(0,360,2.0):
    a=math.radians(deg);best=None
    for d in np.arange(-14,8,0.1):
        u,v=proj([P_(a,d,0)])[0];px=im[int(v),int(u)]
        if px.min()>175 and px.max()-px.min()<45:best=d;break
    res.append((deg,best))
json.dump(res,open('edge_auto.json','w'))
o=Image.open('photo.png').convert('RGB');dr=ImageDraw.Draw(o)
for deg,d in res:
    if d is None:continue
    u,v=proj([P_(math.radians(deg),d,0)])[0];dr.ellipse((u-3,v-3,u+3,v+3),outline=(255,0,255))
o.resize((1400,933)).save('z/edge_auto.png')
print([(d,None if b is None else round(b,1)) for d,b in res])
