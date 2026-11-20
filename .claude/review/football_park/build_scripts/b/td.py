import json,math,numpy as np
from scipy.optimize import least_squares
from camlib import *
def xy2td(x,y):
    s=least_squares(lambda q:[(72.5+q[1])*math.cos(q[0])-x,(88.5+q[1])*math.sin(q[0])-y],[math.atan2(y/88.5,x/72.5),math.hypot(x,y)-80])
    return math.degrees(s.x[0])%360,s.x[1]
def uv2td(p,u,v,z):
    X=at_z(p,u,v,z);return xy2td(X[0],X[1])
