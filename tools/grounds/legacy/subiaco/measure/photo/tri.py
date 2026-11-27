import numpy as np
import camsolve as cs, ptsolve as ps
q1=np.load('cam8n_50_NE.npy'); q2=np.load('cam_fa_E.npy')
def und(x0,y0,k,F):
    x,y=x0,y0
    for _ in range(10): s=1+k*(x*x+y*y)*(F/1200)**2; x,y=x0/s,y0/s
    return x,y
def ray1(u,v):
    c=cs.campos(q1); f,rr,uu=cs.Rm(*q1[3:6]); F=q1[6]; x,y=und((u-960)/F,-(v-720)/F,q1[8],F); d=f+x*rr+y*uu; return c,d/np.linalg.norm(d)
def ray2(u,v):
    q=q2; f,rr,uu=ps.Rm(*q[3:6]); F=q[6]; x,y=und((u-960)/F,-(v-720)/F,q[7],F); d=f+x*rr+y*uu; return q[:3].copy(),d/np.linalg.norm(d)
def tri(a,b):
    (c1,d1),(c2,d2)=ray1(*a),ray2(*b); A=np.array([d1,-d2]).T; t,*_=np.linalg.lstsq(A,c2-c1,rcond=None)
    p1=c1+t[0]*d1;p2=c2+t[1]*d2; return (p1+p2)/2,np.linalg.norm(p1-p2)
def m2px(P): return 941+P[0]/0.2945, 1021-P[1]/0.2945
if __name__=='__main__':
    pts={'TL':((417,607),(1236,211)),'TR':((496,607),(1305,211)),'BL':((418,656),(1236,267)),'BR':((496,656),(1305,267))}
    P={}
    for k,(a,b) in pts.items():
        p,g=tri(a,b); P[k]=p; print(k,np.round(p,2),'gap %.2f m'%g,'aerial px',np.round(m2px(p),1))
    print('width',np.linalg.norm(P['TR']-P['TL']),'height',P['TL'][2]-P['BL'][2])
