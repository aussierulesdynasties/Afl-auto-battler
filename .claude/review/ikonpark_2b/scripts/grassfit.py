# grassfit.py GEOM SAT -> per pitch vertex: distance out from the OSM pitch line where the turf ends (greenness drop)
import cv2,json,sys,numpy as np
G=json.load(open(sys.argv[1]));im=cv2.GaussianBlur(cv2.imread(sys.argv[2]).astype(np.float32),(0,0),1.5)
gr=im[:,:,1]-(im[:,:,0]+im[:,:,2])/2
def val(x,y):return cv2.getRectSubPix(gr,(1,1),(float((x+150)/0.25),float((230-y)/0.25)))[0,0]
P=np.array(G['pitch']);cp=P.mean(0);T=np.arange(0,25,0.25);out=[]
for p in P:
  d=(p-cp)/np.linalg.norm(p-cp);pr=np.array([val(*(p+t*d)) for t in T]);d1=-np.gradient(pr)
  j=int(np.argmax(d1[8:]))+8;out.append(T[j])
out=np.array(out);print('offset now',round(G['grass_offset'],2),'median edge',np.median(out),'p10/p90',np.percentile(out,[10,90]))
print(' '.join(f'{v:.1f}' for v in out))
