import numpy as np, math
f=582.0; yaw=math.radians(-142.3); pit=math.radians(6.0)
fw=np.array([math.cos(pit)*math.cos(yaw),math.cos(pit)*math.sin(yaw),math.sin(pit)]); rt=np.cross(fw,[0,0,1]); rt/=np.linalg.norm(rt); up=np.cross(rt,fw)
def ray(u,v): d=fw+rt*(u-400)/f+up*(300-v)/f; return d
def ground(u,v,h=0.0):   # offset from the eye (eye at z 1.6) to the ray's hit at height h
    d=ray(u,v); t=(h-1.6)/d[2]; return d*t
A=np.array([39.6-35.7,-111+123.6]); A/=np.linalg.norm(A); N=np.array([A[1],-A[0]])   # the shopfront direction; N points east (outward)
k=ground(800,520)[:2]           # kerb point
D=k@N                           # signed distance from the eye to the kerb line along N
# kerb line: the facade line (35.7,-123.6)+s*A, offset 3.3 m outward
P0=np.array([35.7,-123.6])+N*3.3
# R post base: put it at the canopy's NE corner (36.1, -130.5)
r=ground(457,452)[:2]
# eye = Rpost - r; but also satisfy the kerb distance: report both
E1=np.array([36.1,-130.5])-r
print('eye from R post',E1.round(2),' kerb check: eye-to-kerb-line',round((P0-E1)@N,2),'should be',round(D,2))
for (u,v) in [(232,430),(327,440),(457,452),(471,470)]: print((u,v),(E1+ground(u,v)[:2]).round(2))
print('target',(np.array([*E1,1.6])+fw*15).round(2))
E=np.array([*E1,1.6])
for (ub,vb),(ut,vt) in [((232,430),(210,245)),((327,440),(312,302)),((457,452),(437,180))]:
    B=E+ground(ub,vb); d=ray(ut,vt); h=d[:2]/np.linalg.norm(d[:2]); dist=np.linalg.norm((B-E)[:2]); z=1.6+d[2]*dist/np.linalg.norm(d[:2]); print('post at',B[:2].round(2),'top z',round(z,2))
# canopy soffit height at the M post and the fascia: the image point of the canopy front-edge at x 312 is y ~295
