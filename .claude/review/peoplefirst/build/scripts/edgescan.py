import sys;from PIL import Image;import numpy as np
def scan(path,xs,y0=740,y1=1060):
    im=np.array(Image.open(path).convert('RGB')).astype(int)
    W=(im.min(2)>195)&((im.max(2)-im.min(2))<30);out={}
    for x in xs:
        col=list(W[y0:y1,x])+[False];best=(0,0,0);s=None
        for i,w in enumerate(col):
            if w and s is None:s=i
            if not w and s is not None:
                if i-s>best[0]:best=(i-s,s,i)
                s=None
        out[x]=y0+best[2]
    return out
if __name__=='__main__':
    xs=range(440,1461,20);P=scan('photo_clean.png',xs);R=scan(sys.argv[1],xs)
    print(' '.join('%d:%+d'%(x,R[x]-P[x]) for x in xs))
