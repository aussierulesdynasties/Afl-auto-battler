import sys;from PIL import Image;import numpy as np
def scan(path,xs,y0,y1):
    im=np.array(Image.open(path).convert('RGB')).astype(int)
    N=(im[:,:,2]>im[:,:,0]+12)&(im.max(2)<150)
    out={}
    for x in xs:
        ys=np.nonzero(N[y0:y1,x])[0]
        out[x]=(y0+ys.min(),y0+ys.max()) if len(ys)>2 else None
    return out
if __name__=='__main__':
    x0,x1,y0,y1=map(int,sys.argv[2:6]);xs=range(x0,x1,int(sys.argv[6]) if len(sys.argv)>6 else 5)
    P=scan('photo_clean.png',xs,y0,y1);R=scan(sys.argv[1],xs,y0,y1)
    for x in xs:print(x,'photo',P[x],'render',R[x])
