import numpy as np,json
from PIL import Image
I=np.asarray(Image.open('refs/aus/ikon-park-2.jpg').convert('RGB')).astype(float)
r,g,b=I[...,0],I[...,1],I[...,2]
grass=(g>r+5)&(g>b+5)&(g<170)
sky=(b>r+40)&(b>g+10)&(b>150)
edge=[];top=[]
for x in range(2,1198,6):
    col=grass[:,x-2:x+3].mean(1)
    # scan up from y=430 while grass
    y=440
    while y>330 and col[y]>0.6: y-=1
    edge.append((x,y+0.5))
    s=sky[:,x-1:x+2].mean(1); y=150
    while y<330 and s[y]>0.6: y+=1
    top.append((x,y-0.5))
json.dump({'edge':edge,'top':top},open('w/i2_trace.json','w'))
print(edge[::10]);print(top[::10])
