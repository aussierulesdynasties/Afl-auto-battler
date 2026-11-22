p=r'prwt/tools/grounds/gmhba/jss_roof/build_jss.py'
s=open(p,newline='').read();nl='\r\n' if '\r\n' in s else '\n'
old="ZPT={}\nfor z_,kind in ZZ:REAR.append((Vector((xe(z_.y),z_.y)),ZR,0.5,kind));ZPT[len(REAR)-1]=z_\n".replace('\n',nl)
assert old in s
new='''# outer folds run ESE like the inner plates (aerial bands slope 0.35 m south per m east); each zigzag point's
# fold line runs back to the rear edge along that slope. Outer ridge rise: 0 at the rear edge, OUTR at the zigzag
# (GE elevation readout: +1 m midway, +2 m at the step).
OUTR=2.0
RL=[DIAG[0],DIAG[1],Vector((XE,YC)),Vector((XE,YB)),Vector((XE2,YB-0.01)),Vector((XE2,YS))]
def hit_rear(Z):
    d=Vector((-1,0.35)).normalized();best=None
    for k in range(len(RL)-1):
        a,b=RL[k],RL[k+1];e=b-a;den=d.x*(-e.y)-d.y*(-e.x)
        if abs(den)<1e-9:continue
        w=a-Z;t=(w.x*(-e.y)-w.y*(-e.x))/den;u=(d.x*w.y-d.y*w.x)/den
        if t>0 and -1e-6<=u<=1+1e-6 and(best is None or t<best[0]):best=(t,k+u)
    return Z+d*best[0],best[1]
while REAR and REAR[-1][3]=='flat':REAR.pop()
ZW=[hit_rear(z_) for z_,_ in ZZ]
for k in range(int(ZW[0][1])+1):
    if k<len(RL)-1:REAR.append((RL[k],ZR,0.0 if k<2 else 0.25,'flat'))
ZPT={};ZVX={}
for k,(z_,kind) in enumerate(ZZ):
    REAR.append((ZW[k][0],ZR,0.5,kind));ZPT[len(REAR)-1]=z_
    ZVX[len(REAR)-1]=[Vector((v.x,v.y,ZR)) for j,v in enumerate(RL) if k+1<len(ZW) and ZW[k][1]<j<ZW[k+1][1]]
'''.replace('\n',nl)
s=s.replace(old,new)
old2="        plate(Wa,Wb,Zb,TOP,da);plate(Wa,Zb,Za,TOP,da)                       # plain slab\n".replace('\n',nl)
assert old2 in s
new2='''        Oa=Za+Vector((0,0,OUTR)) if ka=='zr' else Za;Ob=Zb+Vector((0,0,OUTR)) if kb=='zr' else Zb
        ring=[Wa]+ZVX.get(i,[])+[Wb]
        for m in range(len(ring)-1):plate(ring[m],ring[m+1],Ob,TOP,da)    # outer folds (fan over rear corners)
        plate(Wa,Ob,Oa,TOP,da)
'''.replace('\n',nl)
s=s.replace(old2,new2)
s=s.replace("        Ta,Tb,Ga,Gb=up(Za,ka),up(Zb,kb),up(Fa,ka),up(Fb,kb)","        Ta,Tb,Ga,Gb=up(Za,ka),up(Zb,kb),up(Fa,ka),up(Fb,kb);Za,Zb=Oa,Ob")
open(p,'w',newline='').write(s)
