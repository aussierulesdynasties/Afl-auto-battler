# flat-shaded painter render of geo.py from the matched camera; writes render + overlay
import sys
exec(open('geo.py').read())
from PIL import Image,ImageDraw
Va=np.array(V,float);d=(Va-C)@M.T;uv=np.stack([cx0+fo*d[:,0]/d[:,2],cy0-fo*d[:,1]/d[:,2]],1)
L=np.array([-0.45,0.35,0.82]);L/=np.linalg.norm(L)
order=sorted(range(len(F)),key=lambda i:-np.mean([d[j,2] for j in F[i][0]]))
im=Image.new('RGB',(W,H),(0,0,0));dr=ImageDraw.Draw(im);mask=Image.new('L',(W,H),0);dm=ImageDraw.Draw(mask)
for i in order:
    idx,m=F[i];pts=Va[list(idx)];n=np.cross(pts[1]-pts[0],pts[2]-pts[0]);nn=np.linalg.norm(n)
    if nn<1e-9:continue
    n/=nn
    if np.dot(n,C-pts.mean(0))<0:n=-n
    s=0.55+0.45*max(0,np.dot(n,L));col=tuple(int(min(255,c_*s)) for c_ in MATS[m])
    poly=[tuple(uv[j]) for j in idx];dr.polygon(poly,fill=col);dm.polygon(poly,fill=255)
tag=sys.argv[1] if len(sys.argv)>1 else 'v1'
im.save('g/r_%s.png'%tag)
ph=Image.open('refs/scg.jpg').convert('RGB');ov=Image.blend(ph,im,0.5);ov.save('g/o_%s.png'%tag)
# edge overlay: model edges in red on photo
import numpy as _n
from PIL import ImageFilter
e=im.convert('L').filter(ImageFilter.FIND_EDGES).point(lambda x:255 if x>25 else 0)
ed=ph.copy();ed.paste((255,0,0),mask=e);ed.save('g/e_%s.png'%tag)
print('faces',len(F))
