import json,numpy as np,math
r=json.load(open('rall.json'));pts=json.load(open('rad.json'))
ok=[x for x in r if x[4] is not None]
lat0=np.mean([x[2] for x in ok]);lon0=np.mean([x[3] for x in ok])
# field centre: the screen centre point (710,430) is at r=0; estimate from linear fit screen->latlon
X=np.array([[x[0],x[1],1] for x in ok]);la=np.linalg.lstsq(X,[x[2] for x in ok],rcond=None)[0];lo=np.linalg.lstsq(X,[x[3] for x in ok],rcond=None)[0]
c=(np.dot([640,500,1],la),np.dot([640,500,1],lo));k=111320
def xy(a,b):return ((b-c[1])*k*math.cos(math.radians(c[0])),(a-c[0])*110950)
turf=np.median([x[4] for x in ok if math.hypot(*xy(x[2],x[3]))<80]);print('centre',c,'turf',turf)
by={}
for x in ok:
    e,n=xy(x[2],x[3]);b=round(math.degrees(math.atan2(n,e))/5)*5%360;by.setdefault(b,[]).append((math.hypot(e,n),x[4]-turf))
for b in sorted(by):
    p=sorted(by[b]);s=' '.join('%d'%h for d,h in p)
    # roof front: first point with h>=8 after r>70
    rf=next(((d,h) for d,h in p if d>70 and h>=8),None)
    print('%3d'%b,'roof front r=%.1f h=%d'%rf if rf else 'none      ','|',s)
