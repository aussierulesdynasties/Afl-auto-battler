import io,contextlib
with contextlib.redirect_stdout(io.StringIO()):import model
from cam import *
def rd(u,v,z):
    p=at_z(u,v,z);a=math.atan2(p[1]-model.PC[1],p[0]-model.PC[0]);return round(math.degrees(a)%360,1),round(float(np.hypot(p[0]-model.PC[0],p[1]-model.PC[1])-model.edge(a)),1)
def run(F,x0=0,y0=0,k=1.0):
    for name,(z,P) in F.items():print(name,z,[rd(x0+cx/k,y0+cy/k,z) for cx,cy in P])
