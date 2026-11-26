"""Find Google Earth's popups in a screenshot (a near-white box with blue "Dismiss" text) and print the click
points, "x,y x,y", or nothing. Used by ge_nadir.js."""
import sys, numpy as np
from PIL import Image
a=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(int)
out=[]
# popups: near-white boxes (240..250) below the toolbar; "Dismiss" is blue text (26,115,232)-ish at the box's lower left
blue=(a[...,2]>200)&(a[...,0]<80)&(a[...,1]>90)&(a[...,1]<150)
ys,xs=np.nonzero(blue[85:260])
if len(xs):
    ys=ys+85
    # cluster by x gaps
    order=np.argsort(xs); xs,ys=xs[order],ys[order]
    groups=[[0]]
    for i in range(1,len(xs)):
        if xs[i]-xs[i-1]>40: groups.append([])
        groups[-1].append(i)
    for g in groups:
        if len(g)>15:
            x,y=int(np.median(xs[g])),int(np.median(ys[g]))
            box=a[max(0,y-30):y+20,max(0,x-40):x+150]
            if (box.min(-1)>232).mean()>0.6: out.append((x,y))
print(' '.join(f'{x},{y}' for x,y in out))
