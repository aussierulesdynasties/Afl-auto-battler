import json,numpy as np,cv2
from scipy.optimize import least_squares
c=json.load(open('cam_w04b.json'));K=np.array([[c['f'],0,c['w']/2],[0,c['f'],c['h']/2],[0,0,1.]])
R=cv2.Rodrigues(np.array(c['r']))[0];T=np.array(c['t']);C=-R.T@T
def ray(u,v):d=R.T@np.linalg.inv(K)@np.array([u,v,1.]);return d/np.linalg.norm(d)
def P(X):q,_=cv2.projectPoints(np.array([X],float),np.array(c['r']),np.array(c['t']),K,None);return q[0,0]
r1=ray(1111,372);r2=ray(970,316)
ridge_pts=[(1113,308),(1280,313)];eave_pts=[(1280,374)]
def line_res(A,d,pts):
    # distance in px from pts to the projected line through A along d
    a=P(A);b=P(A+40*d);n=np.array([-(b-a)[1],(b-a)[0]]);n/=np.linalg.norm(n)
    return [ (np.array(p)-a)@n for p in pts]
def res(x):
    l1,l2,th=x;A=C+l1*r1;B=C+l2*r2;d=np.array([np.cos(th),np.sin(th),0.])
    h=B-A;h[2]=0
    return [ (h@d)*5 ]+line_res(B,d,ridge_pts)+line_res(A,d,eave_pts)
for th0 in np.radians([80,95,105,115]):
    s=least_squares(res,[60,70,th0]);l1,l2,th=s.x;A=C+l1*r1;B=C+l2*r2
    print('th %.1f deg'%np.degrees(th),'res',np.round(s.fun,1),'corner',A.round(2),'apex',B.round(2),'halfdepth %.2f'%np.linalg.norm((B-A)[:2]))
st=json.load(open('stand.json'));print('stand a angle %.1f'%np.degrees(np.arctan2(st['a'][1],st['a'][0])),'club north angle %.1f'%np.degrees(np.arctan2(0.966,0.258)))
print('--- theta scan, bounded')
for thd in (50,55,60,65,70,75):
    th=np.radians(thd)
    f=lambda x:res([x[0],x[1],th])
    s=least_squares(f,[60,65],bounds=([35,35],[110,130]));l1,l2=s.x;A=C+l1*r1;B=C+l2*r2
    print(thd,'res',np.round(s.fun,1),'corner',A.round(1),'apex',B.round(1),'half %.1f'%np.linalg.norm((B-A)[:2]))
print('--- verge through (970,316), apex free')
def res2(x):
    l1,th,h,dz=x;A=C+l1*r1;d=np.array([np.cos(th),np.sin(th),0.]);n=np.array([-d[1],d[0],0.])
    if n[0]>0:n=-n
    B=A+h*n+np.array([0,0,dz])
    return line_res(A,B-A,[(970,316)])+line_res(B,d,ridge_pts)+line_res(A,d,eave_pts)
st=json.load(open('stand.json'));O=np.array(st['O']);a=np.array(st['a']);b=np.array(st['b'])
for l0 in (50,55,60,65,70):
  for th0 in (75,85,95):
    s=least_squares(res2,[l0,np.radians(th0),7,2.5],bounds=([35,np.radians(55),3,0.8],[110,np.radians(115),14,5]))
    l1,th,h,dz=s.x;A=C+l1*r1;dd=A[:2]-O
    print(l0,th0,'res',np.round(s.fun,1),'th %.1f h %.1f dz %.2f pitch %.0f'%(np.degrees(th),h,dz,np.degrees(np.arctan(dz/h))),'corner s %.1f t %.1f z %.2f'%(dd@a,dd@b,A[2]))
