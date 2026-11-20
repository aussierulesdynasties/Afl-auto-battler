from cam import *
from PIL import Image,ImageDraw
pp=np.array(G['pitch']);pa=np.arctan2(pp[:,1]-PC[1],pp[:,0]-PC[0]);pr=np.hypot(pp[:,0]-PC[0],pp[:,1]-PC[1]);o=np.argsort(pa)
def redge(a):return np.interp(a,pa[o],pr[o],period=2*math.pi)
def P_(a,d,z=0):r=redge(a)+d;return (PC[0]+r*math.cos(a),PC[1]+r*math.sin(a),z)
if __name__=='__main__':
    im=Image.open('photo.png').convert('RGB');dr=ImageDraw.Draw(im)
    for deg in range(0,360,10):
        a=math.radians(deg);Y=proj([P_(a,d) for d in range(0,71,5)]);dr.line([tuple(y) for y in Y],fill=(255,255,0),width=1);dr.text(tuple(Y[-1]),str(deg),fill=(255,255,0))
    for dd in range(10,71,10):
        Y=proj([P_(math.radians(t),dd) for t in range(0,361,2)]);dr.line([tuple(y) for y in Y],fill=(0,255,255) if dd%20 else (255,0,255),width=1)
    im.save('z/polar.png')
