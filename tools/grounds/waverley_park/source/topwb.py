import json,math,io,sys,urllib.request,numpy as np
from PIL import Image
lo0,la0,lo1,la1=map(float,open('bbox2.txt').read().split(','))
z=19;n=2**z
def mx(lo):return (lo+180)/360*n*256
def my(la):r=math.radians(la);return (1-math.log(math.tan(r)+1/math.cos(r))/math.pi)/2*n*256
X0,X1,Y0,Y1=mx(lo0),mx(lo1),my(la1),my(la0)
for rel,lab in [(a,b) for a,b in (x.split(':') for x in sys.argv[1:])]:
    tx0,tx1,ty0,ty1=int(X0//256),int(X1//256),int(Y0//256),int(Y1//256)
    M=Image.new('RGB',((tx1-tx0+1)*256,(ty1-ty0+1)*256))
    for ty in range(ty0,ty1+1):
        for tx in range(tx0,tx1+1):
            u='https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/default028mm/MapServer/tile/%s/%d/%d/%d'%(rel,z,ty,tx)
            try:M.paste(Image.open(io.BytesIO(urllib.request.urlopen(u,timeout=30).read())).convert('RGB'),((tx-tx0)*256,(ty-ty0)*256))
            except Exception as e:print('miss',tx,ty,e)
    M=M.crop((round(X0-tx0*256),round(Y0-ty0*256),round(X1-tx0*256),round(Y1-ty0*256))).resize((2000,2000),Image.LANCZOS)
    M.save('wb_%s.jpg'%lab,quality=92);print('saved',lab)
