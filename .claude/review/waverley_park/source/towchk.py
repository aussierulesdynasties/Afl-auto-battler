# gate 2 fix: photo vs render colour along tower A's legs (left end), to set the tower steel colour
exec(open('pj.py',encoding='utf-8').read())
x,y,zh,zb_,hh=-135.2,12.0,58.3,5.0,6.0
ZGK=np.array([(0,0),(95,0),(110,4.5),(128,4.5),(140,4.5),(160,7),(175,11),(197,11),(201,11.5),(214,8.8),(220,8.33),(225,8.5),(235,9),(245,6),(320,5),(380,10),(400,10),(415,0),(PER,0)],float)
def ZG(s):return float(np.interp(s%PER,ZGK[:,0],ZGK[:,1]))
base=np.array([x,y]);PC_=np.mean(F(np.arange(0,PER,1.0)),0)
to=(PC_-base)/np.linalg.norm(PC_-base);sd=np.array([-to[1],to[0]])
sx_=np.arange(0,PER,0.5);zg=ZG(sx_[np.argmin(np.linalg.norm(F(sx_)-[x,y],axis=1))])+zb_;ztop=zh-hh-1.5
ph_=[];rn_=[]
for i,j in[(1,1),(-1,1),(-1,-1),(1,-1)]:
    for z in np.linspace(zg+3,ztop-2,25):
        hw=1.8+(1.5-1.8)*(z-zg)/(ztop-zg);c=base+sd*i*hw+to*j*hw
        p=proj(np.r_[c,z])
        a=samp(PH,p);b=samp(RN[:,:,:3],p)
        if len(a):ph_.append(a[0]);rn_.append(b[0])
ph_=np.array(ph_);rn_=np.array(rn_)
print('n',len(ph_),'photo median',np.median(ph_,0).round(),'p25',np.percentile(ph_,25,0).round(),'render median',np.median(rn_,0).round())
print('tower A mid px',proj(np.r_[base,(zg+ztop)/2]).round())
