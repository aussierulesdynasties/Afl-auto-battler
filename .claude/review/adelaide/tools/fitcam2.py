import sys;sys.argv=['x'];exec(open('tools/fitcam.py').read().split("if __name__")[0])
import itertools
for cxy in [(1109.5,315.0),(905.5,628.5)]:
    best=[]
    for perm in itertools.permutations(OT):
        lab=dict(zip('ABCD',perm))
        for yaw0 in np.radians(np.arange(0,360,30)):
            fwd=np.array([math.cos(yaw0),math.sin(yaw0)]);C0=-fwd*600
            f=lambda q,lab=lab:res(np.r_[q,cxy],lab)
            s=least_squares(f,[C0[0],C0[1],350,yaw0,-0.5,0,1800],bounds=([-5e3,-5e3,30,-20,-1.5,-0.3,300],[5e3,5e3,3000,20,0.2,0.3,20000]))
            best.append((math.sqrt((s.fun**2).mean()),perm,list(s.x)+list(cxy)))
    best.sort(key=lambda z:z[0]);b=best[0]
    print(cxy,round(b[0],2),[str(x)[-2:] for x in b[1]],[round(v,3) for v in b[2]])
    print(np.round(res(np.array(b[2]),dict(zip('ABCD',b[1]))),1))
    json.dump({'p':b[2],'lab':dict(zip('ABCD',b[1]))},open('cam_%d.json'%int(cxy[1]),'w'))
