# python bands.py u1,u2,.. v0 v1 x0 y0 x1 y1 : colour runs down photo columns, z on a vertical plane
import sys;from PIL import Image;from cam import at_plane
im=Image.open('p92.png').convert('RGB')
us=[int(t) for t in sys.argv[1].split(',')];v0,v1=int(sys.argv[2]),int(sys.argv[3]);L=tuple(float(t) for t in sys.argv[4:8])
def cls(r,g,b):
    mx,mn=max(r,g,b),min(r,g,b);l=(r+g+b)/3
    if r>170 and g>110 and b<100 and r-b>90:return 'Y'
    if r>110 and r-g>45 and r-b>45:return 'R'
    if g>r+10 and g>b+10:return 'V'
    if l>185 and mx-mn<45:return 'W'
    if l<85:return 'D'
    return 'G'
for u in us:
    runs=[];prev=None
    for v in range(v0,v1):
        c=cls(*[sum(im.getpixel((uu,v))[i] for uu in (u-1,u,u+1))//3 for i in range(3)])
        if c!=prev:runs.append([c,v,v]);prev=c
        else:runs[-1][2]=v
    out=[]
    for c,a,b in runs:
        if b-a<2:continue
        za=at_plane(u,a,*L)[2];zb=at_plane(u,b+1,*L)[2]
        out.append('%s %d-%d z%.1f-%.1f'%(c,a,b,zb,za))
    x,y,_=at_plane(u,v0,*L);print('u',u,'x%.1f y%.1f'%(x,y),' | '.join(out))
