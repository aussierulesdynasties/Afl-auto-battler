import numpy as np,math,json,datetime
from scipy.optimize import least_squares
exec(open('cam.py').read());from sun import sunpos
p=P();OFF=np.array([3800,14800])
def F2(uv):return np.array(uv,float)+OFF   # crop coords -> frame
def C2(uv):return np.array(uv,float)-OFF
def sdir(az,el):
    a=math.radians(az);return np.array([-math.sin(a),-math.cos(a)])/math.tan(math.radians(el))  # ground offset per metre height
def roof_world(uv,h):return at_z(p,*F2(uv),h)
def shadow_img(uv,h,az,el):
    X=roof_world(uv,h);g=np.array([X[0],X[1],0.0]);g[:2]+=h*sdir(az,el);return C2(proj(p,g)[0])
def h_from(uv,sh,az,el):
    s=least_squares(lambda q:shadow_img(uv,q[0],az,el)-sh,[8.0]);return s.x[0],s.fun
def at_t(m):t=datetime.datetime(1992,2,16,3,0)+datetime.timedelta(minutes=m);return sunpos(t)
