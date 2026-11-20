import sys,json,numpy as np
from PIL import Image,ImageDraw
from camlib import *
c=json.load(open(sys.argv[1]));cam=c['p'][:7];cx,cy=512,314.5
im=Image.open('refs/c/03.jpg').convert('RGB');d=ImageDraw.Draw(im)
def line(P,col,w=2):
    q=proj(cam,np.c_[P,np.zeros(len(P))] if P.shape[1]==2 else P,cx,cy);d.line([tuple(x) for x in q],fill=col,width=w)
line(np.array(c['oval']),(255,140,0))
for i in (1430111014,951696127,1374562961,951696126):line(way(i),(0,255,255))
for i in (43878489,43878228,43878231,43878553,43878234,144908318):line(way(i),(255,0,255))
im.save(sys.argv[2])
