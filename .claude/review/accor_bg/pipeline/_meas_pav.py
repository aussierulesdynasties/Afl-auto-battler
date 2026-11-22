# sample the satellite (0.5 m/px, centre = scene origin) on a 120x120 m open plaza patch NE of the stadium
import numpy as np; from PIL import Image
im=np.asarray(Image.open('data/accor/sat.png').convert('RGB'),np.float32); H,W=im.shape[:2]; cx,cy=W//2,H//2
def px(x,y): return int(cx+x/0.5), int(cy-y/0.5)
# plaza between stadium (NE) and boulevard: sat_1km px ~ (700,420) -> m
def m(p): return ((p[0]*2000/1400-1000)*0.5, -(p[1]*2000/1400-1000)*0.5)
x0,y0=m((640,170)); x1,y1=m((900,430)); print('patch m',x0,y0,x1,y1)
a,b=px(x0,y0); c,d=px(x1,y1); P=im[b:d,a:c]; Image.fromarray(P.astype(np.uint8)).resize(((c-a)*2,(d-b)*2),Image.NEAREST).save('out/accor/pav_patch.png')
L=P.mean(2); print('size px',L.shape,'mean rgb',P.reshape(-1,3).mean(0).round(),'dark',np.percentile(L,15).round(),'light',np.percentile(L,85).round())
dk=P[L<np.percentile(L,25)].mean(0).round(); lt=P[L>np.percentile(L,75)].mean(0).round(); print('dark rgb',dk,'light rgb',lt)
for ax in (0,1):
  s=L.mean(ax)-L.mean(); f=np.abs(np.fft.rfft(s)); k=f[2:].argmax()+2; print('axis',ax,'period m',round(len(s)/k*0.5,1))
