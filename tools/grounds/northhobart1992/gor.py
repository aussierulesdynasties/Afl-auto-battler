# Horrie Gorringe Stand (Argyle St), 1992 form. Local frame: x along the field facade SE->NW (0..41 m, roof ends),
# y back from the front eave toward Argyle St, z up. Sources: aerial 1182_185 (plan, valleys, ridges), hr_gor (facade heights),
# 1992 broadcast frames (open upper deck), 2009 photo (posts, end gables).
import numpy as np
GOR_F0=(-59.09,-75.66);GOR_AX=(-0.6672,0.7448);GOR_NY=(-0.7448,-0.6672)
P_F=P_R=0.348; RH,WH=12.3,10.7  # one 19.2 deg pitch all round: every eave 9.2, main ridge 12.3 (fitted to hr_gor), wing/end ridges 10.7
def yA(x):return 8.46+(x-3.76)*(1.17/33.34)
def yR(x):return 24.46+(x-0.1)*(18.81-24.46)/41.22      # Argyle St rear wall (slants)
XS,XN=4.2,37.6;XK=[12.34,20.6,28.9]
DORM=[(9.49,1.1,11.0,9.7,2.6),(20.68,1.4,11.45,9.9,3.4),(31.52,1.1,11.0,9.7,2.6)]   # x, pediment setback, apex, base, half-width
FY=1.0
PIL=[(0.0,0.9),(5.97,7.20),(11.75,12.91),(28.64,29.95),(34.33,35.42),(40.1,41.0)]
STAIRS=[(3.3,5.4,-1),(9.1,11.4,1),(30.9,32.6,-1)]
ENT=(16.98,24.31);DOOR=(19.4,20.9)
PO=[0.76,6.47,12.38,17.4,23.9,29.3,34.9,40.4]
def roofz(x,y):
    f=9.2+P_F*y;r=RH-P_R*(y-yA(x))
    z=min(f,r) if XS<=x<=XN else -1e9
    ws=WH-P_F*abs(XS-x)
    wn=WH-P_F*abs(x-XN)
    z=max(z,min(f,ws),min(f,wn))
    if y>=yA(x):
        for xk in XK:z=max(z,WH-P_R*abs(x-xk))
    for xg,yp,ap,ba,hw in DORM:
        if y>=yp and abs(x-xg)<=hw:z=max(z,ap-(ap-ba)/hw*abs(x-xg))
    return z
def roofunder(x,y):return roofz(x,y)-0.22
def gor_build(addobj):
    xs=sorted(set([round(float(v),3) for v in list(np.arange(0,41.0001,0.1))+[XS,XN,XS-0.005,XN+0.005,8.27,16.47,24.75,33.25]+XK+[d[0] for d in DORM]+[d[0]+s*d[4] for d in DORM for s in(-1,1)]]))
    nt=246
    def ycol(x):
        ys=list(np.linspace(0,1,nt)*yR(x))
        for d in DORM:ys+= [d[1]-0.005,d[1]]
        return sorted(ys)
    roof=[[(x,y,roofz(x,y)) for y in ycol(x)] for x in xs]
    nt=len(roof[0])
    dn=lambda p:(p[0],p[1],p[2]-0.22)
    addgrid('gor_roof',roof,'roof_iron',steep='pediment');addgrid('gor_ceiling',roof,'ceiling',flip=True,dz=-0.22)
    E=[]
    def skirt(P,mat):
        for k in range(len(P)-1):
            a,b=P[k],P[k+1];E.append(([dn(a),dn(b),b,a],mat))
    skirt([r[0] for r in roof][::-1],'fascia');skirt([r[-1] for r in roof],'fascia')
    skirt(roof[0],'fascia');skirt(roof[-1][::-1],'fascia')
    E.append(([(0,0.02,8.5),(41,0.02,8.5),(41,0.02,8.98),(0,0.02,8.98)],'fascia'))
    E.append(([(0,0.02,8.5),(0,FY,8.5),(41,FY,8.5),(41,0.02,8.5)],'fascia'))
    addobj('gor_fascia',E,double=True)
    Wl=[]
    def quad(p0,p1,z0,z1,mat):
        Wl.append(([(p0[0],p0[1],z0),(p1[0],p1[1],z0),(p1[0],p1[1],z1),(p0[0],p0[1],z1)],mat))
    def box(x0,x1,y0,y1,z0,z1,mat,top=None):
        quad((x0,y0),(x1,y0),z0,z1,mat);quad((x1,y0),(x1,y1),z0,z1,mat);quad((x1,y1),(x0,y1),z0,z1,mat);quad((x0,y1),(x0,y0),z0,z1,mat)
        Wl.append(([(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],top or mat))
    cuts=sorted([(a,b) for a,b,_ in STAIRS]+[ENT])
    x=0.0
    for a,b in cuts+[(41.0,41.0)]:
        if a>x:quad((x,FY),(a,FY),0,2.4,'brick')
        x=b
    for a,b,_ in STAIRS:quad((a,FY),(b,FY),2.2,2.4,'render_cream')
    box(0,41,FY,FY+0.3,2.4,2.55,'render_cream')
    for a,b in PIL:box(a,b,FY-0.3,FY,0,3.1,'render_cream');box(a-0.06,b+0.06,FY-0.36,FY+0.06,3.1,3.25,'render_cream')
    e0,e1=ENT
    quad((e0,FY-0.4),(DOOR[0],FY-0.4),0,3.1,'render_cream');quad((DOOR[1],FY-0.4),(e1,FY-0.4),0,3.1,'render_cream')
    quad((DOOR[0],FY-0.4),(DOOR[1],FY-0.4),2.0,3.1,'render_cream')
    quad((DOOR[0],FY-0.3),(DOOR[1],FY-0.3),0,2.0,'interior_dark')
    quad((e1,FY-0.4),(e1,FY),0,3.1,'render_cream');quad((e0,FY),(e0,FY-0.4),0,3.1,'render_cream')
    box(e0-0.06,e1+0.06,FY-0.46,FY+0.06,3.1,3.3,'render_cream')
    _w=e1-e0;addobj('gor_sign',[([(e0+0.19*_w,FY-0.47,2.25),(e0+0.82*_w,FY-0.47,2.25),(e0+0.82*_w,FY-0.47,2.8),(e0+0.19*_w,FY-0.47,2.8)],'club_sign_lettered')],double=True,uvfit=True)
    for a,b,dr in STAIRS:
        n=11;run=(b-a)/n
        for k in range(n):
            xa=a+k*run if dr>0 else b-(k+1)*run;xb=xa+run;z=0.2*(k+1)
            Wl.append(([(xa,FY,z),(xb,FY,z),(xb,FY+1.2,z),(xa,FY+1.2,z)],'concrete'))
            if dr>0:quad((xa,FY+1.2),(xa,FY),z-0.2,z,'concrete')
            else:quad((xb,FY),(xb,FY+1.2),z-0.2,z,'concrete')
        quad((b,FY+1.2),(a,FY+1.2),0,2.4,'brick')
        quad((a,FY),(a,FY+1.2),0,2.4,'brick');quad((b,FY+1.2),(b,FY),0,2.4,'brick')
    AIS=[((a+b)/2-0.6,(a+b)/2+0.6) for a,b in PIL[1:-1]]+[(ENT[0],ENT[0]+1.2),(ENT[1]-1.2,ENT[1])]
    y0=FY+0.3;z0=2.55
    for r in range(14):
        ya,yb=y0+r*0.8,y0+(r+1)*0.8;zr=z0+(r+1)*0.36
        quad((0.6,ya),(40.4,ya),zr-0.36,zr,'concrete')
        Wl.append(([(0.6,ya,zr),(40.4,ya,zr),(40.4,yb,zr),(0.6,yb,zr)],'concrete'))
        segs=[];x=0.6
        for a,b in sorted(AIS):
            if a>x:segs.append((x,a))
            x=b
        segs.append((x,40.4))
        for a,b in segs:box(a,b,ya+0.3,ya+0.7,zr,zr+0.45,'seats',top='seats_top')
    yb_=y0+14*0.8;zt=z0+14*0.36
    for k in range(40):
        xa,xb=0.6+k*0.995,0.6+(k+1)*0.995
        Wl.append(([(xa,yb_,zt),(xb,yb_,zt),(xb,yb_,roofunder(xb,yb_)),(xa,yb_,roofunder(xa,yb_))],'render_cream'))
    for xe,sg in((0.6,-1),(40.4,1)):
        n=30;ys=np.linspace(FY,yR(xe),n)
        for k in range(n-1):
            za,zb=roofunder(xe,ys[k]),roofunder(xe,ys[k+1])
            lo=[(xe,ys[k],0),(xe,ys[k+1],0),(xe,ys[k+1],2.4),(xe,ys[k],2.4)]
            hi=[(xe,ys[k],2.4),(xe,ys[k+1],2.4),(xe,ys[k+1],zb),(xe,ys[k],za)]
            if sg<0:lo,hi=lo[::-1],hi[::-1]
            Wl.append((lo,'brick'));Wl.append((hi,'render_cream'))
    n=82;xr=np.linspace(0.6,40.4,n)
    for k in range(n-1):
        a,b=(xr[k],yR(xr[k])),(xr[k+1],yR(xr[k+1]))
        Wl.append(([(a[0],a[1],0),(b[0],b[1],0),(b[0],b[1],roofunder(b[0],b[1])),(a[0],a[1],roofunder(a[0],a[1]))],'brick'))
    addobj('gor_walls',Wl,double=True)
    Pl=[]
    for px in PO:
        c=[(px-.125,FY-.125),(px+.125,FY-.125),(px+.125,FY+.125),(px-.125,FY+.125)]
        for k in range(4):
            p0,p1=c[k],c[(k+1)%4];Pl.append(([(p0[0],p0[1],3.25),(p1[0],p1[1],3.25),(p1[0],p1[1],8.5),(p0[0],p0[1],8.5)],'post_maroon'))
    addobj('gor_posts',Pl,double=True)
    Bl=[]   # white barge boards on each gable rake (photo), 0.25 m deep, standing 0.06 proud; finials on the outer gables
    for k,(xg,yp,ap,ba,hw) in enumerate(DORM):
        yb=yp-0.06
        for s in(-1,1):
            x0,x1=xg+s*hw,xg;z0,z1=ba,ap
            Bl.append(([(x0,yb,z0-0.25),(x1,yb,z1-0.25),(x1,yb,z1),(x0,yb,z0)],'trim_white'))
            Bl.append(([(x0,yb,z0),(x1,yb,z1),(x1,yp+0.1,z1+0.04),(x0,yp+0.1,z0+0.04)],'trim_white'))
        if k!=1:
            for a_,b_ in(((-.05,-.05),(.05,-.05)),((.05,-.05),(.05,.05)),((.05,.05),(-.05,.05)),((-.05,.05),(-.05,-.05))):
                Bl.append(([(xg+a_[0],yb+a_[1],ap),(xg+b_[0],yb+b_[1],ap),(xg+b_[0],yb+b_[1],ap+0.55),(xg+a_[0],yb+a_[1],ap+0.55)],'trim_white'))
    addobj('gor_barge',Bl,double=True)
    xg,yp,ap,ba,hw=DORM[1];c=0.75;zc=10.6;yc=yp-0.03
    addobj('gor_clock',[([(xg-c,yc,zc-c),(xg+c,yc,zc-c),(xg+c,yc,zc+c),(xg-c,yc,zc+c)],'clock')],uvfit=True,double=True)
