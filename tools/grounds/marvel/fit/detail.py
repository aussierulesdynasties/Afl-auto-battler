import json,sys,numpy as np
from PIL import Image,ImageDraw
nm=sys.argv[1];D=json.load(open('/tmp/claude-0/obl/anal.json'))
P=[p for p in D['P']];cp=np.array(D['cp']);d=np.array(D['dist'])
idx=[i for i,p in enumerate(P) if p[0]==nm];P=[P[i] for i in idx];cp=cp[idx];d=d[idx]
A=np.array([p[3:] for p in P]);C=np.array([2.3151,0.6397])
rad=A[:,:2]-C;rad/=np.linalg.norm(rad,axis=1)[:,None]
sgn=np.sum((A[:,:2]-cp[:,:2])*rad,1)  # + = GE outside model
dz=A[:,2]-cp[:,2]
im=Image.open(f'/tmp/claude-0/obl/{nm}/view.png').convert('RGB');dr=ImageDraw.Draw(im)
for p,dd in zip(P,d):
    c=(0,255,0) if dd<1 else (255,255,0) if dd<2 else (255,140,0) if dd<5 else (255,0,0)
    dr.ellipse([p[1]-3,p[2]-3,p[1]+3,p[2]+3],fill=c)
im.save(f'/tmp/claude-0/obl/{nm}_ov.png')
z=A[:,2]
for lo,hi,lab in[(-5,11,'ground/plaza z<11'),(11,20,'wall 11-20'),(20,32,'wall 20-32'),(32,40,'upper 32-40'),(40,60,'roof 40+')]:
    m=(z>=lo)&(z<hi)&(d<10)
    if m.sum()==0:continue
    print(f'{lab:18s} n={m.sum():3d} med dist {np.median(d[m]):.2f}  within1 {np.mean(d[m]<1)*100:.0f}% within2 {np.mean(d[m]<2)*100:.0f}%  med horiz signed {np.median(sgn[m]):+.2f}  med dz {np.median(dz[m]):+.2f}')
print('far (>10 m, other buildings/ground):',int((d>=10).sum()))
print('per column (facade z 11-40, d<10): x  n  med signed  med dist')
for x in sorted(set(p[1] for p in P)):
    m=np.array([p[1]==x for p in P])&(z>=11)&(z<40)&(d<10)
    if m.sum()<3:continue
    print(f'  {x:4d} {m.sum():2d} {np.median(sgn[m]):+.2f} {np.median(d[m]):.2f}')
