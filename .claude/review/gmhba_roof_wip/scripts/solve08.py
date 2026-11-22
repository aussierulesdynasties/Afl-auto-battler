import numpy as np
from scipy.optimize import least_squares
W,H=7758,3633;cx,cy=W/2,H/2
P3=lambda h:np.array([[-120,-3.4,24],[-120,-44.8,24],[-120,-3.4,h],[-120,-44.8,h],[-126,22.2,22.7],[-126,-3.4,22.7],[-122.5,-59.2,74.7],[-122.5,-59.2,0],[-57.8,108.0,74.7],[104.5,68.7,74.7]])
px=np.array([[4963,2285],[5952,2388],[4960,2620],[5935,2730],[4237,2308],[4851,2324],[6220,1188],[6162,2898],[3890,1100],[7010,1088]],float)
def proj(q,X):
    C=q[:3];yaw,pit,f=q[3],q[4],q[5]
    fw=np.array([np.cos(pit)*np.cos(yaw),np.cos(pit)*np.sin(yaw),np.sin(pit)])
    rt=np.cross(fw,[0,0,1]);rt/=np.linalg.norm(rt);up=np.cross(rt,fw)
    d=X-C;z=d@fw
    return np.stack([cx+f*(d@rt)/z,cy-f*(d@up)/z],1)
def res(q):return (proj(q,P3(q[6]))-px).ravel()
q0=[-430,-100,165,np.arctan2(-8+100,-118+430),np.arctan2(10-165,np.hypot(312,92)),4000,4.5]
r=least_squares(res,q0)
q=r.x;e=res(q).reshape(-1,2)
print('cam',np.round(q[:3],1),'yaw',round(np.degrees(q[3]),2),'pitch',round(np.degrees(q[4]),2),'f_px',round(q[5]),'band_z',round(q[6],2))
print('rms px',round(np.sqrt((e**2).sum(1).mean()),1),'per point',np.round(np.hypot(*e.T),1))
fw=np.array([np.cos(q[4])*np.cos(q[3]),np.cos(q[4])*np.sin(q[3]),np.sin(q[4])]);T=q[:3]+fw*300
lens=q[5]/W*36
print('VIEW %.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.2f'%(*q[:3],*T,lens))
print('bearing from block to cam',round(np.degrees(np.arctan2(q[1]-10,q[0]+121))%360,1),'(math deg, x east y north)')
