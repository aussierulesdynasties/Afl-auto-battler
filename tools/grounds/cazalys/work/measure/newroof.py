import sys,json,math,numpy as np
from scipy.optimize import least_squares
sys.path.insert(0,'of'); import zline as Z
v=Z.NV['sC']
def inv(px,z): return least_squares(lambda p: Z.nproj(v,p[0],p[1],z)-np.array(px),[-80,-48]).x
C={'FL':11.4,'FK':11.6,'FR':11.9,'RR':11.75,'RK':12.0,'B2':12.0,'B1':11.9}
XY={k:Z.xy_at(k,C[k]) for k in C}; XY['LR']=np.array([-63.02,-62.2])
A=np.array([[*XY[k],1] for k in C]); z=np.array(list(C.values())); pl=np.linalg.lstsq(A,z,rcond=None)[0]; res=A@pl-z
print('plane',pl.round(5),'resid',dict(zip(C,res.round(2))),'rms %.2f'%np.sqrt((res**2).mean()))
zr=lambda p: float(pl[0]*p[0]+pl[1]*p[1]+pl[2])
order=['FR','RR','RK','B2','B1','LR','FL','FK']
poly=[XY[k].round(2).tolist() for k in order]
AP={'L':[-67.05,-64.94,14.5],'C':[-79.54,-47.11,14.68],'R':[-87.4,-28.12,14.52]}
FE={'L':[(490,382.5),(520,465),(335,270),(380,482.5)],'C':[(527.5,380),(757.5,381),(520,465),(760,465),(642.5,235),(640,452.5)],
    'R':[(787.5,385),(760,465),(950,275),(897.5,485)]}
frames=[]
for k in ('R','C','L'):
    feet=[]
    for px in FE[k]:
        q=inv(px,12.0); q=inv(px,zr(q)); feet.append(q.round(2).tolist())
    frames.append({'apex':AP[k],'feet':feet})
w0=inv((578,110),12.0); w1=inv((628,455),12.0); cg=inv((597,480),12.0)
out={'_':'Measured 2026-11-22 (Cazaly\'s rebuild, shape-first pass): corners from three GE top-down views (d=130 m) at the heights read off two GE obliques whose cameras were solved from the painted field lines (0.7 px rms); each corner 11.4-12.0 m, +-0.4 m. The sheet is the plane through the measured corners (rms %.2f m), folded in plan at FK-RK; ribs run square to each panel\'s front. Tie frames: apexes triangulated (nadir + solved oblique, <1 px; L from the oblique alone), feet from the top-down view on the sheet.'%np.sqrt((res**2).mean()),
     'poly':poly,'front':[XY[k].round(2).tolist() for k in ('FL','FK','FR')],'fold':[XY['FK'].round(2).tolist(),XY['RK'].round(2).tolist()],
     'plane':[round(float(x),5) for x in pl],'frames':frames,'walkway':[w0.round(2).tolist(),w1.round(2).tolist()],'cage':[cg.round(2).tolist(),[4.8,3.0,1.3]],
     'block':[XY[k].round(2).tolist() for k in ('RK','B2','B1')]}
json.dump(out,open('rf/roof.json','w'),indent=1); print(json.dumps(out)[:3000])
