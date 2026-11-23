import sys,math,json,numpy as np
sys.path.insert(0,'/home/user/Afl-auto-battler/tools/grounds/optus');import shape
from PIL import Image
from scipy.ndimage import map_coordinates,gaussian_filter
F=360/math.tan(math.radians(25.58/2));OC=shape.OC
IC=np.array(json.load(open('/home/user/Afl-auto-battler/tools/grounds/optus/survey/inner_c.json')))
rdir=sys.argv[1] if len(sys.argv)>1 else 'r2'
def edge(L,e,n,H,th,rexp,z,sign):
    rs=np.arange(rexp-6,rexp+6,0.05)
    u=640+F*(OC[0]+rs*math.cos(th)-e)/(H-z);v=360-F*(OC[1]+rs*math.sin(th)-n)/(H-z)
    if u.min()<3 or u.max()>1276 or v.min()<3 or v.max()>716:return None
    p=map_coordinates(L,[v,u],order=1);g=np.gradient(p)*sign  # sign=-1: bright->dark going outward
    k=int(np.argmax(-g if sign>0 else g)) if False else int(np.argmax(sign*-np.gradient(p)))
    if k<2 or k>len(rs)-3 or abs(np.gradient(p)[k])<3:return None
    return rs[k]
res={'outer':{},'inner':{}}
for a in open('args_g.txt').read().split():
    nm,v=a.split(':');v=[float(x) for x in v.split(',')];e,n,H=v[3],v[4],v[2]
    L=gaussian_filter(np.asarray(Image.open(f'{rdir}/optus_{nm}.png' if rdir!='ge' else f'ge/{nm}.png').convert('RGB'),float).mean(2),0.7)
    for d in np.arange(0,360,0.5):
        th=math.radians(d)
        r=edge(L,e,n,H,th,float(shape.edge_r(th)),float(shape.edge_z(th)),1)
        if r is not None:res['outer'].setdefault(d,[]).append(r-float(shape.edge_r(th)))
        ri=float(shape.fourier(IC,th))
        r=edge(L,e,n,H,th,ri,41.0,-1)
        if r is not None:res['inner'].setdefault(d,[]).append(r-ri)
for k in res:
    dd=np.array([np.median(x) for x in res[k].values()])
    print(k,len(dd),'rms %.2f med %.2f p95 %.2f max %.2f'%(np.sqrt((dd**2).mean()),np.median(dd),np.percentile(abs(dd),95),abs(dd).max()))
    json.dump({str(a):float(np.median(b)) for a,b in res[k].items()},open(f'meas_{rdir}_{k}.json','w'))
