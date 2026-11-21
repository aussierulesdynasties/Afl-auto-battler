p=r'prwt/tools/grounds/gmhba/jss_roof/build_jss.py'
s=open(p,newline='').read()
nl='\r\n' if '\r\n' in s else '\n'
a=s.index('for k,yv in enumerate(YV):');b=s.index("REAR.append((Vector((XE2,YS)),None,0.5,'end'))")
new='''# zigzag where the folded plates start (aerial: the gable shadows fall just west of each ridge; ridges 1.75 m east
# of the shadow centres). West of it a plain slab to the west edge (GE 3D). Valleys midway between ridges.
NOTCH=[(-73.8,77.2),(-78.4,69.6),(-84.4,60.9),(-90.6,52.2),(-95.9,44.0),(-100.3,33.7),(-103.1,25.8),(-106.3,15.5)]
RID=[Vector((x+1.75,y)) for x,y in NOTCH]
ZZ=[(RID[0]+(RID[0]-RID[1])*0.5,'zv')]
for k in range(len(RID)):
    ZZ.append((RID[k],'zr'))
    nx=RID[k+1] if k+1<len(RID) else RID[k]+(RID[k]-RID[k-1])
    ZZ.append(((RID[k]+nx)*0.5,'zv'))
ZPT={}
for z_,kind in ZZ:REAR.append((Vector((xe(z_.y),z_.y)),ZR,0.5,kind));ZPT[len(REAR)-1]=z_
'''.replace('\n',nl)
s=s[:a]+new+s[b:]
# fpt for zigzag points: front of the zigzag point
s=s.replace("R,z,w,kind=REAR[i];FR[i]=front(Vector((R.x,R.y,0)),w)","R,z,w,kind=REAR[i];Q=ZPT.get(i,R);FR[i]=front(Vector((Q.x,Q.y,0)),w)")
a=s.index("    if kind=='valley' and i+2<len(REAR)");b=s.index("    if kind=='end':break")
new='''    if kind in('zv','zr') and REAR[i+1][3] in('zv','zr'):
        Wa,Wb=R3(i),R3(i+1);(Fa,da),(Fb,db)=fpt(i),fpt(i+1)
        def base(j,W,F):
            Z=ZPT[j];t=(Z-W.to_2d()).length/max(1e-6,(F.to_2d()-W.to_2d()).length);return Vector((Z.x,Z.y,W.z+(F.z-W.z)*t))
        Za,Zb=base(i,Wa,Fa),base(i+1,Wb,Fb)
        up=lambda v,k_:v+Vector((0,0,PK)) if k_=='zr' else v.copy()
        ka,kb=REAR[i][3],REAR[i+1][3]
        plate(Wa,Wb,Zb,TOP,da);plate(Wa,Zb,Za,TOP,da)                       # plain slab
        Ta,Tb,Ga,Gb=up(Za,ka),up(Zb,kb),up(Fa,ka),up(Fb,kb)
        plate(Ta,Tb,Gb,TOP,da);plate(Ta,Gb,Ga,TOP,da)                        # folded plate
        face([Za,Zb,Ta if ka=='zr' else Tb],SOFF,[(0,0),(1,0),(0.5,1)])       # west gable over the slab
        face([Fa,Fb,Ga if ka=='zr' else Gb],SOFF,[(0,0),(1,0),(0.5,1)])       # inner gable over the ring roof
        if ka=='zr':PEAKS.append((Ga,Ta))
        i+=1;continue
'''.replace('\n',nl)
s=s[:a]+new+s[b:]
s=s.replace("print('PEAKS',len(PEAKS),'VALLEYS',len(YV),'REAR',len(REAR))","print('PEAKS',len(PEAKS),'REAR',len(REAR))")
open(p,'w',newline='').write(s)
