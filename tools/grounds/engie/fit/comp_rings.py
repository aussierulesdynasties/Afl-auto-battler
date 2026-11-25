import os
import numpy as np, json, math, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'composite.py')).read().split('OUT={}')[0])
A=json.load(open('arcs.json'))
def arc_r(key,nm,b):
    a=A['%s_%s'%(key,nm)]
    if 'corner' in a and (b%360)<a['corner']['bk']: a=a['corner']   # the east roof front's second arc (corner_arc.py)
    c=np.array(a['c']); R=a['R']
    u=np.array([math.sin(math.radians(b)),math.cos(math.radians(b))])
    # ray s*u hits circle |s u - c| = R: s^2 - 2 s u.c + |c|^2 - R^2 = 0, take the far root
    uc=u@c; disc=uc*uc-(c@c-R*R); return uc+math.sqrt(max(disc,0))
bowlF,bowlB=offset_polar(dF),offset_polar(dB)
_fp=json.load(open('fit.json'))['field']; _q=np.array(_fp['p']); _K=_fp['K']
def bowl0(b):
    # the field edge curve's radius along bearing b (polar about its own centre, resampled about the origin)
    t=np.linspace(0,2*np.pi,14400,endpoint=False); r=_q[2]+sum(_q[2+2*k-1]*np.cos(k*t)+_q[2+2*k]*np.sin(k*t) for k in range(1,_K+1))
    x=_q[0]+r*np.sin(t); y=_q[1]+r*np.cos(t); bb=np.degrees(np.arctan2(x,y))%360; rr=np.hypot(x,y); o=np.argsort(bb)
    return float(np.interp(b%360,np.r_[bb[o]-360,bb[o],bb[o]+360],np.r_[rr[o],rr[o],rr[o]]))
def ring(key,b):
    b=b%360; bowl=bowlF if key=='rf' else bowlB
    jN=A['%s_N'%key]['bj']; jE=A['%s_E'%key]['bj']
    if b>=jN or b<=3.0: return arc_r(key,'N',b)
    if 77.0<=b<=jE: return arc_r(key,'E',b)
    if 3.0<b<77.0:   # the open north-east end has no roof: a filler that carries both arcs on and eases from one
        t=(b-3.0)/74.0; w=t*t*(3-2*t); return (1-w)*arc_r(key,'N',b)+w*arc_r(key,'E',b)   # to the other (no kink)
    return bowl(b)
STAND_IN=1.6
if __name__=='__main__':
    E=json.load(open('edges_true.json'))
    ST={'N 2012':(315.3,363),'E 2012':(84,135.4),'E 2012 north corner':(77,84),'SE':(141.4,172.2),'S':(178.2,205.8),'SW':(211.8,239.3),'W':(245.3,272.3),'NW':(278.3,309.3)}
    for key in ('rf','rb'):
        a=np.array(E[key])
        for nm,(lo,hi) in ST.items():
            m=((a[:,0]-lo)%360)<=((hi-lo)%360); 
            if not m.any(): continue
            r=np.array([a[i,1]-ring(key,a[i,0]) for i in np.where(m)[0]]); k=np.abs(r)<4
            print('%s %-20s n=%3d rms %.2f 95%% %.2f max %.2f  (%d mistraces >4 m)'%(key,nm,k.sum(),np.sqrt((r[k]**2).mean()),np.percentile(np.abs(r[k]),95),np.abs(r[k]).max(),(~k).sum()))
    # radial residual is close to normal distance for these near-circular rings
    P=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'model', 'engie.json'); D=json.load(open(P))
    q=np.arange(0,360,1.0)
    D['fence']=[[float(b),round(bowl0(b),2)] for b in q]
    D['rf']=[[float(b),round(ring('rf',b),2)] for b in q]
    D['rb']=[[float(b),round(ring('rb',b),2)] for b in q]
    D['stand_front']=[[float(b),round(ring('rf',b)-STAND_IN,2)] for b in q]
    fit=json.load(open('fit.json'))
    D['outline']={'_note':'The field edge: a 5-harmonic polar curve fitted to the turf edge in Google Earth top-down, sunlit (east, south) and traced in the shade (west, north; fieldshadow.py) (field). Between the roofs at the open north-east end (3 to 77 deg) rf and rb are a filler run with no roof over it. The 1998 bowl: one smooth curve (6-harmonic polar series about (cx, cy), t clockwise from north) fitted to its roof front; its roof back is an exact normal offset. The 2012 north and east stands: each roof edge a circular arc of its own, joined tangentially to the bowl ring at bj (degrees); the east roof front is two arcs, the second (corner) tangent to the first at bk. The stand front is the roof front ring 1.6 m in, everywhere. tools/grounds/engie/fit.',
        'cx':fit['p'][0],'cy':fit['p'][1],'K':fit['K'],'coef':fit['p'][2:3+2*fit['K']],'offsets':{'roof_front':round(dF,2),'roof_back':round(dB,2),'stand_front_from_roof_front':-STAND_IN},'arcs':A,'field':_fp}
    json.dump(D,open(P,'w'),indent=1)
