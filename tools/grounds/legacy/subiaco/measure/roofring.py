# roofring.py IMG OUT.json : roof front and back radii by bearing (bright roof annulus beyond the fence)
import sys,cv2,numpy as np,json
sys.path.insert(0,'/home/user/work/subi/photo'); from camsolve import fr
g=cv2.GaussianBlur(cv2.imread(sys.argv[1]).astype(np.float32).mean(2),(0,0),1.2)
S=0.2945; out=[]
for a in np.arange(0,360,0.5):
    t=np.radians(a); rf=fr(np.array([a]))[0]
    rs=np.arange(rf,rf+75,0.15); px=941+rs*np.cos(t)/S; py=1021-rs*np.sin(t)/S
    v=cv2.remap(g,px.astype(np.float32)[None],py.astype(np.float32)[None],cv2.INTER_LINEAR)[0]
    br=v>float(sys.argv[3]) if len(sys.argv)>3 else v>150
    # longest bright run (allow 0.6 m gaps)
    runs=[];i=0;n=len(br)
    while i<n:
        if br[i]:
            j=i;gap=0
            while j<n and gap<=4: gap=0 if br[j] else gap+1; j+=1
            runs.append((i,j-gap-1)); i=j
        else: i+=1
    if not runs: out.append([float(a),None,None]); continue
    good=[r for r in runs if (r[1]-r[0])*0.15>=4 and rs[r[0]]-rf<35]
    if not good: out.append([float(a),None,None]); continue
    i0,i1=good[0]
    out.append([float(a),float(rs[i0]-rf),float(rs[i1]-rf)])
json.dump(out,open(sys.argv[2],'w'))
d=np.array([[o[0],o[1] or np.nan,o[2] or np.nan] for o in out])
for a in range(0,360,15):
    k=int(a*2); print(a,'front %.1f back %.1f'%(d[k,1],d[k,2]))
