# Fence ellipse fitted to the OSM pitch outline (at Cazaly's the grass runs past the fence, so the grass-edge trace can't be used).
import os, json, math, numpy as np
SP=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O=json.load(open(os.path.join(SP,'work','osm_xy.json')))
P=np.array(O['pitch'])[:-1]; x,y=P[:,0],P[:,1]
M=np.stack([x*x,x*y,y*y,x,y],1);A,B,C,D,E=np.linalg.lstsq(M,np.ones(len(x)),rcond=None)[0]
den=4*A*C-B*B;x0=(B*E-2*C*D)/den;y0=(B*D-2*A*E)/den;th=0.5*math.atan2(B,A-C)
ct,st=math.cos(th),math.sin(th);Ap=A*ct*ct+B*ct*st+C*st*st;Cp=A*st*st-B*ct*st+C*ct*ct
K=1+(A*x0*x0+B*x0*y0+C*y0*y0);a1,a2=math.sqrt(K/Ap),math.sqrt(K/Cp)
print('centre %.2f %.2f semi %.2f %.2f rot %.1f n=%d'%(x0,y0,a1,a2,math.degrees(th),len(P)))
json.dump(dict(ell=[x0,y0,a1,a2,math.degrees(th)]),open(os.path.join(SP,'work','fence.json'),'w'))
