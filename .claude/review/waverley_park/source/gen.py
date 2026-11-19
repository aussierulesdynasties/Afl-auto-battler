exec(open('fence.py',encoding='utf-8').read().split('#MAIN')[0])
import json
TJ=json.load(open('turf.json'));SEG=json.load(open('segs.json'))
QV=[];QU=[];QM=[];TV=[];TU=[];TM=[]
MATN=[]
def mi(n):
    if n not in MATN:MATN.append(n)
    return MATN.index(n)
TILE={'greenpaint':(2,2.6),'roofm':(2,4),'dirt':(4,4),'kiosko':(2,2),'kioskr':(2,2),'kioskb':(2,2),'rib':(1,1),'pave':(4,4),'grass':(4,4),'dirtA':(8,8),'dirtS':(8,8),'dirtP':(8,8),'asph':(8,8),'asphp':(8,8),'grass_n':(8,8),'grass_nl':(8,8),'steeldk':(2,2),'mastg':(1,1),'concrete':(4,4),'aislec':(4,4),'bowlconc':(4,4),'bowllight':(4,4),'facade':(4,4),'fvoid':(2,2),'fcol':(1,1),'fslab':(1,1),'roof':(4,4),'roofn':(4,4),'white':(2,2),'steel':(2,2),'underside':(4,4),'glass':(4,2),'race':(4,2),'blueroof':(4,2),'navywall':(3,3),'redpaint':(2,2),'black':(2,2)}
def tile(m):
    if m.startswith('seat_'):return (2,1)
    return TILE.get(m,(4,4))
def quad(a,b,c,d,m,uv=None):
    a,b,c,d=[np.asarray(x,float) for x in(a,b,c,d)]
    if uv is None and m in ('grass','dirt','pave','dirtA','dirtS','dirtP','asph','asphp','grass_n','grass_nl'):   # ground: world-planar UVs so the texture runs on across quads
        tu,tv=tile(m);uv=[(x[0]/tu,x[1]/tv) for x in(a,b,c,d)]
    if uv is None:
        tu,tv=tile(m);lu=np.linalg.norm(b-a);lv=np.linalg.norm(d-a)
        uv=[(0,0),(lu/tu,0),(lu/tu,lv/tv),(0,lv/tv)]
    QV.append([a,b,c,d]);QU.append(uv);QM.append(mi(m))
def tri(a,b,c,m,uv=((0,0),(1,0),(0,1))):
    TV.append([np.asarray(a,float),np.asarray(b,float),np.asarray(c,float)]);TU.append(uv);TM.append(mi(m))
def sgrid(s0,s1,step=1.5):
    n=max(2,int(math.ceil(abs(s1-s0)/step))+1);return np.linspace(s0,s1,n)
def strip(ss,prof,mats):
    prof=np.asarray(prof,float);npf=len(prof)
    pts=[P(np.full(npf,s),prof[:,0],prof[:,1]) for s in ss]
    for j in range(npf-1):
        m=mats[j]
        if m is None:continue
        tu,tv=tile(m);L=np.hypot(*(prof[j+1]-prof[j]))
        if L<1e-4:continue
        u=0.0
        for i in range(len(ss)-1):
            A,B=pts[i],pts[i+1];du=np.linalg.norm(B[j,:2]-A[j,:2])
            quad(A[j],B[j],B[j+1],A[j+1],m,[(u/tu,0),((u+du)/tu,0),((u+du)/tu,L/tv),(u/tu,L/tv)]);u+=du
def strip2(ss,pf,mats):
    for i in range(len(ss)-1):
        A=pf(ss[i]);B=pf(ss[i+1])
        for j in range(len(A)-1):
            m=mats[j]
            if m is None:continue
            a=P([ss[i]],A[j][0],A[j][1])[0];b=P([ss[i+1]],B[j][0],B[j][1])[0];c=P([ss[i+1]],B[j+1][0],B[j+1][1])[0];d_=P([ss[i]],A[j+1][0],A[j+1][1])[0]
            if np.linalg.norm(d_-a)<1e-4 and np.linalg.norm(c-b)<1e-4:continue
            quad(a,b,c,d_,m)
ZGK=np.array([(0,0),(95,0),(110,4.5),(128,4.5),(140,4.5),(160,7),(175,11),(197,11),(201,11.5),(214,8.8),(220,8.33),(225,8.5),(235,9),(245,6),(320,5),(380,10),(400,10),(415,0),(PER,0)],float)
def ZG(s):return float(np.interp(s%PER,ZGK[:,0],ZGK[:,1]))
def endcap(s,prof,m,flip=False):
    for j in range(len(prof)-1):
        (d0,z0),(d1,z1)=prof[j],prof[j+1]
        if d1-d0<1e-3:continue
        a,b,c,d=P([s],d0,0)[0],P([s],d1,0)[0],P([s],d1,z1)[0],P([s],d0,z0)[0]
        if flip:quad(b,a,d,c,m)
        else:quad(a,b,c,d,m)
def beam(a,b,w,m):
    a=np.asarray(a,float);b=np.asarray(b,float);ax_=b-a;ax_/=np.linalg.norm(ax_)
    t=np.cross(ax_,[0,0,1.0]) if abs(ax_[2])<0.95 else np.cross(ax_,[1.0,0,0]);t/=np.linalg.norm(t);u=np.cross(t,ax_)
    h=w/2;cs=[t*h+u*h,-t*h+u*h,-t*h-u*h,t*h-u*h]
    for k in range(4):quad(a+cs[k],a+cs[(k+1)%4],b+cs[(k+1)%4],b+cs[k],m)
# ---------------- seat block colours ----------------
COL=['rose','rose','rose','Y','G','R','B','Y','R','sage','Y','B','B','B','B','Y','R','R','R','B','G','Y','M','M','G','M','M','Y','G','B','R','Y','sage','L','rose','rose','rose','K','W','P','L','K','rose','sage','B','Y','R','G','B','Y','rose','rose','rose','G','G','M','Y','M','G','G','G','N','W','R']+['G']*7
blocks=[[s0,s0+w,COL[k],k] for k,(s0,w) in enumerate(SEG)]
a0,a1=blocks[0][0],blocks[1][1];blocks[0][1]=blocks[1][0]=(a0+a1)/2
MEM=(392.0,522.0);GAP=(252.5,297.6);XAISLE=(260,360)
RISE=0.28;DEP=0.8;NPAINT=24
def z_r(r):return 1.0+RISE*r
def in_rng(s,r):return r[0]<=s<=r[1]
# ---------------- turf ----------------
x0,y0,x1,y1=TJ['bbox'];span=max(x1-x0,y1-y0)
def tuv(X):return ((X[0]-x0)/span,(X[1]-(y1-span))/span)
C=np.r_[PC,0.0];ssT=np.arange(0,PER,1.0)
for i in range(len(ssT)):
    pass   # director 2026-11-18 'Leave field out': the game draws its own grass inside the boundary fence
strip(sgrid(0,PER,2.0),[(0,0),(0,1.0)],['white'])   # fence front
# ---------------- painted lower rows ----------------
def seat_prof(r):
    d=DEP*r;z=z_r(r);return [(d,z),(d+0.3,z),(d+0.3,z+0.42),(d+0.75,z+0.42),(d+0.8,z+0.8),(d+0.8,z+RISE)]
def walk_prof(r):
    d=DEP*r;z=z_r(r);return [(d,z),(d+0.8,z),(d+0.8,z+RISE)]
def stair_prof(r):
    d=DEP*r;z=z_r(r);return [(d,z),(d+0.4,z),(d+0.4,z+0.14),(d+0.8,z+0.14),(d+0.8,z+RISE)]
NZ=(195.0,252.5);NX=10   # near-right corner: painted rows run on under the roof (rows 24-33, to d 27.2)
for s0,s1,col,k in blocks:
    a,b=s0+0.6,s1-0.6
    subs=[(a,b,('bk%d'%k) if 33<=k<=47 else col)]   # right end: shades matched to the photo (mktex4)
    if k==62:
        w=(b-a);edges=[a]+[a+w*f for f in(0.22,0.27,0.47,0.52,0.72,0.77)]+[b];cs=['W','N','W','N','W','N','W']
        subs=[(edges[i],edges[i+1],cs[i]) for i in range(7)]
    for sa,sb,cc in subs:
        ss=sgrid(sa,sb)
        for r in range(NPAINT):
            dmid=DEP*r+0.4
            if 16.4<=dmid<=17.6 and in_rng((sa+sb)/2,XAISLE):strip(ss,walk_prof(r),['concrete','concrete'])
            else:strip(ss,seat_prof(r),['concrete','seat_'+cc,'seat_'+cc,'seat_'+cc,'seat_'+cc])
        ea,eb=max(sa,NZ[0]),min(sb,NZ[1])
        if eb>ea:
            for r in range(NPAINT,NPAINT+NX):strip(sgrid(ea,eb),seat_prof(r),['concrete','seat_'+cc,'seat_'+cc,'seat_'+cc,'seat_'+cc])
            if eb==NZ[1]:
                for r in range(NPAINT,NPAINT+NX):
                    pr=seat_prof(r);cap=[pr[1],pr[2],pr[3],pr[4],(pr[4][0],z_r(NPAINT))]
                    V=[P([eb],d,z)[0] for d,z in cap];tri(V[0],V[2],V[1],'aislec');tri(V[0],V[3],V[2],'aislec');tri(V[0],V[4],V[3],'aislec')
    ss=sgrid(b,s1+0.6,0.6)
    for r in range(NPAINT+(NX if NZ[0]<=b and s1+0.6<=NZ[1] else 0)):strip(ss,stair_prof(r),['aislec']*4)   # photo: aisles barely show against the seats
    for r in range(NPAINT+(NX if NZ[0]<=a and b<=NZ[1] else 0)):
        pr=seat_prof(r);cap=[pr[1],pr[2],pr[3],pr[4],(pr[4][0],pr[0][1])]
        for sx in(a,b):
            V=[P([sx],d,z)[0] for d,z in cap];tri(V[0],V[1],V[2],'aislec');tri(V[0],V[2],V[3],'aislec');tri(V[0],V[3],V[4],'aislec')
ZB=z_r(NPAINT);DB=DEP*NPAINT
# ---------------- bowl behind the painted rows ----------------
DP1=21.6
def grey_rows(d0,z0,d1):
    pr=[];d=d0;z=z0;ms=[]
    while d+0.8<=d1+1e-6:
        pr+=[(d,z+RISE),(d+0.3,z+RISE),(d+0.3,z+RISE+0.4),(d+0.8,z+RISE+0.4)];ms+=['bowlconc','bowlconc','bowlconc','seat_grey'];d+=0.8;z+=RISE
    return pr,ms,z
rows_pr,rows_m,ZT=grey_rows(DP1,ZB,34.4)
bowl_back=[(DB,ZB),(DP1,ZB)]+rows_pr+[(34.4,ZT+0.4)]
BM=['concrete']+rows_m+['concrete']
BM=BM[:len(bowl_back)-1]
RS=MEM[1];RE=MEM[0]+PER
ssB=sgrid(RS,RE,1.5)
def _light(s):s=s%PER;return 249<=s<=300   # photo: the open terrace in the gap has light treads
BML=[({'bowlconc':'bowlgap','seat_grey':'seat_gapg'}.get(m,m)) for m in BM]   # gap rows: photo shade (mktex4)
def zrow(d):   # top of the grey rows at depth d (tread level)
    return ZB+RISE*math.floor((d-DP1)/0.8+1e-6)+RISE
UPA=0.6   # half width of an upper-tier aisle (photo: aisles run straight on through both tiers)
UPS=sorted(set(round(b[1]%PER,3) for b in blocks if not in_rng(b[1]%PER,(MEM[0]-1,MEM[1]+1))))
# holes cut out of the grey rows, read off the photo grid: (s0, s1, d0, d1, kind)
#  portal: a dark vomitory mouth 3 m wide at each block centre, at the front of the upper tier
#  pit:    the sunken ramp well in the gap terrace
#  deck:   the white walkway along the back of the gap terrace
HOLES=[]
for s0,s1,col,k in blocks:
    sc=(s0+s1)/2
    if not in_rng(sc%PER,(MEM[0]-2,MEM[1]+2)) and not in_rng(sc%PER,NZ):HOLES.append((sc-1.5,sc+1.5,DP1,24.0,'portal'))
HOLES.append((275.0,287.5,26.4,31.2,'pit'));HOLES.append((258.0,292.0,32.0,34.4,'deck'))
def _cuts(lo,hi):
    c=[lo,hi]
    for a in UPS:c+=[a-UPA,a+UPA,a-UPA+PER,a+UPA+PER]
    for h in HOLES:c+=[h[0],h[1],h[0]+PER,h[1]+PER]
    return sorted(set(x for x in c if lo<=x<=hi))
def _piece(pr,mm,d0,d1):   # the part of the row profile from d0 to d1 (inclusive ends)
    ia=min(i for i,(dd,zz) in enumerate(pr) if dd>=d0-1e-6) if d0>pr[0][0] else 0
    ib=max(i for i,(dd,zz) in enumerate(pr) if dd<=d1+1e-6)
    if d0>pr[0][0]:ia=max(i for i,(dd,zz) in enumerate(pr) if dd<=d0+1e-6)
    if d1<pr[-1][0]:ib=min(i for i,(dd,zz) in enumerate(pr) if dd>=d1-1e-6)
    return pr[ia:ib+1],mm[ia:ib]
def _bowl(lo,hi,light):
    cuts=_cuts(lo,hi)
    for a,b in zip(cuts[:-1],cuts[1:]):
        if b-a<1e-3:continue
        mid=(a+b)/2;isA=any(abs(((mid-u+PER/2)%PER)-PER/2)<UPA for u in UPS)
        ss=sgrid(a,b,1.5)
        mm=(['concrete']+['aislec']*(len(bowl_back)-3)+['concrete']) if isA else (BML if light else BM)   # aisle: in line with the aisle below
        hs=sorted([h for h in HOLES if h[0]<mid%PER<h[1]],key=lambda h:h[2])
        dlo=bowl_back[0][0]
        for h in hs+[(0,0,bowl_back[-1][0]+1,0,'end')]:
            if h[4]=='end':pr,m_=_piece(bowl_back,mm,dlo,bowl_back[-1][0])
            else:pr,m_=_piece(bowl_back,mm,dlo,h[2])
            if len(pr)>1:strip(ss,pr,m_)
            if h[4]!='end':dlo=h[3]
_i0=0
for _i in range(1,len(ssB)+1):
    if _i==len(ssB) or _light(ssB[_i])!=_light(ssB[_i0]):
        _seg=ssB[_i0:min(_i+1,len(ssB))];_bowl(_seg[0],_seg[-1],_light(ssB[_i0]));_i0=_i
def _hole_walls(h,zf,mside,mfloor,mback):
    s0,s1,d0,d1,kind=h
    pr=[(dd,zz) for dd,zz in bowl_back if d0-1e-6<=dd<=d1+1e-6]
    for sx_,fl_ in((s0,True),(s1,False)):   # side walls: floor up to the row profile
        for (da,za),(db,zb) in zip(pr[:-1],pr[1:]):
            if db-da<1e-3:continue
            a=P([sx_],da,zf)[0];b=P([sx_],db,zf)[0];c=P([sx_],db,zb)[0];e=P([sx_],da,za)[0]
            quad(b,a,e,c,mside) if fl_ else quad(a,b,c,e,mside)
    ss=sgrid(s0,s1,1.0)
    strip(ss,[(d0,pr[0][1]),(d0,zf),(d1,zf),(d1,pr[-1][1])],[mback if pr[0][1]>zf+1e-3 else None,mfloor,mback])
    return ss
for h in HOLES:
    if h[4]=='portal':_hole_walls(h,ZB,'aislec','black','black')
# the ramp well: walls down below the walkway level, a dark floor and a ramp falling from the left end of the well
_ph=[h for h in HOLES if h[4]=='pit'][0];_zf=ZB-0.5
_wss=_hole_walls(_ph,_zf,'concrete','black','concrete')
_pa,_pb,_pd0=_ph[0],_ph[1],_ph[2]
for _k in range(len(_wss)-1):   # ramp: rises from the well floor at s 285.5 to the terrace at the left end
    sa,sb=_wss[_k],_wss[_k+1]
    if sb>285.5:continue
    za=_zf+(zrow(_pd0)-_zf)*(285.5-sa)/(285.5-_pa);zb_=_zf+(zrow(_pd0)-_zf)*(285.5-sb)/(285.5-_pa)
    quad(P([sa],_pd0+0.4,za)[0],P([sa],_pd0+2.6,za)[0],P([sb],_pd0+2.6,zb_)[0],P([sb],_pd0+0.4,zb_)[0],'aislec')
    beam(P([sa],_pd0+2.6,za+1.0)[0],P([sb],_pd0+2.6,zb_+1.0)[0],0.08,'white')
_dh=[h for h in HOLES if h[4]=='deck'][0]   # white deck: a raised walkway across the back of the gap terrace
_dpr=[(dd,zz) for dd,zz in bowl_back if dd<=_dh[2]+1e-6]
strip(sgrid(_dh[0],_dh[1],1.0),[(_dh[2],_dpr[-1][1]),(_dh[2],ZT+0.4),(34.4,ZT+0.4)],['white','white'])
for sx_,fl_ in((_dh[0],True),(_dh[1],False)):
    pr=[(dd,zz) for dd,zz in bowl_back if dd>=_dh[2]-1e-6]
    for (da,za),(db,zb) in zip(pr[:-1],pr[1:]):
        if db-da<1e-3:continue
        a=P([sx_],da,ZT+0.4)[0];b=P([sx_],db,ZT+0.4)[0];c=P([sx_],db,zb)[0];e=P([sx_],da,za)[0]
        quad(a,b,c,e,'white') if fl_ else quad(b,a,e,c,'white')
def facade_frame(s0,s1,ztop=None,dout=None):
    """outer wall under the roof: dark void 0.8 m back, columns every 2 m, slabs every 2 m, mullions between (photo layout)"""
    zt=ZR_OUT-0.8 if ztop is None else ztop;DO=DR_OUT if dout is None else dout;DV=DO-0.8
    ss=sgrid(s0,s1,1.0)
    strip2(ss,lambda s:[(DV,zt),(DV,ZG(s)-0.3)],['fvoid'])
    strip2(ss,lambda s:[(DV,ZG(s)),(DO,ZG(s))],['pave'])   # floor under the column line: no gap to the sky at the wall foot
    strip(ss,[(DO,zt),(DO,zt+0.01),(DV,zt+0.01)],[None,'fslab'])
    for sc in np.arange(math.ceil(s0/2.0)*2.0,s1-0.2,2.0):
        g=ZG(sc)-0.3
        for (w_,d0_,m_) in((0.27,DO,'fcol'),):
            a=P([sc-w_/2],DV,g)[0];b=P([sc-w_/2],d0_,g)[0];c=P([sc+w_/2],d0_,g)[0];e=P([sc+w_/2],DV,g)[0]
            up=np.array([0,0,zt-g])
            quad(b,c,c+up,b+up,m_);quad(a,b,b+up,a+up,m_);quad(c,e,e+up,c+up,m_)
        a=P([sc+1-0.04],DV,g)[0];b=P([sc+1-0.04],DO-0.25,g)[0];c=P([sc+1+0.04],DO-0.25,g)[0]
        if sc+1<s1:up=np.array([0,0,zt-g]);quad(b,c,c+up,b+up,'fcol')
    for zl in np.arange(2.0,zt-0.5,2.0):
        for i in range(len(ss)-1):
            sa,sb=ss[i],ss[i+1]
            if zl<ZG(sa)+0.8 or zl<ZG(sb)+0.8:continue
            for (dA,zA,dB,zB) in((DO,zl,DO,zl+0.23),(DO,zl+0.23,DV,zl+0.23),(DV,zl,DO,zl)):
                quad(P([sa],dA,zA)[0],P([sb],dA,zA)[0],P([sb],dB,zB)[0],P([sa],dB,zB)[0],'fslab')
def roof_on(s):return not in_rng(s%PER,GAP)
ZR_IN,ZR_OUT,DR_IN,DR_OUT=8.9,15.6,19.7,35.2
def zroof(d):return ZR_IN+(ZR_OUT-ZR_IN)*(d-DR_IN)/(DR_OUT-DR_IN)
DINK=np.array([(0,32),(47,31),(63,29),(86,27),(97,28),(105,22),(119,21),(140,19.7),(195,19.7),(205,21.0),(230,21.2),(240,23.0),(246,23.6),(250,25.0),(253,26.0),(297.6,23.8),(300,30.5),(309,31.5),(318,32),(328,32),(PER,32)],float)
def DIN(s):return float(np.interp(s%PER,DINK[:,0],DINK[:,1]))   # roof inner edge, measured from the photo
roof_sets=[];cur=[]
ssR=np.unique(np.r_[ssB,GAP[0]+PER-1e-4,GAP[1]+PER+1e-4])   # the roof ends exactly at the gap
for s in ssR:
    if roof_on(s):cur.append(s)
    elif cur:roof_sets.append(cur);cur=[]
if cur:roof_sets.append(cur)
for rs in roof_sets:
    rs=np.array(rs)
    strip(rs,[(34.4,ZT+0.4),(34.4,zroof(34.4)-0.8)],['facade'])
    bnd=[b_ for b_ in(110,290,110+PER,290+PER) if rs[0]<b_<rs[-1]]
    cuts=np.r_[rs[0],bnd,rs[-1]]
    for lo_,hi_ in zip(cuts[:-1],cuts[1:]):
        part=np.r_[lo_,rs[(rs>lo_)&(rs<hi_)],hi_];rm_='roofn' if 110<((lo_+hi_)/2)%PER<290 else 'roof'
        strip2(part,lambda s:[(DIN(s),zroof(DIN(s))-0.4),(DIN(s),zroof(DIN(s))),(DR_OUT,ZR_OUT),(DR_OUT,ZR_OUT-0.8),(DIN(s),zroof(DIN(s))-0.4)],['white',rm_,'white','underside'])
    facade_frame(rs[0],rs[-1])
    for sx in(rs[0],rs[-1]):
        di=DIN(sx);V=[P([sx],d,z)[0] for d,z in[(di,zroof(di)-0.4),(di,zroof(di)),(DR_OUT,ZR_OUT),(DR_OUT,ZR_OUT-0.8)]];quad(*V,'white')
gap_ss=np.array([s for s in ssB if not roof_on(s)])
if len(gap_ss):
    gs=np.r_[gap_ss[0]-1.5,gap_ss,gap_ss[-1]+1.5]
    strip2(gs,lambda s:[(34.4,ZT+0.4),(34.4,ZT+1.5),(DR_OUT,ZT+1.5),(DR_OUT,ZT+0.3),(DR_OUT,ZG(s))],['white','white','white','bowlconc'])  # photo scan s 253-265 (d 35.25): grey concrete face, white only on the top 1.2 m coping
for sb in np.arange(0,PER,5.0):   # end roofs: light purlins every 5 m (photo, both ends)
    if 110<sb<290 or in_rng(sb,MEM) or not roof_on(sb):continue
    A=P([sb],DIN(sb),zroof(DIN(sb)))[0];B=P([sb],DR_OUT,ZR_OUT)[0];beam(A+[0,0,0.12],B+[0,0,0.12],0.25,'white')
for s0,s1,col,k in blocks:   # roof ribs along the aisles (near side)
    sb=s1%PER
    if in_rng(sb,MEM) or not roof_on(sb) or not 110<sb<290:continue
    A=P([sb],DIN(sb),zroof(DIN(sb)))[0];B=P([sb],DR_OUT,ZR_OUT)[0];beam(A+[0,0,0.15],B+[0,0,0.15],0.2,'rib')
# ---------------- members' stand ----------------
MQ0,MT0=len(QV),len(TV)
mss=sgrid(MEM[0],MEM[1],1.5)
mid_pr=[(DB,ZB),(20.5,ZB),(20.5,ZB+1.1),(20.8,ZB+1.1),(21.0,ZB+1.1)];mid_mats=['concrete','white','white','concrete']
d=21.0;z=ZB+1.1
while d+0.8<=34.0+1e-6:
    mid_pr+=[(d,z+RISE),(d+0.3,z+RISE),(d+0.3,z+RISE+0.4),(d+0.8,z+RISE+0.4)];mid_mats+=['concrete','concrete','seat_mg','seat_mg'];d+=0.8;z+=RISE
ZM=z+RISE+0.4
mid_pr+=[(35.0,ZM)];mid_mats+=['concrete']
mid_pr+=[(35.0,15.7),(35.0,16.7),(35.0,19.4),(35.0,20.4),(35.5,20.4)];mid_mats+=['facade','white','glass','white','concrete']
d=35.5;z=20.4;UR=(30-20.4)/(52-35.5)*0.8
while d+0.8<=52.0+1e-6:
    mid_pr+=[(d,z+UR),(d+0.3,z+UR),(d+0.3,z+UR+0.42),(d+0.8,z+UR+0.42)];mid_mats+=['bowlconc','bowlconc','seat_ug','seat_ug'];d+=0.8;z+=UR
ZUT=z+UR+0.42
mid_pr+=[(52.2,ZUT)];mid_mats+=['concrete']   # top walk stops at the back frame's void plane
strip(mss,mid_pr,mid_mats)
strip(mss,[(35.0,33.4),(35.0,34.0),(53.0,39.0),(53.0,38.3),(35.0,33.4)],['white','roofm','white','underside'])
# rear block (top-down check, 2026-11-19): straight-down imagery (Esri 2018 and 2026 flights) shows the members' roof at d 35.5-54
# and a lower roof behind it to d 60 that the 1990s photo cannot see (hidden behind the main roof). Plan from the satellite;
# height kept under the main roof's sight line from the photo camera (era-appropriate where no photo shows it).
strip(mss,[(53.0,38.3),(53.0,31.0),(60.0,29.0)],['facade','roof'])
facade_frame(MEM[0],MEM[1],ztop=29.0,dout=60.0)   # members' back wall: same column/slab frame as the outer wall
for sx,fl in((MEM[0],False),(MEM[1],True)):
    endcap(sx,mid_pr[:-1],'white' if not fl else 'facade',fl)
    endcap(sx,[(53.0,31.0),(60.0,29.0)],'facade',fl)
    V=[P([sx],d,z)[0] for d,z in[(35.0,33.4),(35.0,34.0),(53.0,39.0),(53.0,38.3)]];quad(*V,'white')
    if fl:   # left (west) end: open steel frame under the roof, as photographed
        a=P([sx],35.0,20.4)[0];b=P([sx],35.0,33.4)[0];c=P([sx],53.0,ZUT)[0];e=P([sx],53.0,38.3)[0]
        for u_,v_ in((a,b),(c,e),(a,e),(b,c)):beam(u_,v_,0.35,'steel')
for sm in np.arange(MEM[0]+2.0,MEM[1]+0.1,8.0):   # 17 roof masts, one every 8 m, stays to the front
    # gate fix 2026-11-19: photo posts are thin and grey, tops at z 44.5-45.5 (median 45.0, mastchk.py)
    top=P([sm],53.0,45.0)[0];beam(P([sm],53.0,38.5)[0],top,0.3,'mastg');beam(top,P([sm],37.0,34.6)[0],0.18,'mastg');beam(P([sm],35.3,34.15)[0],P([sm],52.9,39.1)[0],0.15,'mastg')
# the photographed west end is skewed: the back corner sits 3.3 m short of the front corner
def _shear(Vs):
    Vs=np.asarray(Vs,float);sh=Vs.shape;X=Vs.reshape(-1,3);sg=np.arange(380,535,0.05);Fg=F(sg)
    out=X.copy()
    for i0 in range(0,len(X),2000):
        xy=X[i0:i0+2000,:2];j=np.argmin(((xy[:,None,:]-Fg[None])**2).sum(-1),1);s=sg[j]
        d=((xy-Fg[j])*N(s)).sum(1);k=3.3*np.clip((s-470)/52,0,None)*np.clip((d-35)/18,0,1)
        s2=s-k;out[i0:i0+2000,:2]=F(s2)+N(s2)*d[:,None]
    return out.reshape(sh)
def hut(sc,d0,d1,zb,zt,w,face='black'):
    ss=sgrid(sc-w/2,sc+w/2,w)
    strip(ss,[(d0,zb),(d0,zt),(d1,zt)],[face,'concrete'])
    endcap(sc-w/2,[(d0,zt),(d1,zt)],'concrete');endcap(sc+w/2,[(d0,zt),(d1,zt)],'concrete',True)
for sc in(394,408,423,438,454,471,487,503,517):hut(sc,19.6,22.0,ZB,ZB+2.6,2.4)
def zu(d):return 20.4+(d-35.5)/0.8*UR+0.42
for k in range(15):   # upper-tier vomitories, one every 8.3 m
    sc=400.0+8.3*k;ss=sgrid(sc-1.6,sc+1.6,3.2)
    strip(ss,[(43.5,zu(43.5)),(43.5,zu(43.5)+2.6),(45.5,zu(43.5)+2.6)],['black','concrete'])
    for sx_,fl_ in((sc-1.6,False),(sc+1.6,True)):
        a=P([sx_],43.5,zu(43.5))[0];b=P([sx_],45.5,zu(45.5))[0];c=P([sx_],45.5,zu(43.5)+2.6)[0];e=P([sx_],43.5,zu(43.5)+2.6)[0]
        quad(b,a,e,c,'concrete') if fl_ else quad(a,b,c,e,'concrete')
QV[MQ0:]=list(_shear(QV[MQ0:]));TV[MT0:]=list(_shear(TV[MT0:])) if len(TV)>MT0 else TV[MT0:]
# ---------------- end buildings and race canopy ----------------
def sbox(s0,s1,d0,d1,z1,mwall,mtop):
    ss=sgrid(s0,s1,1.0)
    g=min(ZG(s0),ZG(s1));z1=g+z1
    strip(ss,[(d0,g-0.5),(d0,z1),(d1,z1),(d1,g-0.5)],[mwall,mtop,mwall])
    for sx_,fl_ in((s0,False),(s1,True)):
        a=P([sx_],d0,g-0.5)[0];b=P([sx_],d1,g-0.5)[0];c=P([sx_],d1,z1)[0];e=P([sx_],d0,z1)[0]
        quad(b,a,e,c,mwall) if fl_ else quad(a,b,c,e,mwall)
sbox(62,65,DR_OUT,53,6.0,'facade','concrete')
# red box on the building's outer edge (photo: low red block on a grey roof, about 1.6 m tall)
ss=sgrid(62,65,1.0);strip(ss,[(49.5,6.0),(49.5,7.6),(53.0,7.6),(53.0,6.0)],['redpaint','redpaint','redpaint'])
for sx_,fl_ in((62,False),(65,True)):
    a_=P([sx_],49.5,6.0)[0];b_=P([sx_],53.0,6.0)[0];c_=P([sx_],53.0,7.6)[0];e_=P([sx_],49.5,7.6)[0]
    quad(b_,a_,e_,c_,'redpaint') if fl_ else quad(a_,b_,c_,e_,'redpaint')
def dsh(s):return 46.5+(s-284.8)*0.406
# blue shed: a straight box in the photo (not curved with the ring); measured outer edge dsh(), inner end on the facade
gsh=min(ZG(283),ZG(305));zsh=gsh+3.0
_to=P([283],dsh(283),0)[0][:2];_bo=P([305],dsh(305),0)[0][:2]   # measured outer edge (photo)
_u=(_bo-_to)/np.linalg.norm(_bo-_to);_n=np.array([-_u[1],_u[0]])
if np.dot(_n,PC-_to)<0:_n=-_n
_sx=np.arange(0,PER,0.25);_FF=F(_sx)
def _dring(q):return float(np.min(np.linalg.norm(_FF-q,axis=1)))
# photo: shed is a straight box ~7 m wide; a lane about 3.6 m wide separates it from the facade (copied as seen)
_ti=_to+_n*7.0;_bi=_bo+_n*7.0
_C=[_ti,_to,_bo,_bi]
def _v(p,z):return np.r_[p,z]
quad(_v(_ti,zsh),_v(_to,zsh),_v(_bo,zsh),_v(_bi,zsh),'roof')
for k in range(4):
    p0,p1=_C[k],_C[(k+1)%4];quad(_v(p0,gsh-0.5),_v(p1,gsh-0.5),_v(p1,zsh),_v(p0,zsh),'navywall')
# ---------------- outside ground: concourse ring and grass embankment ----------------
def outer_d(s):
    s=s%PER;w=np.clip(min(s-(MEM[0]-6),(MEM[1]+6)-s)/6.0,0,1)
    if 279<=s<=309:return max(45.0+18.0*w,46.5+(min(max(s,283),305)-284.8)*0.406+2.0)
    return 45.0+18.0*w
ssG=sgrid(0,PER,2.0)
def _ss(a,b):return ssG[(ssG>=a)&(ssG<=b)]
# concourse ring (d 35.2 to outer_d). Gate fix 2026-11-19, traced from the photo: plain dirt s 118-178, asphalt s 178-252
ssD=ssG[ssG<=118]
for sg_,m_ in((ssD,'dirt'),(_ss(118,178),'dirtA'),(_ss(178,252),'asph'),(_ss(252,PER-1),'pave')):strip2(sg_,lambda s:[(DR_OUT,ZG(s)),(outer_d(s),ZG(s))],[m_])
# embankment down to z 0. Photo: grass beyond d 48 at s 118-160 (dirt above it), dirt with tufts s 160-186,
# a grey asphalt plaza and road down the slope in front of the green building s 186-206, dry grass s 206-252
def emb(s,d):return ZG(s)-(d-outer_d(s))/2.0
def emb_split(ss,dk,m0,m1):strip2(ss,lambda s:[(outer_d(s),ZG(s)),(dk,emb(s,dk)),(outer_d(s)+2.0*ZG(s)+0.01,0.0)],[m0,m1])
# plaza traced from the photo: s 187-200 down to d 52 (light pink dirt with small trees s 182-187), then only the road s 191-199 runs on down the slope
ssG=np.unique(np.r_[ssG,182,187,191,199,200])
for sg_,m_ in((ssG[ssG<=118],'grass'),(_ss(160,182),'dirtS'),(_ss(182,187),'dirtP'),(_ss(191,199),'asphp'),(_ss(200,252),'grass_n'),(_ss(252,PER),'grass')):strip2(sg_,lambda s:[(outer_d(s),ZG(s)),(outer_d(s)+2.0*ZG(s)+0.01,0.0)],[m_])
emb_split(_ss(118,160),48.0,'dirtS','grass_nl');emb_split(_ss(187,191),52.0,'asphp','dirtP');emb_split(_ss(199,200),52.0,'asphp','grass_n')
# ---------------- near-side outside works, from the photo (s 136-210) ----------------
ssd=sgrid(136,170,1.5)   # raised concourse deck where the ground falls away
# gate fix 2026-11-19: the photo shows a dark steel deck and frame along the wall (no white piers, no white rails)
strip(ssd,[(DR_OUT,10.0),(39.5,10.0),(39.5,9.4),(DR_OUT,9.4)],['steeldk','steeldk','steeldk'])
endcap(136,[(DR_OUT,10.0),(39.5,10.0),(39.5,9.4)],'steeldk')
_fs=np.arange(136.5,170.1,3.0)
for sx in _fs:   # steel posts at the outer edge and at the wall, 3 m apart
    for dd in(36.0,39.3):beam(P([sx],dd,ZG(sx)-0.3)[0],P([sx],dd,9.4)[0],0.2,'steeldk')
for a_,b_ in zip(_fs[:-1],_fs[1:]):   # X bracing in the outer frame
    za=ZG(a_);zb=ZG(b_)
    if 9.4-max(za,zb)>0.8:beam(P([a_],39.3,za)[0],P([b_],39.3,9.4)[0],0.12,'steeldk');beam(P([b_],39.3,zb)[0],P([a_],39.3,9.4)[0],0.12,'steeldk')
ssr=sgrid(136,176,1.0)
for zr in(10.5,11.05):strip(ssr,[(39.4,zr),(39.4,zr+0.07)],['steeldk'])
for sx in np.arange(136,176,2.0):beam(P([sx],39.4,10.0)[0],P([sx],39.4,11.1)[0],0.06,'steeldk')
# photo: stairs and kiosk tops sit in the roof's shade and read dark grey
def stair(s_bot,s_top,zb,zt,d0=DR_OUT,d1=DR_OUT+2.0):
    n=int(round((zt-zb)/0.18));dz=(zt-zb)/n
    for i in range(n):
        sa=s_bot+(s_top-s_bot)*i/n;sb_=s_bot+(s_top-s_bot)*(i+1)/n;z=zb+dz*(i+1)
        quad(P([sa],d0,z)[0],P([sa],d1,z)[0],P([sb_],d1,z)[0],P([sb_],d0,z)[0],'aislec')
        quad(P([sa],d1,z-dz)[0],P([sa],d1,z)[0],P([sa],d0,z)[0],P([sa],d0,z-dz)[0],'aislec')
    for dd in(d1,):
        strip(sgrid(min(s_bot,s_top),max(s_bot,s_top),1.0),[(dd,0)],[]) if False else None
        beam(P([s_bot],dd,zb+1.0)[0],P([s_top],dd,zt+1.0)[0],0.06,'steeldk')   # photo: stair rails read dark
        A=P([s_bot],dd,zb)[0];B=P([s_top],dd,zt)[0];C_=P([s_top],dd,zt-0.5)[0];D=P([s_bot],dd,zb-0.01)[0];quad(A,B,C_,D,'aislec')
    ls=sgrid(s_top,s_top-np.sign(s_bot-s_top)*1.5,1.5)   # top landing and door
    strip(ls,[(d0,zt),(d1,zt),(d1,zt-0.4)],['aislec','aislec'])
    sd_=s_top-np.sign(s_bot-s_top)*0.75;strip(sgrid(sd_-0.6,sd_+0.6,1.2),[(d0-0.02,zt),(d0-0.02,min(zt+2.1,ZR_OUT-0.9))],['black'])
stair(179.5,172.0,ZG(179.5),14.0);stair(198.5,202.0,ZG(198.5),14.0)   # photo: rises toward larger s, top landing by the orange kiosk (samp5 check 2026-11-19)
KD0,KD1=33.6,35.3   # photo: kiosks stand under the roof, front just proud of the column line
# photo read at the column line (d 35): a coloured band on a dark base; band bottom/top z per group
def kfloor(s):return 10.0 if s<175 else ZG(s)
def kiosk(s0,s1,m,zb,zt):
    ss=sgrid(s0,s1,1.0)
    strip2(ss,lambda s:[(KD1,kfloor(s)),(KD1,zb)],['fvoid'])          # dark base, floor up to the band
    strip(ss,[(KD0,zt),(KD1,zt),(KD1,zb)],['aislec',m])                # coloured band and its top
    for sx_,fl_ in((s0,False),(s1,True)):
        g=kfloor(sx_)
        for z0_,z1_,mm in((g,zb,'fvoid'),(zb,zt,m)):
            a_=P([sx_],KD0,z0_)[0];b_=P([sx_],KD1,z0_)[0];c_=P([sx_],KD1,z1_)[0];e_=P([sx_],KD0,z1_)[0]
            quad(b_,a_,e_,c_,mm) if fl_ else quad(a_,b_,c_,e_,mm)
for s0,s1,m,zb,zt in((165.6,168.5,'kiosko',11.2,12.3),(168.5,172.6,'kioskr',11.2,12.3),(172.6,173.4,'kiosko',11.2,12.3),
                     (186.8,191.2,'kioskb',11.3,12.8),(191.4,193.2,'concrete',11.3,12.8),(193.5,195.8,'kioskb',11.3,12.8),
                     (204.2,205.5,'kiosko',11.8,13.0),(205.8,215.8,'kioskr',11.8,13.0)):kiosk(s0,s1,m,zb,zt)   # photo scan along d 35.3, 0.5 m steps
# long low building on the near side, outside the concourse (photo x 480-725, y 458-516): green walls, grey sheet roof
def lbuild(s0,s1,df,db,hf,hb,mf,mb):
    ss=sgrid(s0,s1,1.0)
    strip2(ss,lambda s:[(df(s),ZG(s)-0.3),(df(s),ZG(s)+hf),(db(s),ZG(s)+hb),(db(s),ZG(s)-0.3)],[mf,'roofn',mb])
    for sx_,fl_ in((s0,False),(s1,True)):
        g=ZG(sx_);a=P([sx_],db(sx_),g-0.3)[0];b=P([sx_],df(sx_),g-0.3)[0];c=P([sx_],df(sx_),g+hf)[0];e=P([sx_],db(sx_),g+hb)[0]
        quad(b,a,e,c,'greenpaint') if fl_ else quad(a,b,c,e,'greenpaint')
lin=lambda s0,v0,s1,v1:(lambda s:v0+(s-s0)*(v1-v0)/(s1-s0))
lbuild(180.0,186.6,lin(180,46.5,186.6,46.4),lin(180,42.4,186.6,42.5),2.4,3.0,'greenpaint','greenpaint')
lbuild(186.6,200.3,lin(186.6,46.2,200.3,45.8),lin(186.6,42.6,200.3,42.0),2.2,2.8,'facade','greenpaint')
lbuild(200.3,214.5,lin(200.3,46.0,214.5,44.0),lin(200.3,42.0,214.5,38.5),2.4,3.0,'greenpaint','greenpaint')
ss=sgrid(183.8,186.4,0.5);strip2(ss,lambda s:[(43.2,ZG(s)+2.9),(43.2,ZG(s)+4.6),(41.0,ZG(s)+4.6),(41.0,ZG(s)+2.9)],['white','white','white'])
# ---------------- goal posts ----------------
ax=np.array(TJ['ax']);ay=np.array([-ax[1],ax[0]])
# director 2026-11-18 'Posts out': the game draws its own goal and behind posts
# ---------------- light towers ----------------
# 4th value: tower foot height above the stadium ring ground (A stands on higher ground; photo grid: foot at y 160)
# 5th value: lamp panel height. Photo grid: C and D heads read about 1.3x shorter than A/B's 6 m panel
TW=[(-135.2,12.0,58.3,5.0,6.0),(86.0,131.8,55.7,0.0,6.0),(140.2,-40.7,45.9,0.0,4.6),(-10.9,-133.2,47.3,0.0,4.6)]
for x,y,zh,zb,hh in TW:
    base=np.array([x,y]);to=(PC-base)/np.linalg.norm(PC-base);sd=np.array([-to[1],to[0]])
    sx_=np.arange(0,PER,0.5);zg=ZG(sx_[np.argmin(np.linalg.norm(F(sx_)-[x,y],axis=1))])+zb;ztop=zh-hh-1.5;NPAN=max(6,int(round(ztop/4.5)))
    def leg(i,j,z):
        hw=1.8+(1.5-1.8)*(z-zg)/(ztop-zg);c=base+sd*i*hw+to*j*hw;return np.r_[c,z]
    cs=[(1,1),(-1,1),(-1,-1),(1,-1)]
    for i,j in cs:beam(leg(i,j,zg),leg(i,j,ztop),0.35,'steel')
    zs=np.linspace(zg,ztop,NPAN+1)
    for k in range(NPAN):
        za,zb=zs[k],zs[k+1]
        for q_ in range(4):
            (i0,j0),(i1,j1)=cs[q_],cs[(q_+1)%4]
            beam(leg(i0,j0,za),leg(i1,j1,zb),0.14,'steel');beam(leg(i1,j1,za),leg(i0,j0,zb),0.14,'steel');beam(leg(i0,j0,zb),leg(i1,j1,zb),0.16,'steel')
    tilt=math.radians(15);up=np.array([0,0,math.cos(tilt)])+np.r_[to,0]*math.sin(tilt);nrm=np.r_[to,0]*math.cos(tilt)-np.array([0,0,math.sin(tilt)])
    hc=np.array([x,y,zh])+np.r_[to,0]*0.2;sd3=np.r_[sd,0]
    # head copied from the photo: a lamp panel about 12 x 7 m, curved in plan (front view of A/B reads as a
    # rectangle, back view of C/D reads as an arch), tilted to the ground, on a service platform
    R_=8.7;to3=np.r_[to,0]
    def hp(ph,t_,f_):return hc+sd3*R_*math.sin(ph)-to3*R_*(1-math.cos(ph))+up*(t_*hh/2-hh/2)+nrm*f_
    PH=np.linspace(-0.61,0.61,13)
    for k in range(len(PH)-1):
        a0,a1=PH[k],PH[k+1]
        quad(hp(a1,-1,0.4),hp(a0,-1,0.4),hp(a0,1,0.4),hp(a1,1,0.4),'lamps',[(1,0),(0,0),(0,1),(1,1)])
        quad(hp(a0,-1,-0.4),hp(a1,-1,-0.4),hp(a1,1,-0.4),hp(a0,1,-0.4),'lampback',[(0,0),(1,0),(1,1),(0,1)])
        quad(hp(a0,1,-0.4),hp(a0,1,0.4),hp(a1,1,0.4),hp(a1,1,-0.4),'white')
        quad(hp(a1,-1,-0.4),hp(a1,-1,0.4),hp(a0,-1,0.4),hp(a0,-1,-0.4),'white')
    for ph in(PH[0],PH[-1]):quad(hp(ph,-1,-0.4),hp(ph,-1,0.4),hp(ph,1,0.4),hp(ph,1,-0.4),'white')
    pc=np.array([x,y,ztop])
    def pq(s_,t_,z_):return pc+sd3*s_*3.2+to3*t_*1.6+np.array([0,0,z_])
    quad(pq(-1,-1,0.2),pq(1,-1,0.2),pq(1,1,0.2),pq(-1,1,0.2),'steel')
    for s_ in(-1,1):beam(pq(s_,-1,0.2),pq(s_,-1,1.3),0.08,'white');beam(pq(s_,1,0.2),pq(s_,1,1.3),0.08,'white')
    beam(pq(-1,-1,1.3),pq(1,-1,1.3),0.08,'white');beam(pq(-1,1,1.3),pq(1,1,1.3),0.08,'white')
    for ph in(PH[0],0.0,PH[-1]):beam(hp(ph,-0.6,-0.4),pc+np.array([0,0,0.2]),0.25,'steel')
# near side (s 110-300): undercroft and paving matched to the photo's darker shade (mktex4 *_n textures)
_NS=np.arange(0,PER,0.5);_FX=F(_NS)
for _L,_M in((QV,QM),):
    for _i in range(len(_L)):
        _n=MATN[_M[_i]]
        if _n not in('pave','fvoid','fcol','fslab','underside','facade','aislec'):continue
        _c=np.mean(_L[_i],axis=0)[:2];_j=np.argmin(np.sum((_FX-_c)**2,axis=1));_s=_NS[_j];_d=float(np.linalg.norm(_FX[_j]-_c))
        if _n=='facade' and _d>38.0:continue   # the sheds keep their own shade
        if _n=='aislec' and _d<36.0:continue   # only the stairs and ramps outside the stand
        if 110<=_s<=300:
            if _n=='pave':   # near paving: the darker middle blends into the lighter ends over 20 m (5 steps), no hard seam
                _t=float(np.clip(min((_s-150)/20,(240-_s)/20),0,1));_M[_i]=mi('pave_b%d'%int(round(_t*4)))
            else:_M[_i]=mi(_n+'_n')
np.savez('mesh.npz',QV=np.array(QV,np.float32),QU=np.array(QU,np.float32),QM=np.array(QM,np.int32),TV=np.array(TV,np.float32),TU=np.array(TU,np.float32),TM=np.array(TM,np.int32))
json.dump(MATN,open('mats.json','w'))
print('quads',len(QV),'tris',len(TV),'mats',MATN)
# tower base distance to facade line (embedded check)
for x,y,zh,zb,hh in TW:
    sx=np.arange(0,PER,0.5);dd=np.linalg.norm(F(sx)-[x,y],axis=1);i=np.argmin(dd);print('tower',(x,y),'s',sx[i],'d from fence',round(dd[i],1))
