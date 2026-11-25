# Solve a GE capture's camera from the painted field lines: ICP along the projected line normals.
import os
import sys,json,math,numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as nd
from scipy.optimize import least_squares
sys.path.insert(0,'of'); import solve as S
def segs():
    # model lines as separate polylines so tangents are right
    import solve
    cx,cy,a,b,r=S.BL; r=math.radians(r); ua=np.array([math.cos(r),math.sin(r)]); ub=np.array([-math.sin(r),math.cos(r)]); c=np.array([cx,cy])
    out=[]; t=np.linspace(0,2*np.pi,2880,endpoint=False); out.append(c+np.outer(a*np.cos(t),ua)+np.outer(b*np.sin(t),ub))
    def inside(Q): q=Q-c; return (q@ua/a)**2+(q@ub/b)**2<0.99
    for s in (1,-1):
        G=c+s*b*ub; t=np.linspace(0,2*np.pi,1440,endpoint=False); Q=G+50*np.stack([np.cos(t),np.sin(t)],1); out.append(Q[inside(Q)])
    s=np.linspace(-25,25,250)
    for k in (-25,25): out.append(c+np.outer(s,ua)+k*ub); out.append(c+k*ua+np.outer(s,ub))
    for sg in (1,-1):   # goal squares: 6.4 m wide, 9 m deep from the goal line
        G=c+sg*b*ub; w=np.linspace(-3.2,3.2,40); dd=np.linspace(0,9,50)
        out.append(G+np.outer(w,ua)-sg*9*ub); out.append(G+3.2*ua-sg*np.outer(dd,ub)); out.append(G-3.2*ua-sg*np.outer(dd,ub))
    return [np.c_[q,np.zeros(len(q))] for q in out]
GE=os.environ.get('GE','of/ge') if 'os' in dir() else 'of/ge'
RS=tuple(int(x) for x in os.environ.get('RS','30,20,12,8,5,5').split(','))
SEG=segs()
import os; VT=float(os.environ.get("VT","6"))
def resp(im):
    a=np.asarray(im,float); bl=a[...,2]; g=a.mean(2)
    th=bl-nd.grey_opening(bl,size=(7,7)); th2=g-nd.grey_opening(g,size=(7,7))
    gr=(a[...,1]>a[...,0]+2)&(a[...,1]>a[...,2]+8)
    gf=nd.uniform_filter(gr.astype(float),13)
    return nd.gaussian_filter(np.minimum(th,th2),0.7)*(gf>0.55)
def matches(p,R,rs):
    out=[]
    for P in SEG:
        uv,z=S.proj(p,P); tg=np.gradient(uv,axis=0); n=np.stack([-tg[:,1],tg[:,0]],1); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-9
        ok=(z>0)&(uv[:,0]>R+5)&(uv[:,0]<1275-R)&(uv[:,1]>65+R)&(uv[:,1]<715-R)
        k=np.arange(-R,R+0.01,0.5)
        for i in np.where(ok)[0][::2]:
            q=uv[i]+np.outer(k,n[i]); v=nd.map_coordinates(rs,[q[:,1],q[:,0]],order=1)
            j=v.argmax()
            if v[j]>VT and 0<j<len(k)-1: out.append((P[i],q[j],n[i]))
    return out
def solve(name,p0):
    im=Image.open(GE+'/{}.png'.format(name)).convert('RGB'); rs=resp(im); p=np.array(p0,float)
    for R in RS:
        M=matches(p,R,rs); X=np.array([m[0] for m in M]); Y=np.array([m[1] for m in M]); N=np.array([m[2] for m in M])
        f=lambda q: np.sum((S.proj(q,X)[0]-Y)*N,1)
        sol=least_squares(f,p,loss='huber',f_scale=1.5,x_scale=[1,1,1,.01,.01,.01]); p=sol.x
        r=f(p); inl=np.abs(r)<3
        print(f' {name} R{R} n{len(M)} inl {inl.mean():.0%} rms {np.sqrt((r[inl]**2).mean()):.2f}px')
    o=im.copy(); dr=ImageDraw.Draw(o)
    for P in SEG:
        uv,z=S.proj(p,P); dr.line([tuple(q) for q,zz in zip(uv,z) if zz>0],fill=(0,255,255),width=1)
    for y in Y[inl]: dr.point(tuple(y),fill=(255,0,255))
    o.save(GE+'/../{}_sol.png'.format(name)); return p,np.sqrt((r[inl]**2).mean())
if __name__=='__main__':
    V={v['name']:v for v in json.load(open(sys.argv[1]))}; out={}
    for k in sys.argv[2:]:
        p0=S.init(V[k]); p,rms=solve(k,p0); out[k]=dict(p=list(map(float,p)),rms=float(rms))
        print(k,'dC',np.round(p[:3]-p0[:3],1),'dang',np.round(np.degrees(p[3:]-p0[3:]),2))
    json.dump(out,open(sys.argv[1].replace('v.json','solved.json'),'w'),indent=1)
