import numpy as np,json,math
from PIL import Image,ImageDraw,ImageFilter
M=Image.open('field_mask.png').filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MaxFilter(9))
m=np.asarray(M)>0
# keep largest blob approx: restrict to ellipse-ish by removing pixels far outside -> just use as is after opening
O=json.load(open('C:/Users/DANTE/AppData/Local/Temp/claude/9f4017b9c485d8cb/fb8d066d-4ddf-4085-adc6-c6288b802d1c/scratchpad/moor/build.json'))
P=np.array(O['pitch'])[:-1]
lat=-37.9378;MPP=156543.03392*math.cos(math.radians(lat))/2**19
ys,xs=np.nonzero(m);cm=np.array([xs.mean(),ys.mean()])
def rast(th,s,t):
    c,si=math.cos(th),math.sin(th);Q=P-P.mean(0);Q=Q@np.array([[c,si],[-si,c]])*s/MPP
    pts=[(cm[0]+t[0]+x,cm[1]+t[1]-y) for x,y in Q]   # image y down = north up
    im=Image.new('L',m.shape[::-1]);ImageDraw.Draw(im).polygon(pts,fill=1);return np.asarray(im)>0,pts
def iou(th,s,t):r,_=rast(th,s,t);return (r&m).sum()/(r|m).sum()
best=max(((iou(math.radians(a),1,(0,0)),a) for a in range(-20,21,2)));print('coarse',best)
a0=best[1];bb=best
for a in np.arange(a0-3,a0+3,0.25):
  for s in (0.97,0.98,0.99,1.0,1.01,1.02,1.03):
    for tx in range(-16,17,2):
      for ty in range(-16,17,2):
        v=iou(math.radians(a),s,(tx,ty))
        if v>bb[0]:bb=(v,a,s,tx,ty)
print('fine',bb)
json.dump({'iou':bb[0],'rot_deg':bb[1],'scale':bb[2],'t':[bb[3],bb[4]],'cm':cm.tolist(),'mpp':MPP,'pmean':P.mean(0).tolist()},open('reg.json','w'))
_,pts=rast(math.radians(bb[1]),bb[2],(bb[3],bb[4]))
im=Image.open('wb_3026_z19.png').convert('RGB');d=ImageDraw.Draw(im);d.line(pts+[pts[0]],fill=(255,0,255),width=2);im.save('reg_check.png')
