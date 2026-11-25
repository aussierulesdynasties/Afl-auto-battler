import sys,json,math,numpy as np
from scipy.optimize import least_squares
sys.path.insert(0,'of'); import zline as Z, solve as S
sys.path.insert(0,'/home/user/Afl-auto-battler/tools/grounds/cazalys/work'); import fence_ge as fg
E=[-1.2135,-3.69,75.22,87.49,28.87]
c=lambda X,Y,y0=230: (400+X/3, y0+Y/3)
PTS={'tunnel top':(c(765,180),c(765,120)),'L stair top':(c(320,195),c(320,130)),'seat top R':(c(1000,185),c(1000,130)),
     'seat front R':(c(1000,345),c(1000,315)),'seat top L2':(c(150,200),c(150,140)),'R stair top':(c(1200,180),c(1200,120))}
P={k:np.array(Z.SOL[k]['p']) for k in ('of_gs','of_gs50')}
for k,(a,b) in PTS.items():
    f=lambda q: np.r_[S.proj(P['of_gs'],q[None])[0][0]-a, S.proj(P['of_gs50'],q[None])[0][0]-b]
    r=least_squares(f,[-70,-45,5.0]); q=r.x; J=r.jac; cov=np.linalg.pinv(J.T@J)*1.0
    b_=math.degrees(math.atan2(q[0],q[1]))%360; rr=math.hypot(q[0],q[1]); d=fg.dist(E,q[None,:2])[0]
    print(f'{k:14s} b {b_:6.1f} r {rr:6.2f} past fence {d:5.2f} z {q[2]:5.2f} +-{math.sqrt(cov[2,2]):.2f} (1px)  resid {np.abs(r.fun).max():.1f}px')
