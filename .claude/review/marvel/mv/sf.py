# stadium frame helpers: (u,v,z) -> local (s,t,z) -> world; project with a camera json
import sys,os,math,json,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from frame import *
from cam import proj
O=np.array([-7.12,-6.5]);TH=math.radians(-7.27);U=np.array([math.cos(TH),math.sin(TH)]);V=np.array([-U[1],U[0]])
def st(u,v):return O+u*U+v*V
def uvw(u,v,z):s,t=st(u,v);return wld(s,t,z)
def P(cam):return json.load(open(cam))['p']
def pj(p,pts):return proj(p,[uvw(*q) for q in pts])
