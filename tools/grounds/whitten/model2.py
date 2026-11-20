# Whitten (Western) Oval as in the 1986 aerial (e86_l.jpg). World metres, x east, y north, z up.
# Every outline is a pick off the photo's pixel grid, back-projected through the fitted camera (cam.json).
# Output model2.json: parts {name: {v, f, m (material per face), o (texture origin), a (texture axis)}}
from cam import *
p=np.array(json.load(open('cam.json'))['p'])
def bp(px,z): return [at_z(p,u,v,z)[:2].tolist() for u,v in px]
def bp1(u,v,z): return at_z(p,u,v,z)[:2]
P={}
def part(name,o=(0,0),a=(1,0)):
    a=np.array(a,float);a/=np.linalg.norm(a)
    P.setdefault(name,dict(v=[],f=[],m=[],o=list(map(float,o)),a=a.tolist()));return P[name]
def face(pt,mat,pts):
    k=len(pt['v']);pt['v']+=[list(map(float,q)) for q in pts];pt['f'].append(list(range(k,k+len(pts))));pt['m'].append(mat)
def quad(pt,mat,a,b,c,d):face(pt,mat,[a,b,c,d])
def box(pt,mat,base,z0,z1,top=None,side=None):
    """vertical prism on polygon base (ccw seen from above); top/side materials"""
    n=len(base);lo=[[x,y,z0] for x,y in base];hi=[[x,y,z1] for x,y in base]
    face(pt,top or mat,hi);face(pt,mat,lo[::-1])
    for i in range(n):j=(i+1)%n;quad(pt,side or mat,lo[i],lo[j],hi[j],hi[i])
def obox(pt,mat,c,ax,L,Wd,z0,z1,top=None):
    """oriented box: centre c (xy), axis ax, length L along ax, width Wd"""
    ax=np.array(ax,float);ax/=np.linalg.norm(ax);n=np.array([-ax[1],ax[0]]);c=np.array(c,float)
    b=[c-ax*L/2-n*Wd/2,c+ax*L/2-n*Wd/2,c+ax*L/2+n*Wd/2,c-ax*L/2+n*Wd/2];box(pt,mat,[q.tolist() for q in b],z0,z1,top)
def cyl(pt,mat,x,y,z0,z1,r0,r1,seg=12):
    lo=[[x+r0*math.cos(2*math.pi*i/seg),y+r0*math.sin(2*math.pi*i/seg),z0] for i in range(seg)]
    hi=[[x+r1*math.cos(2*math.pi*i/seg),y+r1*math.sin(2*math.pi*i/seg),z1] for i in range(seg)]
    for i in range(seg):j=(i+1)%seg;quad(pt,mat,lo[i],lo[j],hi[j],hi[i])
    face(pt,mat,hi)
def resample(pts,n):
    pts=np.array(pts,float);d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))];t=np.linspace(0,d[-1],n)
    return np.stack([np.interp(t,d,pts[:,i]) for i in range(pts.shape[1])],1)
def plen(pts):return float(np.sum(np.linalg.norm(np.diff(np.array(pts),axis=0),axis=1)))
def terrace(pt,A,B,z0,z1,nst,tread='step_t',riser='step_r',seats=None,aisles=(),seatmat='seat'):
    """stepped terrace between polyline A (front, low) and B (back, high), same point count.
    seats: bench on every row except within aisles (list of (i0,i1) column index ranges along the polyline)"""
    A=np.array(A,float);B=np.array(B,float);n=len(A)
    for s in range(nst):
        t0,t1=s/nst,(s+1)/nst;zl=z0+(z1-z0)*s/nst;z=z0+(z1-z0)*(s+1)/nst
        r0=A*(1-t0)+B*t0;r1=A*(1-t1)+B*t1
        for i in range(n-1):
            quad(pt,riser,[*r0[i],zl],[*r0[i+1],zl],[*r0[i+1],z],[*r0[i],z])
            quad(pt,tread,[*r0[i],z],[*r0[i+1],z],[*r1[i+1],z],[*r1[i],z])
        if seats:
            sw,sh=seats  # bench depth, height
            for i in range(n-1):
                if any(a0<=i<a1 for a0,a1 in aisles):continue
                f0=r0[i]*(0.55)+r1[i]*(0.45);f1=r0[i+1]*0.55+r1[i+1]*0.45
                d=(r1[i]-r0[i]);d=d/np.linalg.norm(d)*sw/2
                a,b,c,e=f0-d,f1-d,f1+d,f0+d
                face(pt,seatmat,[[*a,z+sh],[*b,z+sh],[*c,z+sh],[*e,z+sh]])
                quad(pt,seatmat,[*a,z],[*b,z],[*b,z+sh],[*a,z+sh])
    # solid ends and back
    quad(pt,riser,[*A[0],0],[*B[0],0],[*B[0],z1],[*A[0],z0]);quad(pt,riser,[*B[-1],0],[*A[-1],0],[*A[-1],z0],[*B[-1],z1])
    for i in range(n-1):quad(pt,riser,[*B[i+1],0],[*B[i],0],[*B[i],z1],[*B[i+1],z1])
    for i in range(n-1):quad(pt,riser,[*A[i],0],[*A[i+1],0],[*A[i+1],z0],[*A[i],z0])
def sheet(pt,mat,A,B,zA,zB,under=None,th=0.25):
    """roof sheet between polylines A (z=zA) and B (z=zB) with thickness and a fascia"""
    A=np.array(A,float);B=np.array(B,float);n=len(A)
    for i in range(n-1):
        quad(pt,mat,[*A[i],zA],[*A[i+1],zA],[*B[i+1],zB],[*B[i],zB])
        quad(pt,under or mat,[*B[i],zB-th],[*B[i+1],zB-th],[*A[i+1],zA-th],[*A[i],zA-th])
        quad(pt,'fascia',[*A[i+1],zA-th],[*A[i],zA-th],[*A[i],zA],[*A[i+1],zA])
        quad(pt,'fascia',[*B[i],zB-th],[*B[i+1],zB-th],[*B[i+1],zB],[*B[i],zB])
    quad(pt,'fascia',[*A[0],zA-th],[*B[0],zB-th],[*B[0],zB],[*A[0],zA]);quad(pt,'fascia',[*B[-1],zB-th],[*A[-1],zA-th],[*A[-1],zA],[*B[-1],zB])


def bldg(pt,wallmat,Q,h,roof='skillion',roofmat='roof_white',rise=0.6,doors=True,openfront=False,z0=0.0):
    """small building on footprint Q (4 corners, picked at roof height): walls to h, iron roof with 0.4 m eaves,
    doors and windows on the long side facing the ground, windows on the other long side.
    roof: flat | skillion (high side away from the ground) | gable (ridge along the long axis, rise above the eaves)
    openfront: brick piers with dark openings on the ground-facing long side (shelter / toilet block)"""
    kv=len(pt['v']);Q=[np.array(q,float) for q in Q];cen=sum(Q)/4
    ar=sum((Q[i][0]*Q[(i+1)%4][1]-Q[(i+1)%4][0]*Q[i][1]) for i in range(4))
    if ar<0:Q=Q[::-1]
    box(pt,wallmat,[q.tolist() for q in Q],0,h,top=wallmat)
    sides=[(Q[i],Q[(i+1)%4]) for i in range(4)];Ls=[np.linalg.norm(b-a) for a,b in sides]
    k0=int(np.argmax([Ls[0]+Ls[2],Ls[1]+Ls[3]]) and 1 or 0)  # long sides are k0 and k0+2
    def outn(a,b):
        d=b-a;n=np.array([d[1],-d[0]])/np.linalg.norm(d);return n if np.dot(n,(a+b)/2-cen)>0 else -n
    lo=[sides[k0],sides[k0+2]];front=min(lo,key=lambda ab:np.linalg.norm((ab[0]+ab[1])/2-c));back=lo[1] if front is lo[0] else lo[0]
    # eaves: footprint grown 0.4 m
    E=[q+(q-cen)/np.linalg.norm(q-cen)*0.55 for q in Q]
    fi=[i for i in range(4) if any(np.allclose(Q[i],x) for x in front)];bi=[i for i in range(4) if i not in fi]
    if roof=='flat':
        box(pt,roofmat,[e.tolist() for e in E],h,h+0.25,top=roofmat,side='fascia')
    elif roof=='skillion':
        z=[h if i in fi else h+rise for i in range(4)]
        face(pt,roofmat,[[*E[i],z[i]+0.15] for i in range(4)]);face(pt,'roof_under',[[*E[i],z[i]] for i in range(4)][::-1])
        for i in range(4):j=(i+1)%4;quad(pt,'fascia',[*E[i],z[i]],[*E[j],z[j]],[*E[j],z[j]+0.15],[*E[i],z[i]+0.15])
        for i in range(4):  # wall infill up to the sloping roof
            j=(i+1)%4
            if z[i]>h or z[j]>h:face(pt,wallmat,[[*Q[i],h],[*Q[j],h],[*Q[j],z[j]-0.02],[*Q[i],z[i]-0.02]])
    else:  # gable along the long axis
        ia,ib=k0,(k0+2)%4  # long sides: (ia,ia+1) and (ib,ib+1); gable ends are the other two
        m0=(E[(ia+1)%4]+E[ib])/2;m1=(E[ia]+E[(ib+1)%4])/2;zr=h+rise
        face(pt,roofmat,[[*E[ia],h],[*E[(ia+1)%4],h],[*m0,zr],[*m1,zr]]);face(pt,roofmat,[[*E[ib],h],[*E[(ib+1)%4],h],[*m1,zr],[*m0,zr]])
        face(pt,'roof_under',[[*m1,zr-0.1],[*m0,zr-0.1],[*E[(ia+1)%4],h-0.1],[*E[ia],h-0.1]]);face(pt,'roof_under',[[*m0,zr-0.1],[*m1,zr-0.1],[*E[(ib+1)%4],h-0.1],[*E[ib],h-0.1]])
        g0=(Q[(ia+1)%4]+Q[ib])/2;g1=(Q[ia]+Q[(ib+1)%4])/2
        face(pt,wallmat,[[*Q[(ia+1)%4],h],[*Q[ib],h],[*g0,zr-0.05]]);face(pt,wallmat,[[*Q[(ib+1)%4],h],[*Q[ia],h],[*g1,zr-0.05]])
    def onface(a,b,u0,u1,z0,z1,mat,off=0.04):
        d=(b-a)/np.linalg.norm(b-a);n=outn(a,b)*off;A=a+d*u0+n;B=a+d*u1+n
        face(pt,mat,[[*A,z0],[*B,z0],[*B,z1],[*A,z1]] if np.cross(np.r_[d,0],np.r_[n,0])[2]<0 else [[*B,z0],[*A,z0],[*A,z1],[*B,z1]])
    for (a,b),isfront in ((front,True),(back,False)):
        L_=float(np.linalg.norm(b-a))
        if openfront and isfront:  # piers every ~2.4 m, dark openings between (photo: pink piers, dark bays)
            nb=max(2,int(round(L_/2.4)))
            for k in range(nb):onface(a,b,k*L_/nb+0.35,(k+1)*L_/nb-0.35,0.0,h-0.5,'opening')
            continue
        if not doors:continue
        nb=max(1,int(L_//4.0));w=L_/nb
        for k in range(nb):
            u=k*w+w/2
            if isfront and (k%2==0 or nb==1):onface(a,b,u-0.45,u+0.45,0.0,min(2.1,h-0.3),'door')
            elif min(2.0,h-0.3)>1.2:onface(a,b,u-0.6,u+0.6,1.1,min(2.0,h-0.3),'window')
    for v_ in pt['v'][kv:]:v_[2]+=z0

pitch=np.array(G['1224799506'],float);c=pitch.mean(0)
def pitch_at(t):
    d=np.array([math.cos(t),math.sin(t)]);n=len(pitch)
    for i in range(n):
        a=pitch[i]-c;b=pitch[(i+1)%n]-c;Mx=np.array([d,-(b-a)]).T
        try:s_,u_=np.linalg.solve(Mx,a)
        except np.linalg.LinAlgError:continue
        if s_>0 and 0<=u_<=1:return c+d*s_,(b-a)/np.linalg.norm(b-a)
def offs(a0,a1,d,nn=40):
    out=[]
    for t in np.radians(np.linspace(a0,a1,nn)):
        q,tg=pitch_at(t);nrm=np.array([tg[1],-tg[0]])
        if np.dot(nrm,q-c)<0:nrm=-nrm
        out.append((q+nrm*d).tolist())
    return out

# =============== EJ Smith stand (Gordon St, east): roofed concrete terrace, rusty iron roof ===============
RB=resample(bp([(113,247),(166,300),(216,350),(268,410),(310,447)],8.0),29)   # roof back edge (street side)
RF=resample(bp([(142,247),(200,300),(252,350),(300,410),(348,447)],6.5),29)   # roof front edge (ground side)
ax=RB[-1]-RB[0];ejs=part('ejs_stand',o=RB[0].tolist(),a=ax.tolist())
sheet(ejs,'roof_rust',RF,RB,6.5,8.0,under='roof_under')
# terrace under the roof: front at the roof's front line, back 0.6 m inside the back wall
nrm=np.array([-ax[1],ax[0]]);nrm/=np.linalg.norm(nrm)
if np.dot(nrm,RB[0]-RF[0])<0:nrm=-nrm
TB=RB-nrm*0.6;TF=RF.copy()
terrace(ejs,TF,TB,0.3,3.6,9,tread='ejs_tread',riser='ejs_riser')
# inside back wall (ads, white) from terrace top to roof, outside wall to the street with piers every bay
for i in range(len(TB)-1):quad(ejs,'ejs_inwall',[*TB[i],3.6],[*TB[i+1],3.6],[*TB[i+1],7.75],[*TB[i],7.75])
for i in range(len(RB)-1):quad(ejs,'ejs_outwall',[*RB[i+1],0],[*RB[i],0],[*RB[i],7.75],[*RB[i+1],7.75])
L=plen(RB);nb=int(round(L/4.6));print('EJS length',round(L,1),'bays',nb)
for k in range(nb+1):
    q=resample(RB,nb+1)[k];obox(ejs,'ejs_outwall',(q+nrm*0.2).tolist(),ax,0.6,0.4,0,7.75)
# blue steel columns on the front step line every 6 m, and roof rafters
nc=int(round(plen(RF)/6.0))
for k in range(nc+1):
    q=resample(RF,nc+1)[k]-nrm*0.0+nrm*0.4;cyl(ejs,'steel_blue',q[0],q[1],0.6,6.25,0.12,0.12,8)
    qb=resample(TB,nc+1)[k];g=np.array([*q,6.2]);h=np.array([*qb,7.7]);d=(h-g)
    nn=np.array([-d[1],d[0],0]);nn=nn/np.linalg.norm(nn)*0.08
    quad(ejs,'steel_blue',(g-nn).tolist(),(h-nn).tolist(),(h+nn).tolist(),(g+nn).tolist())
    quad(ejs,'steel_blue',(g-nn-[0,0,0.35]).tolist(),(h-nn-[0,0,0.35]).tolist(),(h-nn).tolist(),(g-nn).tolist())
# south end building (terracotta roof) and north end building (white)
SE_=bp([(112,240),(130,234),(140,246),(122,252)],4.5);sb=part('ejs_south_building',o=SE_[0],a=ax.tolist())
bldg(sb,'brick_wall',SE_,3.6,roof='gable',roofmat='roof_terracotta',rise=0.9)
NE_=bp([(333,451),(349,448),(352,462),(336,466)],4.0);nb_=part('ejs_north_building',o=NE_[0],a=ax.tolist())
bldg(nb_,'render_white',NE_,3.4,roof='skillion',rise=0.6)
HT=bp([(387,421),(399,419),(399,428),(387,430)],1.5);ht=part('north_pole_hut',o=HT[0],a=(np.array(HT[1])-HT[0]).tolist());bldg(ht,'render_cream',HT,1.6,roof='flat',roofmat='concrete_flat')  # small white hut by the north light pole
# coach's box on the front of the stand
CB=bp([(239,336),(250,331),(254,345),(243,350)],3.5);cbx=part('ejs_coaches_box',o=CB[0],a=ax.tolist())
bldg(cbx,'render_white',CB,3.0,roof='skillion',rise=0.5)

# =============== south-east concrete rings (open terrace by the fence) ===============
rse=part('rings_se',o=(0,0),a=(0,1))
terrace(rse,offs(-98,-37,3.5),offs(-98,-37,15.3),0.3,2.6,10,tread='ring_tread',riser='ring_riser')

# =============== south end: advertising wall, scoreboard building, terrace bank, scoreboard ===============
# base read off the wall's bottom edge in the photo, height 5.3 m from top/bottom pairs (5.0-6.0 measured)
_b=np.array(bp([(286.5,152.5),(275,155),(260,159),(250,162.5),(240,168.5),(220,174),(200,179),(180,185),(172,187.5)],0.0))
_c=np.polyfit(_b[:,0],_b[:,1],2);_x=np.linspace(_b[0,0],_b[-1,0],7);SW=[[float(x),float(np.polyval(_c,x))] for x in _x];sw=np.array(SW);WH=5.3
wax=sw[0]-sw[-1];swp=part('south_wall',o=SW[2],a=wax.tolist())
wn=np.array([-wax[1],wax[0]]);wn/=np.linalg.norm(wn)
for i in range(len(sw)-1):
    a,b=sw[i],sw[i+1];a2,b2=a-wn*0.3,b-wn*0.3
    quad(swp,'adwall',[*b,0],[*a,0],[*a,WH],[*b,WH]);quad(swp,'render_white',[*a2,0],[*b2,0],[*b2,WH],[*a2,WH])
    quad(swp,'render_white',[*a,WH],[*b,WH],[*b2,WH],[*a2,WH])
# advertising panels on the wall's ground face, read off the photo (picked corners, put on the wall plane)
def onwall(u,v,off,ztop=6.0):
    C=p[:3];w=ray(p,u,v);best=None
    for k in range(len(sw)-1):  # each wall segment's own camera-side face (sw-wn*0.3)
        a=sw[k]-wn*0.3;b=sw[k+1]-wn*0.3;d=b-a;n3=np.array([-d[1],d[0],0.0])
        t=n3@(np.array([*a,0.0])-C)/(n3@w);X=C+t*w;s_=(X[:2]-a)@d/(d@d)
        bad=max(0,-s_,s_-1)*10+max(0,-X[2],X[2]-WH)  # off the segment or off the wall height
        if best is None or bad<best[0]:best=(bad,X)
    X=best[1];X[:2]-=wn*off;X[2]=min(max(X[2],0.05),ztop);return X.tolist()
for mat,q,off,*zt in (  # sponsor panels removed: director 2026-11-18 "C: no boards", bare fence at every ground
                  ('opening',[(174,176),(180,174.5),(180,184),(174,185.5)],0.12),):
    Pq=np.array([onwall(u,v,off,*zt) for u,v in q]);L_=(Pq[0]+Pq[3])/2;R_=(Pq[1]+Pq[2])/2;zb=(Pq[2,2]+Pq[3,2])/2;zt_=(Pq[0,2]+Pq[1,2])/2  # a flat rectangle on the wall
    face(swp,mat,[[*L_[:2],zt_],[*R_[:2],zt_],[*R_[:2],zb],[*L_[:2],zb]][::-1])
SB1=bp([(143,169),(159,167),(160,181),(144,187)],6.0);sbp=part('south_east_block',o=SB1[0],a=wax.tolist())
bldg(sbp,'brick_wall',SB1,5.8,roof='flat',roofmat='roof_grey')
SB2=bp([(113,212),(135,203),(140,222),(118,232)],1.5);box(sbp,'render_white',SB2,0,1.5,top='concrete_flat')
# terrace bank: fine concrete steps from the boundary up to the rim
# south bank: gravel walk at the foot, 7 concrete steps (0.3 m risers, ~0.75 m treads, hb/wo-seatsboard.jpg), then a dirt slope to the crest
HL_LO=resample(bp([(290,154),(330,157),(370,159),(410,158),(428,157)],0.0),24)
_hpx=resample([(290,140),(320,131),(354,120),(380,115),(400,114),(425,117),(444,124)],24)
_H=[2.6+1.4*min(1,max(0,(u-290)/64)) for u,v in _hpx]
HL_HI=np.array([at_z(p,u,v,h)[:2] for (u,v),h in zip(_hpx,_H)])
_d=HL_HI-HL_LO;_L=np.linalg.norm(_d,axis=1)[:,None];HL_MID=HL_LO+_d*np.minimum(1,5.25/_L)
hb=part('south_bank',o=HL_LO[0].tolist(),a=(HL_LO[-1]-HL_LO[0]).tolist())
terrace(hb,HL_LO,HL_MID,0.0,2.1,7,tread='bank_tread',riser='bank_riser')
for i in range(len(HL_LO)-1):
    quad(hb,'bank_earth',[*HL_MID[i],2.1],[*HL_MID[i+1],2.1],[*HL_HI[i+1],_H[i+1]],[*HL_HI[i],_H[i]])
    quad(hb,'bank_earth',[*HL_HI[i+1],0],[*HL_HI[i],0],[*HL_HI[i],_H[i]],[*HL_HI[i+1],_H[i+1]])
for k in (0,-1):
    face(hb,'bank_earth',[[*HL_MID[k],0],[*HL_HI[k],0],[*HL_HI[k],_H[k]],[*HL_MID[k],2.1]])
# scoreboard: dark board 3 m tall read off the photo (453.7,133.3)-(464.2,138.3) bottom edge, 1.5 m deep, on the crest
_b0=bp1(453.7,133.3,4.0);_b1=bp1(464.2,138.3,4.0);_ax=_b1-_b0;_n=np.array([_ax[1],-_ax[0]])/np.linalg.norm(_ax)
if np.dot(_n,c-_b0)<0:_n=-_n
KI=[_b0.tolist(),_b1.tolist(),(_b1-_n*1.5).tolist(),(_b0-_n*1.5).tolist()]
kp=part('south_scoreboard',o=KI[0],a=_ax.tolist())
box(kp,'scoreboard_face',KI,4.0,7.0,top='roof_grey')
# light shed beside it (464-477,131-142) and the two white huts behind the crest (442-455,113-127)
for nm,px,zt in [('south_shed',[(465,131),(476,133),(476,137),(465,135)],7.0),('south_huts',[(443,116),(452,114),(455,120),(446,122)],3.0)]:
    q=bp(px,zt);sp=part(nm,o=q[0],a=(np.array(q[1])-q[0]).tolist());bldg(sp,'render_cream' if nm=='south_shed' else 'render_white',q,zt-4.5 if nm=='south_shed' else zt-0.5,roof='skillion' if nm=='south_shed' else 'gable',rise=0.5,z0=4.0 if nm=='south_shed' else 0.0)

# =============== west: seating blocks with aisles, main stand, old stand ===============
# members' open seating: rows follow the boundary, split by six white aisles. Each aisle's foot and head picked off the photo (gM.png)
_AF=[(450,174),(478,178),(502,185),(526,194),(546,205),(564,216)];_AB=[(461,156),(492,160),(521,168),(548,179),(569,188),(586,201)]
_EF=[(432,172),(600,220)];_EB=[(440,158),(604,206)];WZ0,WZ1=0.6,4.0
_fa=[bp1(u,v,WZ0) for u,v in _AF];_ba=[bp1(u,v,WZ1) for u,v in _AB];_fe=[bp1(u,v,WZ0) for u,v in _EF];_be=[bp1(u,v,WZ1) for u,v in _EB]
WB_LO=[_fe[0]];WB_HI=[_be[0]];ais=[]
def _bay(F0,F1,B0,B1,lo,hi,nsub=3):  # points across one bay, inset lo/hi metres from its ends (curve between them kept by the photo picks)
    L=np.linalg.norm(F1-F0);out=[]
    for t in np.linspace(lo/L,1-hi/L,nsub+1):out.append((F0*(1-t)+F1*t,B0*(1-t)+B1*t))
    return out
_Fs=[_fe[0],*_fa,_fe[1]];_Bs=[_be[0],*_ba,_be[1]]
for k_ in range(len(_Fs)-1):
    lo=0.0 if k_==0 else 0.6;hi=0.0 if k_==len(_Fs)-2 else 0.6
    pts=_bay(_Fs[k_],_Fs[k_+1],_Bs[k_],_Bs[k_+1],lo,hi)
    if k_>0:ais.append((len(WB_LO)-1,len(WB_LO)))  # 1.2 m aisle column between the bays
    for f_,b_ in (pts if k_==0 else pts):WB_LO.append(f_);WB_HI.append(b_)
    if k_==0:WB_LO.pop(0);WB_HI.pop(0)
WB_LO=np.array(WB_LO);WB_HI=np.array(WB_HI)
_uu=(pitch-c)/np.linalg.norm(pitch-c,axis=1)[:,None];_FR=pitch+_uu*3.0  # boundary fence line (as built below)
def _ringr(pt_):
    d=(pt_-c)/np.linalg.norm(pt_-c);best=0
    for i in range(len(_FR)):
        a=_FR[i]-c;b=_FR[(i+1)%len(_FR)]-c
        try:s_,u_=np.linalg.solve(np.array([d,-(b-a)]).T,a)
        except np.linalg.LinAlgError:continue
        if s_>0 and 0<=u_<=1:best=max(best,s_)
    return best
for i in range(len(WB_LO)):  # seats start behind the boundary wall (photo: pale strip between grass and the first row)
    r=_ringr(WB_LO[i]);d=WB_LO[i]-c;L=np.linalg.norm(d)
    if L<r+0.9:WB_LO[i]=c+d/L*(r+0.9)
_dep=float(np.mean(np.linalg.norm(WB_HI-WB_LO,axis=1)));WN=max(6,int(round(_dep/0.85)))
print('members seats: depth %.1f m, %d rows, %d aisles'%(_dep,WN,len(ais)))
wb=part('west_seats',o=WB_LO[0].tolist(),a=(WB_LO[-1]-WB_LO[0]).tolist())
terrace(wb,WB_LO,WB_HI,WZ0,WZ1,WN,tread='seat_tread',riser='seat_riser',seats=(0.35,0.45),aisles=ais,seatmat='bench')
for a0,a1 in ais:  # white aisle steps
    for s_ in range(WN):
        t0,t1=s_/WN,(s_+1)/WN;z=WZ0+(WZ1-WZ0)*(s_+1)/WN
        A=WB_LO;B=WB_HI;r0a=A[a0]*(1-t0)+B[a0]*t0;r0b=A[a1]*(1-t0)+B[a1]*t0;r1a=A[a0]*(1-t1)+B[a0]*t1;r1b=A[a1]*(1-t1)+B[a1]*t1
        face(wb,'aisle',[[*r0a,z+0.01],[*r0b,z+0.01],[*r1b,z+0.01],[*r1a,z+0.01]])
CC_B=resample(bp([(560,122),(680,162)],15.0),9);CC_F=resample(bp([(550,133),(673,177)],10.0),9)
ms=part('main_stand',o=CC_B[0].tolist(),a=(CC_B[-1]-CC_B[0]).tolist())
sheet(ms,'roof_white',CC_F,CC_B,10.0,15.0,under='roof_under')
CS_LO=resample(bp([(545,150),(665,205)],1.0),9);CS_HI=CC_B+0.0
mn=np.array([-(CC_B[-1]-CC_B[0])[1],(CC_B[-1]-CC_B[0])[0]]);mn/=np.linalg.norm(mn)
if np.dot(mn,CC_B[0]-CC_F[0])<0:mn=-mn
terrace(ms,CS_LO,CS_HI-mn*0.5,1.0,8.0,14,tread='seat_tread',riser='seat_riser',seats=(0.35,0.45),aisles=[(0,1),(4,5),(7,8)],seatmat='bench')
for i in range(len(CC_B)-1):quad(ms,'brick_wall',[*CC_B[i+1],0],[*CC_B[i],0],[*CC_B[i],15.0],[*CC_B[i+1],15.0])
for i in (0,-1):quad(ms,'brick_wall',[*CC_B[i],0],[*CC_F[i],0],[*CC_F[i],10.0],[*CC_B[i],15.0])
nmc=8
for k in range(nmc+1):
    q=resample(CC_F,nmc+1)[k]-mn*0.6;cyl(ms,'steel_white',q[0],q[1],1.0,9.8,0.15,0.15,8)
# Coca-Cola sign on the roof's back edge
# roof sign as a blank panel, no lettering (director 2026-11-18 "C: no lettering": every sign becomes a blank panel)
cs=np.array(bp([(562,130),(590,137)],15.0));d=cs[1]-cs[0];sg=part('main_stand_sign',o=cs[0].tolist(),a=d.tolist())
quad(sg,'sign',[*cs[0],15.0],[*cs[1],15.0],[*cs[1],17.6],[*cs[0],17.6]);quad(sg,'sign',[*cs[1],15.0],[*cs[0],15.0],[*cs[0],17.6],[*cs[1],17.6])
# north end block of the main stand (salmon brick)
EB=bp([(652,170),(684,160),(688,196),(662,205)],0.0);eb=part('main_stand_end_block',o=EB[0],a=(CC_B[-1]-CC_B[0]).tolist())
bldg(eb,'brick_wall',EB,10.25,roof='flat',roofmat='roof_white')
OLD=bp([(486,114),(513,104),(552,123),(522,135)],8.0);ol=part('old_stand',o=OLD[0],a=(np.array(OLD[1])-OLD[0]).tolist())
bldg(ol,'navy_wall',OLD,7.75,roof='flat',roofmat='roof_grey')  # navy-painted facade (photo 43-63,62-81,76-95)

# =============== EJ Whitten stand (north-west, curved roof) ===============
EJ_B=resample(bp([(728,202),(745,218),(760,240),(768,262),(773,285)],12.5),12)
EJ_F=resample(bp([(680,205),(700,230),(712,255),(720,283)],10.5),12)
ew=part('ejw_stand',o=EJ_B[0].tolist(),a=(EJ_B[-1]-EJ_B[0]).tolist())
sheet(ew,'roof_white',EJ_F,EJ_B,10.5,12.5,under='roof_under',th=0.5)
en=EJ_B-EJ_F
for i in range(len(EJ_B)-1):quad(ew,'ejw_back',[*EJ_B[i+1],0],[*EJ_B[i],0],[*EJ_B[i],12.1],[*EJ_B[i+1],12.1])
for i in (0,):quad(ew,'ejw_back',[*EJ_B[i],0],[*EJ_F[i],0],[*EJ_F[i],10.1],[*EJ_B[i],12.1])
# low building north of the EJW, pale terracotta roof (photo 724-772, 290-320)
RG=bp([(726,303),(768,291)],5.0);EV=bp([(730,318),(774,309)],3.5)  # pink lean-to roof, ridge (white trim) to eave
lb=part('ejw_lowbldg',o=RG[0],a=(np.array(RG[1])-RG[0]).tolist());box(lb,'render_white',[RG[0],RG[1],EV[1],EV[0]],0.0,3.5)
sheet(lb,'roof_pink',np.array(EV),np.array(RG),3.5,5.0,under='roof_under',th=0.2)
# seat rows under the roof only (director 2026-11-18): front row under the roof's front edge, rows step back along the curve
EJ_Bt=resample(bp([(728,202),(745,218),(760,240),(769,266)],12.5),30);EJ_Ft=resample(bp([(680,205),(700,230),(712,255),(716,268)],10.5),30)  # seats stop at the low building
_sd=EJ_Bt-EJ_Ft;_sl=np.linalg.norm(_sd,axis=1)[:,None];_su=_sd/_sl
EJ_S=EJ_Ft+_su*0.5;EJ_T=EJ_Bt-_su*0.8;_nr=int(round(float(np.mean(np.linalg.norm(EJ_T-EJ_S,axis=1)))/0.8));print('EJW seat rows',_nr)
terrace(ew,EJ_S,EJ_T,1.0,1.0+0.4*_nr,_nr,tread='ejwseat_tread',riser='ejwseat_riser',seats=(0.35,0.45),aisles=[(0,1),(7,8),(14,15),(21,22),(28,29)],seatmat='ejwseat_bench')
for i in range(len(EJ_S)-1):quad(ew,'ejwseat_riser',[*EJ_S[i],0],[*EJ_S[i+1],0],[*EJ_S[i+1],1.0],[*EJ_S[i],1.0])  # front wall under the first row
# roof ribs across the roof, front edge to back edge, every ~5 m (the darker bands in the photo)
_Lr=plen(EJ_F);_nrib=int(round(_Lr/5.0));print('EJW ribs',_nrib+1)
for k in range(_nrib+1):
    f_=resample(EJ_F,_nrib+1)[k];b_=resample(EJ_B,_nrib+1)[k];d_=b_-f_;n_=np.array([-d_[1],d_[0]])/np.linalg.norm(d_)*0.2
    A_=[*(f_-n_),10.5];B_=[*(b_-n_),12.5];C_=[*(b_+n_),12.5];D_=[*(f_+n_),10.5]
    quad(ew,'steel_white',[A_[0],A_[1],A_[2]+0.3],[B_[0],B_[1],B_[2]+0.3],[C_[0],C_[1],C_[2]+0.3],[D_[0],D_[1],D_[2]+0.3])
    quad(ew,'steel_white',A_,B_,[B_[0],B_[1],B_[2]+0.3],[A_[0],A_[1],A_[2]+0.3]);quad(ew,'steel_white',C_,D_,[D_[0],D_[1],D_[2]+0.3],[C_[0],C_[1],C_[2]+0.3])
# angled gantry at the stand's front corner (photo 640-676, 258-277): a white-roofed race rising from the ring into the stand
rc=part('ejw_race',o=bp1(643,273,3.0).tolist(),a=(bp1(662,266,6.5)-bp1(643,273,3.0)).tolist())
_g0=bp1(643,273,3.0);_g1=bp1(662,266,6.5);_gd=_g1-_g0;_gu=_gd/np.linalg.norm(_gd);_gn=np.array([-_gu[1],_gu[0]])
for (q0,z0),(q1,z1),w,w1 in (((_g0,3.0),(_g1,6.5),2.1,0.45),):  # photo: 4.2 m wide at the ring end, tapering to a point at the walkway
    a0,b0,a1,b1=q0-_gn*w,q0+_gn*w,q1-_gn*w1,q1+_gn*w1
    face(rc,'roof_white',[[*a0,z0],[*a1,z1],[*b1,z1],[*b0,z0]])
    face(rc,'render_white',[[*a0,0],[*a1,0],[*a1,z1-0.2],[*a0,z0-0.2]][::-1]);face(rc,'render_white',[[*b0,0],[*b1,0],[*b1,z1-0.2],[*b0,z0-0.2]])
    face(rc,'render_white',[[*b0,0],[*a0,0],[*a0,z0-0.2],[*b0,z0-0.2]][::-1])  # end wall facing the ground
    _m0=(a0+b0)/2;_dn=-_gu*0.03;face(rc,'opening',[[*(_m0+_gn*1.2+_dn),0],[*(_m0-_gn*1.2+_dn),0],[*(_m0-_gn*1.2+_dn),2.3],[*(_m0+_gn*1.2+_dn),2.3]][::-1])  # race doorway
    face(rc,'render_white',[[*a0,z0-0.2],[*a1,z1-0.2],[*a1,z1],[*a0,z0]]);face(rc,'render_white',[[*b1,z1-0.2],[*b0,z0-0.2],[*b0,z0],[*b1,z1]])
_g2=bp1(676,262,7.5)  # the steel walkway carrying on up into the stand (blue-grey in the photo)
obox(rc,'steel_blue',((_g1+_g2)/2).tolist(),_g2-_g1,float(np.linalg.norm(_g2-_g1)),1.4,6.3,6.6)
for i in range(len(EJ_F)-1):  # fascia band under the roof edge (cream with red/white/blue)
    quad(ew,'ejw_fascia',[*EJ_F[i],9.4],[*EJ_F[i+1],9.4],[*EJ_F[i+1],10.25],[*EJ_F[i],10.25])
for k in range(0,12,3):
    q=EJ_F[k]+(EJ_B[k]-EJ_F[k])*0.12;cyl(ew,'steel_white',q[0],q[1],5.0,10.1,0.18,0.18,8)

# =============== north-west concrete rings ===============
rnw=part('rings_nw',o=(0,0),a=(1,0))
terrace(rnw,offs(108,169,3.5),offs(108,169,19.3),0.3,3.0,12,tread='ring_tread',riser='ring_riser')

# =============== north: red panel walls, terrace down to the courts, small scoreboard ===============
for nm,(l,r) in (('north_wall_1',((482,445),(650,398))),('north_wall_2',((385,488),(455,460)))):
    B0=np.array(bp([l,r],0.0));d=B0[1]-B0[0];Ln=np.linalg.norm(d);u=d/Ln;nw=np.array([-u[1],u[0]])
    if np.dot(nw,np.array([214.,140.])-c)<0 and False:nw=-nw
    pw=part(nm,o=B0[0].tolist(),a=d.tolist());npn=int(round(Ln/2.4))
    for k in range(npn):  # panels with 5 cm gaps, posts between
        a=B0[0]+u*(k*Ln/npn+0.03);b=B0[0]+u*((k+1)*Ln/npn-0.03)
        for s,sgn in ((0,1),(0.12,-1)):
            pass
        tm=(k+0.5)/npn;pm='render_white' if (nm=='north_wall_1' and 0.226<tm<0.393) else 'red_panel'  # photo 520-548: the toilet block's white wall in the fence line
        quad(pw,pm,[*a,0.2 if pm=='red_panel' else 0],[*b,0.2 if pm=='red_panel' else 0],[*b,4.8],[*a,4.8]);quad(pw,pm,[*b+nw*0.12,0.2 if pm=='red_panel' else 0],[*a+nw*0.12,0.2 if pm=='red_panel' else 0],[*a+nw*0.12,4.8],[*b+nw*0.12,4.8])
        quad(pw,pm,[*a,4.8],[*b,4.8],[*b+nw*0.12,4.8],[*a+nw*0.12,4.8])
        q=B0[0]+u*(k*Ln/npn);obox(pw,'steel_grey',(q+nw*0.25).tolist(),u,0.15,0.15,0,5.0)
    q=B0[1];obox(pw,'steel_grey',(q+nw*0.25).tolist(),u,0.15,0.15,0,5.0)
NT_HI=resample(bp([(482,447),(560,425),(650,400)],0.0),16);NT_LO=resample(bp([(493,457),(570,438),(650,420)],0.0),16)
ntp=part('north_terrace',o=NT_LO[0].tolist(),a=(NT_LO[-1]-NT_LO[0]).tolist())
_NH=NT_HI+np.array([0.3,0.6])
for i in range(len(NT_LO)-1):
    quad(ntp,'rubble',[*NT_LO[i],0.3],[*NT_LO[i+1],0.3],[*_NH[i+1],3.0],[*_NH[i],3.0])
    quad(ntp,'rubble',[*NT_LO[i+1],0],[*NT_LO[i],0],[*NT_LO[i],0.3],[*NT_LO[i+1],0.3])
for k in (0,-1):face(ntp,'rubble',[[*NT_LO[k],0],[*_NH[k],0],[*_NH[k],3.0],[*NT_LO[k],0.3]])
# south toilet block (photo 520-548, 418-446): white wall section in the fence line with a dark doorway, low white block behind it
W0=np.array(bp([(482,445),(650,398)],0.0));wd=W0[1]-W0[0];wu=wd/np.linalg.norm(wd);wn=np.array([-wu[1],wu[0]])
_gs=1.0 if np.dot(wn,c-(W0[0]+W0[1])/2)>0 else -1.0
_pm=W0[0]+wd*((531-482)/168);_o=(wn*(0.12+0.03) if _gs<0 else -wn*0.03)  # ground face of the wall
SBN=bp([(537,430),(548,428),(548,433),(537,435)],3.0);sbn=part('north_scoreboard',o=SBN[0],a=wu.tolist())
for _o in (wn*0.15,-wn*0.03):
    face(sbn,'opening',[[*(_pm-wu*1.1+_o),0],[*(_pm+wu*1.1+_o),0],[*(_pm+wu*1.1+_o),2.4],[*(_pm-wu*1.1+_o),2.4]])
bldg(sbn,'render_white',SBN,2.7,roof='flat',roofmat='roof_white')
# sheds north-west
# sheds north-west: roof outlines read at roof height (zoom zNE)
for nm,q,zt,wm,rm,rf in (('nw_shed_1',[(712,337),(726,335),(727,344),(714,346)],3.2,'render_white','roof_white','gable'),('nw_shed_2',[(696,350),(715,345),(716,356),(698,360)],3.4,'render_white','roof_grey','gable'),('nw_hut',[(731,374),(740,371),(741,379),(733,382)],2.2,'render_white','roof_white','flat')):
    Q=bp(q,zt);sp_=part(nm,o=Q[0],a=(np.array(Q[1])-Q[0]).tolist());bldg(sp_,wm,Q,zt-(0.9 if rf=='gable' else 0.3),roof=rf,roofmat=rm,rise=0.9 if rf=='gable' else 0.3,openfront=(nm=='nw_toilets'))

# =============== light towers (tapered) with lamp heads ===============
def tower(name,x,y,h):
    t=part(name,o=(x,y),a=(1,0));cyl(t,'pole',x,y,0,h,0.35,0.15,12)
    d=np.array([144.,77.])-[x,y];d/=np.linalg.norm(d);s=np.array([-d[1],d[0]])
    hc=np.array([x,y])+d*0.6
    # head frame 3.0 x 1.6 m with a catwalk, 2 rows x 4 floodlights facing the ground
    obox(t,'steel_grey',hc.tolist(),s,3.2,0.25,h-0.2,h+1.8)
    obox(t,'steel_grey',(hc-d*0.5).tolist(),s,3.2,1.0,h-0.3,h-0.2)
    for r in range(2):
        for k in range(4):
            q=hc+s*(-1.2+0.8*k)+d*0.35;obox(t,'lamp',q.tolist(),s,0.6,0.35,h+0.1+0.85*r,h+0.75+0.85*r)
tower('tower_n',215.4,137.4,17.9);tower('tower_se',195.1,-6.5,17.5)

# =============== apron (outer concrete) ===============
from scipy.spatial import ConvexHull
allxy=np.array([v[:2] for q in P.values() for v in q['v']]);hull=allxy[ConvexHull(allxy).vertices]
def radial(poly,angs):
    poly=np.array(poly,float);out=[]
    for t in angs:
        d=np.array([math.cos(t),math.sin(t)]);best=None
        for i in range(len(poly)):
            a=poly[i]-c;b=poly[(i+1)%len(poly)]-c;Mx=np.array([d,-(b-a)]).T
            try:s,u=np.linalg.solve(Mx,a)
            except np.linalg.LinAlgError:continue
            if s>0 and 0<=u<=1 and (best is None or s>best):best=s
        out.append((c+d*best).tolist())
    return out
angs=np.linspace(0,2*math.pi,121)[:-1]
# ground perimeter: walls and stand backs, in order round the ground (picked off the photo)
PER=[*RB.tolist(),*bp([(350,458)],0.0),*bp([(385,488),(455,460),(482,445)],0.0),*bp([(650,398),(700,382),(730,421),(765,410)],0.0),
     *EJ_B[::-1].tolist(),*bp([(688,196)],0.0),*CC_B[::-1].tolist(),*bp([(500,108)],0.0),*HL_HI[::-1].tolist(),*SW,*bp([(140,182),(120,200),(118,236)],0.0)]
uu=(pitch-c)/np.linalg.norm(pitch-c,axis=1)[:,None];inner=radial((pitch+uu*3.0).tolist(),angs);outer=radial(PER,angs)
ap=part('apron',o=(0,0),a=(1,0));n=len(angs)
for i in range(n):j=(i+1)%n;quad(ap,'apron',[*inner[j],0.05],[*inner[i],0.05],[*outer[i],0.05],[*outer[j],0.05])
bf=part('boundary_fence',o=(0,0),a=(1,0))
for i in range(n):
    j=(i+1)%n;a_,b_=np.array(inner[i]),np.array(inner[j]);o_=(a_-c)/np.linalg.norm(a_-c)*0.3;o2=(b_-c)/np.linalg.norm(b_-c)*0.3
    quad(bf,'fence_white',[*b_,0],[*a_,0],[*a_,1.0],[*b_,1.0]);quad(bf,'fence_white',[*(a_+o_),0],[*(b_+o2),0],[*(b_+o2),1.0],[*(a_+o_),1.0])
    quad(bf,'fence_cap',[*a_,1.0],[*(a_+o_),1.0],[*(b_+o2),1.0],[*b_,1.0])
    quad(bf,'kerb',[*(a_+o_),0.06],[*(a_+o_*2.0),0.06],[*(b_+o2*2.0),0.06],[*(b_+o2),0.06])
    if i%4==0:  # grated drain pit at the foot of the fence every ~25 m
        m_=(a_+b_)/2+(o_+o2)/2*2.6;t_=(b_-a_)/np.linalg.norm(b_-a_)*0.45;r_=(o_+o2)/2/0.3*0.3
        face(bf,'drain',[[*(m_-t_-r_),0.065],[*(m_+t_-r_),0.065],[*(m_+t_+r_),0.065],[*(m_-t_+r_),0.065]])
# no playing field: the game draws its own grass inside the boundary fence (director 2026-11-18 "Leave field out")

# north-west apron: dirt over the concrete and a grass patch (photo 655-780, 310-400)
ad=part('apron_dirt',o=(0,0),a=(1,0))
face(ad,'dirt_apron',[[*q,0.07] for q in bp([(712,310),(733,320),(760,330),(772,343),(773,357),(757,367),(747,373),(733,383),(720,390),(703,393),(682,390),(657,377),(682,368),(698,360),(723,348)],0.0)])
face(ad,'grass_patch',[[*q,0.09] for q in bp([(735,371),(772,357),(780,384),(762,399),(742,396)],0.0)])
json.dump(P,open('model2.json','w'))
print(len(P),'parts',sum(len(q['f']) for q in P.values()),'faces')
