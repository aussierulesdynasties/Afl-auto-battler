import json,numpy as np,hashlib
def enc(c):
    c=np.asarray(c,float);return np.where(c<=0.0031308,12.92*c,1.055*c**(1/2.4)-0.055)*255
def table(names):
    return {n:enc([b/255 for b in hashlib.md5(n.encode()).digest()[:3]]) for n in names}
def name(px,T):
    best=min(T,key=lambda n:np.abs(T[n]-px).sum());return best,np.abs(T[best]-px).sum()
