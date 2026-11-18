import sys;from PIL import Image;import numpy as np
def ribs(path,x0=440,x1=1470):
    im=np.array(Image.open(path).convert('RGB')).astype(int)
    N=(im[:,:,2]>im[:,:,0]+12)&(im.max(2)<150)
    X=[];T=[]
    for x in range(x0,x1):
        ys=np.nonzero(N[740:930,x])[0]
        if len(ys)<5:continue
        X.append(x);T.append(740+ys.min())
    X=np.array(X);T=np.array(T,float)
    c=np.polyfit(X,T,6);d=T-np.polyval(c,X)
    d=np.convolve(d,np.ones(5)/5,'same')
    pk=[]
    for i in range(len(X)):
        w=(np.abs(X-X[i])<=20)
        if d[i]==d[w].max() and d[i]>1.0:pk.append(int(X[i]))
    return pk
if __name__=='__main__':
    print('photo ',ribs('photo_clean.png'));print('render',ribs(sys.argv[1]))
