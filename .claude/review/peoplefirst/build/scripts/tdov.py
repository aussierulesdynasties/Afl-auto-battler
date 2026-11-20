# overlay straight-down render on the satellite crop, same scale and north. python tdov.py td.png out.png
import sys,json,numpy as np
from PIL import Image
S=json.load(open('sat.json'));sat=Image.open('sat.png').convert('RGB');W=1000
x0,y0=int(round(S['px']-W/2)),int(round(S['py']-W/2));crop=sat.crop((x0,y0,x0+W,y0+W))
td=Image.open(sys.argv[1]).convert('RGBA');al=np.array(td)[...,3:]/255.0
c=np.array(crop).astype(float);t=np.array(td)[...,:3].astype(float)
blend=c*(1-0.5*al)+t*0.5*al
# edge of the model's silhouette in magenta on the satellite
import cv2
m=(al[...,0]>0.5).astype(np.uint8);e=cv2.morphologyEx(m,cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8))>0
edge=c.copy();edge[e]=(255,0,255)
out=np.concatenate([c,blend,edge],1);Image.fromarray(out.astype(np.uint8)).save(sys.argv[2]);print('ok')
