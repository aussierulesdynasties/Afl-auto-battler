# draw polar tables (work/plan.json) on the GE orthographic top view; writes ge/ov_<quad>.png zoomed crops
import cv2,numpy as np,json,math,sys
S=0.3995919; im=cv2.imread('ge/top65.png'); P=json.load(open('work/plan.json')); C=np.zeros(2); CC=np.array(P['centre']); AX=math.radians(P['axis'])
def L2W(u,v): return (CC[0]+u*math.sin(AX)+v*math.cos(AX), CC[1]+u*math.cos(AX)-v*math.sin(AX))
def px(x,y): return (int(round(960+x/S)), int(round(540-y/S)))
def polar(tab,step=0.5):
    t=np.array(tab,float); t=np.r_[t[-1:]-[360,0],t,t[:1]+[360,0]]
    bs=np.arange(0,360+step,step); r=np.interp(bs,t[:,0],t[:,1]); a=np.radians(bs)
    return np.c_[C[0]+r*np.sin(a),C[1]+r*np.cos(a)]
g=im.copy()
for v in range(-200,201,10):
    x,_=px(v,0); cv2.line(g,(x,0),(x,1079),(0,90,160),1); _,y=px(0,v); cv2.line(g,(0,y),(1919,y),(0,90,160),1)
cols={'roof_outer':(0,0,255),'roof_inner':(0,255,0),'facade':(255,255,0)}
for k,c in cols.items():
    if k in P:
        pts=np.array([px(*p) for p in polar(P[k])],np.int32); cv2.polylines(g,[pts],True,c,1)
        for b,r in P[k]:
            a=math.radians(b); cv2.circle(g,px(C[0]+r*math.sin(a),C[1]+r*math.cos(a)),3,c,-1)
for T in P.get('towers',[]):
    cv2.circle(g,px(*T[:2]),int(T[2]/S),(255,128,0),1)
if 'roof_inner_local' in P:
    pts=np.array([px(*L2W(u,v)) for u,v in P['roof_inner_local']],np.int32); cv2.polylines(g,[pts],True,(0,255,0),1)
if 'fence' in P:
    x0,y0,a1,a2,rot=P['fence']; t=np.linspace(0,2*math.pi,400); r=math.radians(rot)
    pts=np.array([px(x0+a1*math.cos(q)*math.cos(r)-a2*math.sin(q)*math.sin(r), y0+a1*math.cos(q)*math.sin(r)+a2*math.sin(q)*math.cos(r)) for q in t],np.int32)
    cv2.polylines(g,[pts],True,(255,0,255),1)
if 'arch' in P:
    A=P['arch']
    for v in A['v']:
        for dv in (-A['width']/2,A['width']/2):
            cv2.line(g,px(*L2W(A['u_feet'][0],v+dv)),px(*L2W(A['u_feet'][1],v+dv)),(0,200,255),1)
cv2.imwrite('ge/ov_full.jpg',g)
q=sys.argv[1:] or ['nw','ne','sw','se']
for name in q:
    x0,y0={'nw':(-180,180),'ne':(-10,180),'sw':(-180,10),'se':(-10,10),'n':(-95,180),'s':(-95,10),'w':(-180,95),'e':(-10,95)}[name]
    a,b=px(x0,y0);c,d=px(x0+190,y0-190)
    crop=g[max(b,0):d,a:c]; crop=cv2.resize(crop,None,fx=1.6,fy=1.6,interpolation=cv2.INTER_NEAREST)
    for v in range(-200,201,50):
        for w in range(-200,201,50):
            X,Y=px(v,w)
            if a<=X<c and b<=Y<d: cv2.putText(crop,f'{v},{w}',(int((X-a)*1.6)+2,int((Y-max(b,0))*1.6)-3),0,0.45,(255,255,255),1)
    cv2.imwrite(f'ge/ov_{name}.png',crop)
