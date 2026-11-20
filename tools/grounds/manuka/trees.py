# find tree crowns in the reference: green, textured pixels outside the stands; back-project at crown height
import io,contextlib,math,json,numpy as np
from PIL import Image,ImageFilter
with contextlib.redirect_stdout(io.StringIO()): import model
import cam
from scipy import ndimage
im=Image.open('photo.png').convert('RGB');a=np.array(im,float);H,W,_=a.shape
R,G,B=a[...,0],a[...,1],a[...,2]
g=np.array(im.convert('L').filter(ImageFilter.FIND_EDGES),float)
tex=ndimage.uniform_filter(g,9)
green=(G>=R-4)&(G>B+6)&(tex>12)&(G<235)
# distance beyond the grass edge for each pixel at z 6
ys,xs=np.mgrid[0:H:4,0:W:4]
D=np.full((H//4+1,W//4+1),-1.0)
for i in range(ys.shape[0]):
    for j in range(ys.shape[1]):
        X=cam.at_z(xs[i,j],ys[i,j],6.0)
        if X is None:continue
        a_=math.atan2(X[1]-model.PC[1],X[0]-model.PC[0]);r=math.hypot(X[0]-model.PC[0],X[1]-model.PC[1])
        D[i,j]=r-(model.edge(a_)+model.PC[0]*0 if False else r-model.edge(a_)) if False else r-math.hypot(*(np.array(model.P(a_,0,0)[:2])-model.PC))
Dfull=np.array(Image.fromarray(D.astype(np.float32)).resize((W,H),Image.NEAREST))
mask=green&(Dfull>16)&(Dfull<52)
mask=ndimage.binary_opening(mask,iterations=2)
Image.fromarray((mask*255).astype(np.uint8)).save('z/tree_mask.png')
lab,n=ndimage.label(mask);out=[]
for k,sl in enumerate(ndimage.find_objects(lab),1):
    m=lab[sl]==k;area=m.sum()
    if area<120:continue
    yy,xx=np.nonzero(m);yy=yy+sl[0].start;xx=xx+sl[1].start
    # split big clumps into ~40 px cells
    for cy in range(yy.min(),yy.max()+1,40):
        for cx in range(xx.min(),xx.max()+1,40):
            s_=(yy>=cy)&(yy<cy+40)&(xx>=cx)&(xx<cx+40)
            if s_.sum()<300:continue
            u,v=xx[s_].mean(),yy[s_].mean();X=cam.at_z(u,v,6.0)
            out.append((float(X[0]),float(X[1]),float(math.sqrt(s_.sum())/40)))
json.dump(out,open('trees.json','w'));print(n,len(out))
