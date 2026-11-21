import json,math,numpy as np
_s=json.load(open('align.json'))['s']
def f2w(X):
    X=np.atleast_2d(np.asarray(X,float));c,s=math.cos(_s[0]),math.sin(_s[0]);return X@np.array([[c,s],[-s,c]])+_s[1:3]
def w2f(X):
    X=np.atleast_2d(np.asarray(X,float))-_s[1:3];c,s=math.cos(_s[0]),math.sin(_s[0]);return X@np.array([[c,s],[-s,c]]).T
