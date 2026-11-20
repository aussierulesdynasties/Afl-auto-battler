import numpy as np
from PIL import Image, ImageDraw
im=np.asarray(Image.open('ref46.jpg').convert('RGB')).astype(float)
L=im.mean(2); S=im.max(2)-im.min(2)
grey=(L>120)&(S<40)
pts=[]
for x in range(680,1150,10):
    col=grey[330:480,x-3:x+4].mean(1)
    k=np.convolve(col,np.ones(5)/5,'same')
    # strongest horizontal-ish grey band in the column
    y=int(np.argmax(k))+330; pts.append((x,y,round(float(k.max()),2)))
print(pts)
img=Image.open('ref46.jpg').convert('RGB'); d=ImageDraw.Draw(img)
for x,y,v in pts: d.ellipse([x-2,y-2,x+2,y+2],outline=(255,0,0))
img.crop((660,320,1160,480)).resize((1500,480)).save('g/walkdet.png')
