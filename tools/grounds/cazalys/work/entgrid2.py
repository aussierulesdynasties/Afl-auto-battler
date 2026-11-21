import math,json,sys,io,urllib.request
sys.path.insert(0,'work');import geo
from PIL import Image,ImageDraw
z=19;n=2**z
la,lo=geo.xy2ll(0,-130)
xt=(lo+180)/360*n;yt=(1-math.asinh(math.tan(math.radians(la)))/math.pi)/2*n
X0,Y0=int(xt)-2,int(yt)-2;K=4
im=Image.new('RGB',(256*K,256*K))
for i in range(K):
  for j in range(K):
    r=urllib.request.Request(f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{Y0+j}/{X0+i}',headers={'User-Agent':'Mozilla/5.0'})
    im.paste(Image.open(io.BytesIO(urllib.request.urlopen(r).read())),(i*256,j*256))
im=im.resize((512*K,512*K),Image.LANCZOS);d=ImageDraw.Draw(im)
def xy2px(x,y):
  a,b=geo.xy2ll(x,y);gx=(b+180)/360*n;gy=(1-math.asinh(math.tan(math.radians(a)))/math.pi)/2*n
  return ((gx-X0)*512,(gy-Y0)*512)
P=json.load(open('work/osm_xy.json'))['bldg_s'];d.line([xy2px(*p) for p in P],fill=(255,0,0),width=2)
for g in range(-100,101,5):
  c=(255,255,0) if g%10==0 else (0,200,255)
  d.line([xy2px(g,-60),xy2px(g,-200)],fill=c,width=1);d.line([xy2px(-100,-g-100),xy2px(100,-g-100)],fill=c,width=1)
  d.text(xy2px(g,-62),str(g),fill='yellow');d.text(xy2px(-98,-g-100),str(-g-100),fill='yellow')
x0,y0=xy2px(10,-95);x1,y1=xy2px(60,-160)
im.crop((int(x0),int(y0),int(x1),int(y1))).save(sys.argv[1])
