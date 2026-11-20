import numpy as np,math,json
U0,V0=10594.0,9795.0;F=305.07/0.0125
def Rm(om,ph,ka):
    Rx=np.array([[1,0,0],[0,math.cos(om),-math.sin(om)],[0,math.sin(om),math.cos(om)]])
    Ry=np.array([[math.cos(ph),0,math.sin(ph)],[0,1,0],[-math.sin(ph),0,math.cos(ph)]])
    Rz=np.array([[math.cos(ka),-math.sin(ka),0],[math.sin(ka),math.cos(ka),0],[0,0,1]])
    return Rz@Ry@Rx   # camera->world
def proj(p,X):
    C=np.array(p[:3]);R=Rm(*p[3:6]);d=(np.atleast_2d(X)-C)@R   # world->camera coords
    # camera looks down -z; image x right, image y up
    u=U0+p[6]+F*d[:,0]/(-d[:,2]);v=V0+p[7]-F*d[:,1]/(-d[:,2])
    return np.stack([u,v],1)
def ray(p,u,v):
    R=Rm(*p[3:6]);dc=np.array([(u-U0-p[6])/F,-(v-V0-p[7])/F,-1.0]);w=R@dc;return w/np.linalg.norm(w)
def at_z(p,u,v,z=0.0):
    C=np.array(p[:3]);w=ray(p,u,v);t=(z-C[2])/w[2];return C+t*w
def P():return json.load(open('cam.json'))['p']
