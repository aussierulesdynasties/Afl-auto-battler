import numpy as np
from PIL import Image
PAL={'R':(205,40,50),'M':(125,35,45),'Y':(250,200,90),'G':(34,98,52),'B':(55,80,160),'P':(235,160,165),'rose':(215,95,105),'L':(165,160,195),'K':(240,205,155),'W':(235,235,232),'sage':(115,150,120),'N':(25,28,45),'grey':(58,44,44),'mg':(52,74,58),'ug':(58,54,58)}
s=np.asarray(Image.open('tex2/seat.png')).astype(float)/238.0
for k,c in PAL.items():
    a=np.clip(s*np.array(c),0,255).astype(np.uint8);Image.fromarray(a).save(f'tex2/seat_{k}.png')
print('ok',len(PAL))
