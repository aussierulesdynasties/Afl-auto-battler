import numpy as np,json,math,sys
D=json.load(open('geo_build.json'));RG=np.array(D['RG'])
def rg(a):f=(a%360)*4;i=int(f)%1440;t=f-int(f);return RG[i]*(1-t)+RG[(i+1)%1440]*t
def R(yaw,p_,roll):
    cy,sy,cp,sp,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(p_),np.sin(p_),np.cos(roll),np.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f);return np.array([cr*r+sr*u,-sr*r+cr*u,f])
prof=[(1.5,1.0),(6.5,4.0),(8.5,4.0),(8.5,6.0),(18.0,12.7),(18.0,15.2)]
L=np.cumsum([0]+[math.hypot(prof[i+1][0]-prof[i][0],prof[i+1][1]-prof[i][1]) for i in range(len(prof)-1)])
def pt(a,row):
    s=row/30;k=min(np.searchsorted(L,s,side='right')-1,len(prof)-2);t=(s-L[k])/(L[k+1]-L[k])
    d=prof[k][0]+(prof[k+1][0]-prof[k][0])*t;z=prof[k][1]+(prof[k+1][1]-prof[k][1])*t
    r=rg(a)+d;return np.array([r*math.cos(math.radians(a)),r*math.sin(math.radians(a)),z])
def ray(cam,X,W,H):
    p=json.load(open(cam))['p'];Rm=R(*p[3:6]);d=(X-p[:3])@Rm.T;u=W/2+p[6]*d[0]/d[2];v=H/2-p[6]*d[1]/d[2]
    dirc=np.array([(u-W/2)/p[6],-(v-H/2)/p[6],1.0]);w=Rm.T@dirc;return np.array(p[:3]),w/np.linalg.norm(w),(u,v)
def tri(o1,d1,o2,d2):
    A=np.c_[d1,-d2];t=np.linalg.lstsq(A,o2-o1,rcond=None)[0];P1=o1+t[0]*d1;P2=o2+t[1]*d2;return (P1+P2)/2,np.linalg.norm(P1-P2)
if __name__=='__main__':
    a1,r1,a2,r2=map(float,sys.argv[1:5]);w0cam=sys.argv[5] if len(sys.argv)>5 else 'sf3.json'
    o1,d1,uv1=ray('cam.json',pt(a1,r1),2000,1333);o2,d2,uv2=ray(w0cam,pt(a2,r2),2000,1333)
    P,e=tri(o1,d1,o2,d2);a=math.degrees(math.atan2(P[1],P[0]))%360;r=math.hypot(P[0],P[1])
    print('px main',np.round(uv1,1),'w0',np.round(uv2,1));print('P',np.round(P,2),'gap',round(e,2),'ang',round(a,2),'d from RG',round(r-rg(a),2),'z',round(P[2],2))
    print('model point main',np.round(pt(a1,r1),2))
