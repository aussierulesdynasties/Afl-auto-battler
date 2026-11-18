import json,math,os
_c=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'cam92f.json')))
p=_c['p'];C=p[:3];yaw,pit,rol=p[3:6];FO=p[6];CX,CY=_c['cx'],_c['cy']
cy,sy,cp,sp,cr,sr=math.cos(yaw),math.sin(yaw),math.cos(pit),math.sin(pit),math.cos(rol),math.sin(rol)
F=(cy*cp,sy*cp,sp);R=(sy,-cy,0.0)
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dot(a,b):return sum(x*y for x,y in zip(a,b))
U=cross(R,F)
RI=tuple(cr*R[i]+sr*U[i] for i in range(3));UI=tuple(-sr*R[i]+cr*U[i] for i in range(3))
def proj(x,y,z):
    d=(x-C[0],y-C[1],z-C[2]);d2=dot(d,F);return (CX+FO*dot(d,RI)/d2,CY-FO*dot(d,UI)/d2)
def ray(u,v):
    a=(u-CX)/FO;b=-(v-CY)/FO;return tuple(F[i]+a*RI[i]+b*UI[i] for i in range(3))
def at_z(u,v,z):
    r=ray(u,v);t=(z-C[2])/r[2];return (C[0]+t*r[0],C[1]+t*r[1],z)
def at_plane(u,v,x0,y0,x1,y1):
    # vertical plane through (x0,y0)-(x1,y1)
    r=ray(u,v);nx,ny=-(y1-y0),(x1-x0)
    t=((x0-C[0])*nx+(y0-C[1])*ny)/(r[0]*nx+r[1]*ny);return (C[0]+t*r[0],C[1]+t*r[1],C[2]+t*r[2])
