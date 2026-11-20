from PIL import Image
import numpy as np
ph=Image.open('photo.jpg').convert('L');rn=Image.open('ren.png').convert('L')
P=np.array(ph.crop((486,492,536,544)).resize((200,208),Image.BICUBIC)).astype(float);P=(P-P.mean())/P.std()
best=None
for s in np.arange(0.90,1.101,0.02):
  for dy in np.arange(-4,4.01,0.5):
    for dx in np.arange(-4,4.01,0.5):
      cx,cy=511+dx,518+dy;hw,hh=25*s,26*s
      R=np.array(rn.crop((int(0),0,1200,675)).transform((200,208),Image.EXTENT,(cx-hw,cy-hh,cx+hw,cy+hh),Image.BICUBIC)).astype(float)
      R=(R-R.mean())/R.std();c=(P*R).mean()
      if best is None or c>best[0]:best=(c,s,dx,dy)
print('corr %.3f scale %.2f dx %.1f dy %.1f'%best)
