# overlay: model roof edges (all stands), towers and pitch outline projected with a camera json onto its photo
import io,contextlib,sys
with contextlib.redirect_stdout(io.StringIO()):exec(open('geo.py').read())
import cv2
cj=json.load(open(sys.argv[1]));p=cj['p'];im=cv2.imread(cj.get('img','refs/scg.jpg'));PCc=np.array([0.94,-11.82])
def pl(X,c,t=2):
    X=np.array(X);ok=((X-np.array(p[:3]))@R(*p[3:6])[2])>1
    pp=proj(p,X)
    for i in range(len(pp)-1):
        if ok[i] and ok[i+1]:cv2.line(im,tuple(int(v) for v in pp[i]),tuple(int(v) for v in pp[i+1]),c,t)
for st in STANDS:
    ks=sorted(d for d,v in OUT.items() if v[4]==st)
    o=[];i_=[];b=[]
    for d in ks:
        lo_,hi_,zf,zo,s=OUT[d];a=math.radians(d);u=np.array([math.cos(a),math.sin(a)]);o.append([*(PCc+hi_*u),zo]);i_.append([*(PCc+lo_*u),zf]);b.append([*(PCc+hi_*u),0])
    pl(o,(0,0,255));pl(i_,(0,255,255));pl(b,(255,0,255),1)
for t in TW:pl([[*t,0],[*t,68.09]],(255,0,0),3)
pl(np.c_[dens(G['4000006'],3),np.zeros(len(dens(G['4000006'],3)))],(0,255,0),1)
cv2.imwrite(sys.argv[2],im)
