# Heritage stands as clean buildings (exec'd from geo.py after herit.py): every roof is a true plane with a straight
# ridge, gable ends are flat triangles, eaves overhang 0.5 m with a trim fascia. Layout in blds.py.
exec(open('blds.py').read())
for _z in sorted({b[6] for b in BLD}):
    MATS['hw%d'%round(_z*10)]=(160,78,58);MATS['hsL%d'%round(_z*10)]=(60,40,44);MATS['hsM%d'%round(_z*10)]=(60,40,44)
MATS.update({'skyglass':(96,140,138),'ashlar':(222,204,160),'hped':(222,204,160),'trim':(232,214,140),'btrim':(238,236,228)})
OV=0.5;HDEC={}
def _fr(f):
    (ox,oy),a=FR[f];a=math.radians(a);U=np.array([math.cos(a),math.sin(a)]);return np.array([ox,oy]),U,np.array([-U[1],U[0]])
ROOFZ={}
def building(n,f,u0,u1,w0,w1,ze,rise,kind):
    O,U,Wd=_fr(f)
    if kind=='gable_w':   # ridge along w: work in a frame turned +90 deg (a along w, b along -u)
        A,B=Wd,-U;a0,a1,b0,b1=w0,w1,-u1,-u0
    else:
        A,B=U,Wd;a0,a1,b0,b1=u0,u1,w0,w1
    P=lambda a,b,z:v(*(O+a*A+b*B),z)
    hw=(b1-b0)/2;bm=(b0+b1)/2;s=rise/hw;ze_e=ze-OV*s
    front=(w0<=10.5);hs=('hsL' if f=='L' else 'hsM')+'%d'%round(ze*10);hwm='hw%d'%round(ze*10)
    # walls (corners counter-clockwise from above); the wall facing the field is the open stand
    C=[(a0,b0),(a1,b0),(a1,b1),(a0,b1)]
    for i in range(4):
        (pa,pb),(qa,qb)=C[i],C[(i+1)%4]
        xy_mid=O+((pa+qa)/2)*A+((pb+qb)/2)*B;nrm=np.cross(np.r_[(qa-pa)*A+(qb-pb)*B,0],[0,0,1])[:2]
        facing_field=front and np.dot(nrm,-Wd)>0.7*np.linalg.norm(nrm)
        quad(P(pa,pb,0),P(qa,qb,0),P(qa,qb,ze),P(pa,pb,ze),hs if facing_field else hwm)
    E=[(a0-OV,b0-OV),(a1+OV,b0-OV),(a1+OV,b1+OV),(a0-OV,b1+OV)]
    if kind=='hip_u':
        r0,r1=a0+hw,a1-hw
        R0,R1=P(r0,bm,ze+rise),P(r1,bm,ze+rise);e=[P(a,b,ze_e) for a,b in E]
        quad(e[0],e[1],R1,R0,'hroof');quad(e[2],e[3],R0,R1,'hroof');tri(e[3],e[0],R0,'hroof');tri(e[1],e[2],R1,'hroof')
        for i in range(4):   # trim fascia round all four eaves
            (pa,pb),(qa,qb)=E[i],E[(i+1)%4];quad(P(pa,pb,ze_e-0.35),P(qa,qb,ze_e-0.35),P(qa,qb,ze_e),P(pa,pb,ze_e),'trim')
    else:
        R0,R1=P(a0-OV,bm,ze+rise),P(a1+OV,bm,ze+rise);e=[P(a,b,ze_e) for a,b in E]
        quad(e[0],e[1],R1,R0,'hroof');quad(e[2],e[3],R0,R1,'hroof')
        # gable triangles (flat, in the end-wall planes): the field-facing pediment is painted, others brick
        for (pa,pb),(qa,qb),ea in (((a0,b1),(a0,b0),a0),((a1,b0),(a1,b1),a1)):
            facing_field=(kind=='gable_w' and ea==a0)
            m='hped' if (facing_field and n=='M2') else ('stone' if facing_field else 'brick')
            tri(P(pa,pb,ze),P(qa,qb,ze),P(ea,bm,ze+rise),m)
            if m=='hped':HDEC['hped']={'o':[float(q) for q in O+ea*A+b1*B],'d':[float(q) for q in -B],'w':float(b1-b0),'z0':ze,'z1':ze+rise}
            ex=ea-OV if ea==a0 else ea+OV   # white barge boards under both rakes
            for (sa,sb),(ta,tb) in (((ex,b0-OV),(ex,bm)),((ex,bm),(ex,b1+OV))):
                za=ze_e if sb in(b0-OV,b1+OV) else ze+rise;zb=ze+rise if tb==bm else ze_e
                quad(P(sa,sb,za-0.4),P(ta,tb,zb-0.4),P(ta,tb,zb),P(sa,sb,za),'btrim');quad(P(ta,tb,zb-0.4),P(sa,sb,za-0.4),P(sa,sb,za),P(ta,tb,zb),'btrim')
            finial(*(O+ex*A+bm*B),ze+rise)
        for (pa,pb),(qa,qb) in ((E[0],E[1]),(E[2],E[3])):   # trim fascia along both eaves
            quad(P(pa,pb,ze_e-0.35),P(qa,qb,ze_e-0.35),P(qa,qb,ze_e),P(pa,pb,ze_e),'trim')
    ROOFZ[n]=(O,A,B,a0,a1,b0,b1,ze,s,kind,hw)
def roofz(n,x,y):
    O,A,B,a0,a1,b0,b1,ze,s,kind,hw=ROOFZ[n];d=np.array([x,y])-O;a=d@A;b=d@B
    dist=min(b-b0,b1-b)
    if kind=='hip_u':dist=min(dist,a-a0,a1-a)
    return ze+s*dist
def inside(n,x,y):
    O,A,B,a0,a1,b0,b1=ROOFZ[n][:7];d=np.array([x,y])-O;return a0<=d@A<=a1 and b0<=d@B<=b1
def finial(x,y,z,h=1.6):
    prism(x,y,0.09,6,z,z+h,'btrim');cone(x,y,0.22,8,z+h*0.55,z+h*0.75,'hroof',bulge=1)
def gablet(n,uc,wd=3.6,rise=1.8):
    """small gable on the field slope of building n at u=uc: cream face flush with the stand front, ridge to the field."""
    O,U,Wd=_fr([b for b in BLD if b[0]==n][0][1]);bb=[b for b in BLD if b[0]==n][0];w0,ze=bb[4],bb[6];s=ROOFZ[n][8]
    P=lambda u,w,z:v(*(O+u*U+w*Wd),z);ze_e=ze-OV*(rise/(wd/2))
    back=w0+(rise+0.6)/s;ua,ub=uc-wd/2,uc+wd/2
    tri(P(ua,w0,ze),P(ub,w0,ze),P(uc,w0,ze+rise),'stone')
    quad(P(ua-OV,w0-OV,ze_e),P(uc,w0-OV,ze+rise),P(uc,back,ze+rise),P(ua-OV,back,ze_e),'hroof')
    quad(P(uc,w0-OV,ze+rise),P(ub+OV,w0-OV,ze_e),P(ub+OV,back,ze_e),P(uc,back,ze+rise),'hroof')
    for (sa,za),(ta,zb) in (((ua-OV,ze_e),(uc,ze+rise)),((uc,ze+rise),(ub+OV,ze_e))):
        quad(P(sa,w0-OV,za-0.35),P(ta,w0-OV,zb-0.35),P(ta,w0-OV,zb),P(sa,w0-OV,za),'btrim')
    finial(*(O+uc*U+(w0-OV)*Wd),ze+rise,2.2)
for b in BLD:building(*b)
for n,uc in GABLETS:gablet(n,uc)
# Members' back roof: the two skylight lanterns read off the photo grid (px 253-268 x 461-469 and 275-288 x 452-459)
for (u0_,w0_,u1_,w1_) in ((253,461,268,469),(275,452,288,459)):
    a_,b_=np.array(px_world([(u0_,(w0_+w1_)/2)],14)[0]),np.array(px_world([(u1_,(w0_+w1_)/2)],14)[0])
    c_=(a_+b_)/2;ln_=float(np.linalg.norm(b_-a_));wd_=float(np.linalg.norm(np.array(px_world([(u0_,w1_)],14)[0])-np.array(px_world([(u0_,w0_)],14)[0])))
    zr=max([roofz(b[0],*c_) for b in BLD if b[1]=='M' and inside(b[0],*c_)],default=None)
    if zr is None:print('LANTERN OUTSIDE',c_);continue
    gablebox(c_[0],c_[1],math.atan2(*(b_-a_)[::-1]),ln_,wd_,zr-1.0,zr+1.0,1.0,'hroof','glassblk','hroof')
# Ladies' Stand: the glazed strip on the back slope of the main roof (teal in the aerial photo, px 345-370 x 540-565)
_O,_U,_W=_fr('L');_q=lambda u,w:(_O+u*_U+w*_W)
_g=[(30.8,21.0),(33.2,21.0),(33.2,28.6),(30.8,28.6)]
quad(*[v(*_q(u,w),roofz('L1',*_q(u,w))+0.12) for u,w in _g],'skyglass')
