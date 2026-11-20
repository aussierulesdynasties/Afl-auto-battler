import sys;sys.argv=['x'];exec(open('tools/fitcam.py').read().split("if __name__")[0])
lab=json.load(open('cam.json'))['lab']
TOP={'A':(95,650),'B':(750,473),'C':(1458,542),'D':(690,682)}
BASES={'C':(1462,838)}
if len(sys.argv)>1 or True: pass
def res3(q,cxy,bases):
    p=np.r_[q[:7],cxy];Ht=q[7];out=[]
    for k,(base,sh) in PT.items():
        t=TW[lab[k]];a,b=proj(p,np.array([[t[0],t[1],0],[t[0],t[1],60]]))
        if k in bases:out+=list(proj(p,np.array([t[0],t[1],0]))[0]-bases[k])
        for s in sh+[TOP[k]]:out.append(linedist(a,b,np.array(s,float)))
        out+=list(proj(p,np.array([t[0],t[1],Ht]))[0]-TOP[k])
    pp=proj(p,PIT);dd=np.sqrt(((GR[:,None,:]-pp[None])**2).sum(-1)).min(1)
    return np.array(out+list(dd))
c0=json.load(open('cam.json'))['p']
for name,bases in [('C',{'C':(1462,838)}),('CA',{'C':(1462,838),'A':(97,958)})]:
  for cxy in [(1109.5,315.0),(905.5,628.5)]:
    s=least_squares(res3,c0[:7]+[60],args=(cxy,bases),bounds=([-5e3,-5e3,30,-20,-1.5,-0.3,300,20],[5e3,5e3,3000,20,0.2,0.3,20000,120]))
    p=np.r_[s.x[:7],cxy]
    D=proj(p,np.array([[*TW[lab['D']],0]]))[0];WF=proj(p,np.array([[-95,71,0],[-100,59,0]]))
    print(name,cxy,'rms',round(math.sqrt((s.fun**2).mean()),2),'H',round(s.x[7],1),'C',np.round(s.x[:3]),'f',round(s.x[6]),'Dbase',D.round(),'facade19/18',WF.round().tolist())
    print('  ',np.round(s.fun,1))
    json.dump({'p':list(p),'lab':lab,'H':s.x[7]},open('cam3_%s_%d.json'%(name,int(cxy[1])),'w'))
