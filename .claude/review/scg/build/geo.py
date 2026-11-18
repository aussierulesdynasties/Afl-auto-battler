# SCG model geometry in world metres (x east, y north, z up), from OSM footprints + photo back-projection.
exec(open('meas.py').read())
MATS={'glasst':(48,104,176),'spand':(158,164,168),'cladl':(208,211,212),'ground':(70,70,72),'grass':(95,140,55),'apron':(120,120,115),'seat':(45,105,100),'wall':(200,195,185),
 'roof':(236,236,232),'roofu':(150,150,150),'fascia':(225,222,215),'facade':(222,200,165),'facade2':(205,205,205),
 'tower':(118,106,88),'lamp':(240,240,230),'screen':(25,30,45),'hroof':(85,150,80),'brick':(195,120,85),'glass':(50,55,65),'plant':(180,180,175),'headback':(124,113,112),'glassroof':(95,95,100),'stone':(214,210,200),'steel':(200,202,205),'glassm':(34,40,48),'fence':(238,238,234),'ribbon':(232,112,38),'soffit':(52,58,64),'rail':(150,152,154),'sbface':(26,28,32),'sbad':(242,168,40),'glassblk':(30,28,30)}
V=[];F=[]  # F: (i,j,k[,l], mat)
def v(x,y,z):V.append((x,y,z));return len(V)-1
def quad(a,b,c,d,m):F.append(((a,b,c,d),m))
def tri(a,b,c,m):F.append(((a,b,c),m))
def interp(tab,a):
    ks=sorted(tab);xs=np.array(ks,float);ys=np.array([tab[k] for k in ks],float);return float(np.interp(a,xs,ys))
def wrap(a,a0):  # bring degrees a into [a0,a0+360)
    return (a-a0)%360+a0
N=720
def pol(k):return polar(G[k])
GR=pol('4000006')
_GO=pol('598232976')[:,1]
def rw(d):return float(_GO[int(round((d%360)*2))%720])+7.5     # near-stand wall line: OSM grandstand outline, offset to the photo
def nearclamp(d,rb):return min(rb,rw(d)-4.5) if 168<=d%360<=256 else rb
def P(r,a,z):return v(PC[0]+r*math.cos(a),PC[1]+r*math.sin(a),z)
def band(profile,a0,a1,m,step=1):
    """profile(adeg)->list of (r,z) inner->outer; m mat per segment list. Builds strips over degrees a0..a1."""
    degs=np.arange(a0,a1+1e-6,step*0.5);rows=[]
    for d in degs:
        pr_=profile(d)
        rows.append(None if pr_ is None else [P(r,math.radians(d),z) for r,z in pr_])
    for i in range(len(rows)-1):
        A,B=rows[i],rows[i+1]
        if A is None or B is None or len(A)!=len(B):continue
        for j in range(len(A)-1):quad(A[j],B[j],B[j+1],A[j+1],m[j] if isinstance(m,list) else m)
def rr_at(Pp,d):
    i=int(round((d%360)*2))%720;return Pp[i]
# --- roofs: per stand, front/outer edge = OSM radius or a photo polyline back-projected at the measured height
def photo_edge(px,zfun):
    """px: photo pixel polyline; zfun(deg)->z. Returns (degs, r) sorted, resampled densely."""
    pts=[]
    for i in range(len(px)-1):
        for t in np.linspace(0,1,12,endpoint=False):pts.append(((1-t)*px[i][0]+t*px[i+1][0],(1-t)*px[i][1]+t*px[i+1][1]))
    pts.append(px[-1]);out=[]
    for u,w in pts:
        z=20.0
        for _ in range(6):X=at_z(u,w,z);d=math.degrees(theta(X));z=zfun(d)
        out.append((d,rr(X)))
    out.sort();return np.array(out)
def from_tab(A,d):return float(np.interp(d,A[:,0],A[:,1]))
TF={'203':{42:38,47:36,52:34.5,57:33.4,62:31.5,67:30.6,72:29.8,77:30.8,82:31.5,92:34.6,97:38.4,102:42.2,107:48},
    '203o':{42:37,47:37,57:39.8,62:41.5,67:43,72:44,77:46.9,87:53,97:54,107:50},
    '200':{-100:35,-75:35,-65:33.5,-60:32.5,-55:32.1,-50:31,-45:30.2,-40:30.2,-35:29.2,-30:29},
    '200o':{-100:37.5,-75:37.5,-70:36,-65:32.4,-60:32.2,-55:31.5,-50:30.4,-45:30.2,-40:29.6,-30:29.8}}
def zbot(d):  # Brewongle/Churchill outer fascia height: 21 m west, 24 m at the SE corner
    d=wrap(d,-250);return float(np.interp(d,[-191,-150,-135,-100],[21,21,24,24]))
BOT_O=photo_edge([(470,597),(530,603),(600,606),(700,604),(740,595),(760,588),(820,568),(855,560),(886,560),(913,548),(948,533),(978,514),(1002,483),(1017,437),(1023,391),(1021,372)],zbot)
TRU_O=photo_edge([(1024,339),(1022,320),(1019,306),(1015,291),(1009,277),(999,257),(987,238),(973,221),(957,205),(941,190),(923,176),(905,165),(887,154),(869,145),(832,130),(815,123)],lambda d:interp(TF['200o'],d))
TRU_F=photo_edge([(913,348),(916,331),(916,314),(914,298),(912,286),(908,276),(903,265)],lambda d:interp(TF['200'],d))
BOT_O[:,0]=np.where(BOT_O[:,0]>0,BOT_O[:,0]-360,BOT_O[:,0])  # west side angles as negative
BOT_O=BOT_O[np.argsort(BOT_O[:,0])]
STANDS={};GRISE=4.0
def osm_r(k,i):
    Pp=pol(k)
    return lambda d:rr_at(Pp,d)[i]
# Messenger: OSM plan to 107 deg; west half of the outer edge fitted to the roof's white edge in the reference + 063
# (out 9-16 m, down 8 m); the crescent then runs on to a point at ~113 deg (triangulated: r 122, z 42)
_mf,_mo=osm_r('195513203',0),osm_r('195513203',1)
_MDR={42:0,81:0,90:9,102:13,107:16};_MDZ={42:0,81:0,90:-8,107:-8}
def _mes_f(d):return _mf(d) if d<=104 else 99.4+(121.0-99.4)*((min(d,113)-104)/9)**1.5   # inner edge sweeps out to the tip
def _mes_o(d):
    if d<=107:return _mo(d)+interp(_MDR,d)
    return float(np.interp(d,[107,113],[_mo(107)+16,121.0]))
def _mes_zf(d):return interp(TF['203'],d) if d<=107 else float(np.interp(d,[107,113],[48,42]))
def _mes_zo(d):return interp(TF['203o'],d)+interp(_MDZ,d) if d<=107 else float(np.interp(d,[107,113],[42,42]))
STANDS['messenger']=(42,113,_mes_f,_mes_zf,_mes_o,_mes_zo)
STANDS['oreilly']=(-32,22,osm_r('195513197',0),lambda d:interp({-32:24.3,22:24.0},d),osm_r('195513197',1),lambda d:interp({-32:26.5,22:25.8},d))
_trf=osm_r('195513200',0)
STANDS['trumper']=(-105.8,-30,   # south end: a radial line at -105.8 deg, read off the photo at both roof edges
    lambda d:_trf(d) if d>-75 else from_tab(TRU_F,d),lambda d:interp(TF['200'],d),lambda d:from_tab(TRU_O,d),lambda d:interp(TF['200o'],d))
_chf=osm_r('659304331',0);_brf=osm_r('659304332',0)
def botf(d):
    d=wrap(d,-250)
    v_=_chf(d) if d>-138 else _brf(d)
    return v_
STANDS['bottom']=(-224+360-360,-101,lambda d:botf(d),lambda d:float(np.interp(wrap(d,-250),[-191,-138,-100],[15.9,15.5,14.5])),lambda d:from_tab(BOT_O,wrap(d,-250)),lambda d:zbot(d))
# photo: the roof's north end runs on under the Trumper's end on a slant, from -100 deg at the outer edge to -94 at the inner
_b=STANDS['bottom'];_xrf0,_xzf0,_xro0,_xzo0=_b[2:]
def _xbend(d):return 98.0+(134.6-98.0)*min(1.0,max(0.0,(-94.0-d)/6.0))
def _xro(d):return min(_xro0(d),_xbend(d)) if d>-100 else _xro0(d)
def _xzo(d):
    if d<=-100:return _xzo0(d)
    lo=_xrf(d);full=_xro0(d);return _xzf0(d)+(_xzo0(d)-_xzf0(d))*(_xro(d)-lo)/(full-lo)
def _xrf(d):return _xrf0(d) if d<=-100 else _xrf0(-100)
STANDS['bottom']=(-191,-94.5,_xrf,_xzf0,_xro,_xzo)
OUT={}
for k,(a0,a1,rf,zf,ro,zo) in STANDS.items():
    def prof(d,rf=rf,zf=zf,ro=ro,zo=zo):
        lo,hi=rf(d),ro(d)
        if np.isnan(lo) or np.isnan(hi) or hi-lo<4:return None
        return [(lo,zf(d)-1.6)]+[(lo+(hi-lo)*t,zf(d)+(zo(d)-zf(d))*t) for t in np.linspace(0,1,7)]
    if k=='messenger':
        # photos (reference + 063): a thin white rim at the field edge, then glazing with cross ribs sloping up 4 m to the
        # white blade (widest ~9 m mid-span, tapering to nothing at both ends); the blade rises from there to the back edge
        def gw(d,a0=a0,a1=106):return 9.0*math.sin(math.pi*min(1,max(0,(d-a0)/(a1-a0))))**0.6
        def pmes(d,rf=rf,zf=zf,ro=ro,zo=zo):
            lo,hi=rf(d),ro(d)
            if np.isnan(lo) or np.isnan(hi) or hi-lo<0.3:return None
            w=gw(d) if gw(d)>0.8 else 0.0;r1=lo+min(1.5,0.3*(hi-lo));r2=min(r1+w,lo+0.7*(hi-lo));w=r2-r1;rise=GRISE*min(1,w/4)
            Z=lambda r:(zf(d)+rise)+(zo(d)-zf(d)-rise)*(r-r2)/max(hi-r2,0.5)   # blade line from the glazing top to the back edge
            return [(lo,zf(d)-1.6),(lo,zf(d)),(r1,zf(d)),(r1,zf(d)-0.3),(r2,zf(d)+rise-0.3),(r2,zf(d)+rise)]+                   [(r2+(hi-r2)*t,Z(r2+(hi-r2)*t)) for t in np.linspace(0,1,6)[1:]]
        band(pmes,a0,a1,['fascia','roof','fascia','glassroof','fascia']+['roof']*5)
        GLASS_RIB=(a0,a1,rf,zf,ro,zo,gw)
    else:band(prof,a0,a1,['fascia']+['roof']*6)
    def under(d,rf=rf,zf=zf,ro=ro,zo=zo,thr=0.3 if k=='messenger' else 4):
        lo,hi=rf(d),ro(d)
        if np.isnan(lo) or np.isnan(hi) or hi-lo<thr:return None
        return [(hi,zo(d)-1.2),(lo,zf(d)-1.6)]
    band(under,a0,a1,'roofu')
    for d in np.arange(a0,a1+0.1,0.5):
        lo,hi=rf(d),ro(d)
        if k=='messenger' and d>107:continue   # the roof tip past 107 deg overhangs; the bowl below keeps its own line
        if k=='messenger':   # stand body on the OSM outer line; the fitted roof overhangs it (up to 16 m at the west end)
            hb=_mo(d);zu=(zf(d)-1.6)+((zo(d)-1.2)-(zf(d)-1.6))*(hb-lo)/(hi-lo);OUT[round(d*2)/2%360]=(lo,hb,zf(d),zu+1.2,k);continue
        if not(np.isnan(lo) or np.isnan(hi)) and hi-lo>=4:OUT[round(d*2)/2%360]=(lo,hi,zf(d),zo(d),k)
# --- Messenger glazed strip: cross ribs every ~3.5 m of the field edge (photo: ~28 ribs along the crescent)
a0,a1,rf,zf,ro,zo,gw=GLASS_RIB;_d=a0+1.0
while _d<a1-1.0:
    lo,hi=rf(_d),ro(_d);w=gw(_d)
    if not(np.isnan(lo) or np.isnan(hi)) and w>0.8:
        r1=lo+min(1.5,0.3*(hi-lo));r2=min(r1+w,lo+0.7*(hi-lo));w=r2-r1;h=0.15/lo;rise=GRISE*min(1,w/4)
        a=math.radians(_d);pts=[]
        for s_ in(-1,1):
            for r_,zz in((r1,zf(_d)-0.3),(r2,zf(_d)+rise-0.3)):pts.append((r_,a+s_*h,zz))
        b=[P(r_,aa,zz) for r_,aa,zz in pts];t=[P(r_,aa,zz+0.6) for r_,aa,zz in pts]
        quad(t[0],t[1],t[3],t[2],'fascia');quad(b[0],b[1],t[1],t[0],'fascia');quad(b[2],t[2],t[3],b[3],'fascia')
        quad(b[0],t[0],t[2],b[2],'fascia');quad(b[1],b[3],t[3],t[1],'fascia')
    _d+=math.degrees(3.5/lo) if not np.isnan(lo) else 1.0
exec(open('roofdet.py').read())
# --- facades under roof outer edge
def fac(d):
    o=OUT.get(round(d*2)/2%360)
    if not o:return None
    lo,hi,zf,zo,k=o
    if 168<=d%360<=256:return None   # near stand: modelled bay by bay in near.py
    if k in('messenger','trumper','oreilly'):return None
    return [(hi,0),(hi,zo-1.2)]
band(fac,-180,180,'facade')
# Trumper back (Gate 9 photo, ground to roof edge in shares of the wall height): recessed dark concourse to 22%,
# three blue glass storeys with grey floor spandrels to 74%, pale grey band to 83%, dark window strip to 89%,
# white cladding to the roof edge
def trumback(d):
    o=OUT.get(round(d*2)/2%360)
    if not o or o[4]!='trumper':return None
    lo,hi,zf,zo,k=o;zt=zo-1.2;zc=0.22*zt;zg=0.74*zt;s=(zg-zc)/3
    return [(hi-3,0),(hi-3,zc-0.6),(hi,zc-0.6),(hi,zc),(hi,zc+s-0.9),(hi,zc+s),(hi,zc+2*s-0.9),(hi,zc+2*s),(hi,zg),
            (hi,0.83*zt),(hi,0.89*zt),(hi,zt)]
band(trumback,-105.8,-30,['dark','slab','slab','glasst','spand','glasst','spand','glasst','cladl','glassblk','facade'])
# O'Reilly back: no photo of its face. Built to the Trumper's own lines: the same ground concourse (set back 3 m under the
# rake, soffit at the Trumper's height at the join), then shaded concourse glazing in two storeys with a grey floor
# spandrel, then the Trumper's top bands (pale band, dark window strip, white cladding) that the Gate 9 photo shows
# running on round the curve. The wall stays flush above the concourse: the seat rake's back row is only 0.7 m inside.
ZC_J=0.22*(29.7-1.2)   # Trumper concourse soffit height at the join (-30 deg)
def oreback(d):
    o=OUT.get(round(d*2)/2%360)
    if not o or o[4]!='oreilly':return None
    lo,hi,zf,zo,k=o;zt=zo-1.2;zb=0.74*zt;s2=(zb-ZC_J)/2
    return [(hi-3,0),(hi-3,ZC_J-0.6),(hi,ZC_J-0.6),(hi,ZC_J),(hi,ZC_J+s2-0.9),(hi,ZC_J+s2),(hi,zb),(hi,0.83*zt),(hi,0.89*zt),(hi,zt)]
band(oreback,-32,22,['dark','slab','slab','glassm','spand','glassm','cladl','glassblk','facade'])
# Trumper/O'Reilly join: the Trumper's last slice (-30.5) reaches 123 m out, the O'Reilly's first (-30) only 94.6 m, so the
# seat rake twists across the wedge between them. A radial end wall at -30 carries the O'Reilly's bands out to the
# Trumper's wall and up to the Trumper's top, so the two backs meet and no seats show.
def _joinwall(d=-30.0):
    o=OUT[round(d*2)/2%360];zt=o[3]-1.2;r0=o[1];r1=OUT[round((d-0.5)*2)/2%360][1];zT=OUT[round((d-0.5)*2)/2%360][3]-1.2
    pr=oreback(d);zs=[z for _,z in pr[3:]]+[zT];ms=['glassm','spand','glassm','cladl','glassblk','facade','facade']
    zs=[0.0,ZC_J-0.6]+zs;ms=['dark','slab']+ms
    a=math.radians(d)
    for i in range(len(zs)-1):
        if zs[i+1]-zs[i]<1e-3:continue
        quad(P(r0,a,zs[i]),P(r1,a,zs[i]),P(r1,a,zs[i+1]),P(r0,a,zs[i+1]),ms[i])
_joinwall()
# Messenger back (photo 063, east end): pale stone-panel podium ~18 m on the plan line, terrace with glass balustrade,
# glazed upper concourse set 5 m in, running up to the roof underside; steel V-struts from the stand top to the roof
MPOD=23.0   # podium top, 063 photo back-projected onto the plan line: 24, 24, 22 m at 44.5, 48.5, 51.7 deg
def mund(d,r,lo):return (_mes_zf(d)-1.6)+((_mes_zo(d)-1.2)-(_mes_zf(d)-1.6))*(r-lo)/(_mes_o(d)-lo)-0.1   # Messenger roof underside at r
def mesback(d):
    o=OUT.get(round(d*2)/2%360)
    if not o or o[4]!='messenger':return None
    lo,hi,zf,zo,k=o;top=max(MPOD+5.6,mund(d,hi-5,lo))
    # podium, glass balustrade, terrace, then the concourse 5 m in: white upstand, window band, white band, shaded void to the roof
    return [(hi,0),(hi,MPOD),(hi,MPOD+1.1),(hi,MPOD),(hi-5,MPOD),(hi-5,MPOD+1.2),(hi-5,MPOD+4.2),(hi-5,MPOD+5.2),(hi-5,top)]
band(mesback,44.5,107,['stone','glass','glass','slab','wall','glassm','wall','dark'])
def mescore(d):   # 42-44.5 deg: concrete stair core beside the podium (063 photo x 690-755)
    o=OUT.get(round(d*2)/2%360)
    if not o or o[4]!='messenger':return None
    lo,hi,zf,zo,k=o;return [(hi,0),(hi,MPOD+2),(hi-5,MPOD+2),(hi-5,max(MPOD+3,mund(d,hi-5,lo)))]
band(mescore,42,44.5,['conc','slab','dark'])
_d=44.0
while _d<106:
    o=OUT.get(round(_d*2)/2%360)
    if o:
        lo,hi,zf,zo,k=o;a=math.radians(_d);ru=_mes_o(_d);zr=_mes_zo(_d)-1.2
        zs=(zf-1.6)+(zr-(zf-1.6))*((hi-3)-lo)/(ru-lo)   # roof underside above the strut tops
        for s_ in(-1,1):
            A=np.array([PC[0]+(hi-5)*math.cos(a),PC[1]+(hi-5)*math.sin(a),MPOD+5.2])
            ab=a+s_*4.0/hi;Bp=np.array([PC[0]+(hi-3)*math.cos(ab),PC[1]+(hi-3)*math.sin(ab),zs])
            ax=Bp-A;ax/=np.linalg.norm(ax);q=np.cross(ax,[0,0,1.0]);q/=np.linalg.norm(q);q2=np.cross(ax,q);rad=0.25
            ring0=[v(*(A+rad*(math.cos(t)*q+math.sin(t)*q2))) for t in np.linspace(0,2*math.pi,7)[:-1]]
            ring1=[v(*(Bp+rad*(math.cos(t)*q+math.sin(t)*q2))) for t in np.linspace(0,2*math.pi,7)[:-1]]
            for i in range(6):quad(ring0[i],ring0[(i+1)%6],ring1[(i+1)%6],ring1[i],'steel')
    _d+=math.degrees(15.0/130)
NEAR0=len(F);exec(open('near.py').read());NEAR1=len(F)
# --- seating bowl: grass edge -> back under roof
# upper-deck front with its LED ribbon (reference photo, back-projected onto the rake): 14 m back from the grass on the
# north stands (-31..22 deg), 26 m on the east stands (-46..-76 deg); none seen on the Messenger or heritage stands
RIB={-104:26.0,-38.5:26.0,-38:14.0,30:14.0}   # one step at -38 deg, behind the stair tower in the photo
def seats(d):
    g=rr_at(GR,d)[1]
    o=OUT.get(round(d*2)/2%360)
    if o is None and 106.5<d%360<112:o=OUT[106.5]   # photo: the Messenger lower bowl runs on past its roof to the Members' Pavilion
    if o is None:
        if 112<=d%360<=168:rb,zb=g+18,7.0   # heritage bleachers
        else:rb,zb=g+22,10.0
    else:
        lo,hi,zf,zo,k=o;rb=nearclamp(d,hi-(5.0 if k=='messenger' else 1.0));zb=min(zf*0.62,zo-4)
    sl=lambda r:1.2+(zb-1.2)*(r-g-3)/(rb-g-3)
    dd=(d+180)%360-180;D=interp(RIB,dd) if -104<=dd<=30 and o is not None else None
    if D is None or not(g+8<g+D<rb-4):
        rD=(g+3+rb)/2;zD=sl(rD);mid=[(rD,zD)]*6
    else:
        rD=g+D;zD=sl(rD-3.0);mid=[(rD-3.0,zD),(rD,zD),(rD,zD+1.2),(rD-1.0,zD+1.2),(rD-1.0,zD+2.2),(rD-0.4,zD+2.2)]   # photo: a shaded cross-aisle (~2 m seen) under the ribbon's 1 m overhang
    lower=[(g+3+(mid[0][0]-g-3)*t,sl(g+3+(mid[0][0]-g-3)*t)) for t in (0.5,)]
    u0=mid[-1];upper=[(u0[0]+(rb-u0[0])*t,u0[1]+(zb-u0[1])*t) for t in (0.33,0.67,1.0)]
    return [(g+2.5,0.05),(g+3,1.2)]+lower+mid+upper   # director: leave the field out (game draws grass inside the fence)
band(seats,-180,180,['fence','seat','seat','dark','dark','dark','ribbon','slab','seat','seat','seat'])
# end wall where that bowl stops at the Members' Pavilion (112 deg)
_pr=seats(111.9);_a=math.radians(112);_rb=_pr[-1][0];_b=P(_rb,_a,0)
_pv=[P(r_,_a,z_) for r_,z_ in _pr]
for i in range(len(_pv)-1):tri(_b,_pv[i+1],_pv[i],'wall')
# sandstone end pier of the stand beside the Members' Pavilion (photo x 442-488, y 535-647): 165-169.5 deg, r 99-121, 16 m
def polar_box(a0,a1,r0,r1,z,m):
    A0,A1=math.radians(a0),math.radians(a1)
    c=[P(r_,a_,h_) for h_ in (0,z) for a_ in (A0,A1) for r_ in (r0,r1)]
    for f in ((0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5),(4,5,7,6)):quad(*[c[i] for i in f],m)
polar_box(165,169.5,99,121,16.0,'brick')
def backwall(d):
    o=OUT.get(round(d*2)/2%360)
    if o and o[4]!='messenger':lo,hi,zf,zo,k=o;rb=nearclamp(d,hi-1.0);zb=min(zf*0.62,zo-4);return [(rb,zb),(rb,zo-1.2)]   # Messenger: its concourse wall (mesback) closes the back
band(backwall,-180,180,'wall')
# --- grass
_gd=np.arange(0,360,2.0);_gr=[rr_at(GR,d)[1] for d in _gd];_K=8
_rings=[[P(_gr[i]*(k/_K),math.radians(d),0.05) for i,d in enumerate(_gd)] for k in range(1,_K+1)]
c=v(PC[0],PC[1],0.05)
for i in []:   # director 2026-11-18: "Leave field out"
    j=(i+1)%len(_gd);tri(c,_rings[0][i],_rings[0][j],'grass')
    for k in range(_K-1):quad(_rings[k][i],_rings[k][j],_rings[k+1][j],_rings[k+1][i],'grass')
# --- light towers: 68 m, 12-sided, 2.3 m across at the base tapering to 1.5 m under the head (photo widths);
# head = 7.7 m wide x 9.5 m panel, tilted 30 deg to face down onto the field, lamps on the field side
cj=json.load(open('cam.json'));HT=cj['p'][9]
TOWERS=[]
for (x,y) in cj['T']:
    n=12;rb_,rt_=1.15,0.75;zt=HT-4.0
    bot=[v(x+rb_*math.cos(2*math.pi*i/n),y+rb_*math.sin(2*math.pi*i/n),0) for i in range(n)]
    top=[v(x+rt_*math.cos(2*math.pi*i/n),y+rt_*math.sin(2*math.pi*i/n),zt) for i in range(n)]
    for i in range(n):quad(bot[i],bot[(i+1)%n],top[(i+1)%n],top[i],'tower')
    a=math.atan2(PC[1]-y,PC[0]-x);f=np.array([math.cos(a),math.sin(a),0.0]);u=np.array([-math.sin(a),math.cos(a),0.0])
    tilt=math.radians(30);up=np.array([0,0,1.0])*math.cos(tilt)+f*math.sin(tilt)   # panel 'up' leans toward the field
    nrm=np.cross(u,up);nrm=nrm if nrm@f<0 else -nrm   # back normal (away from field)
    base=np.array([x,y,zt])-f*0.2;hw,hh,dp=3.85,9.5,0.9
    def Pt(s,t,q):X=base+s*hw*u+t*hh*up+q*dp*nrm;return v(*X)
    B={(s,t,q):Pt(s,t,q) for s in(-1,1) for t in(0,1) for q in(0,1)}
    quad(B[-1,0,0],B[1,0,0],B[1,1,0],B[-1,1,0],'lamp')
    quad(B[-1,0,1],B[-1,1,1],B[1,1,1],B[1,0,1],'headback')
    quad(B[-1,1,0],B[1,1,0],B[1,1,1],B[-1,1,1],'tower');quad(B[-1,0,0],B[-1,0,1],B[1,0,1],B[1,0,0],'tower')
    quad(B[-1,0,0],B[-1,1,0],B[-1,1,1],B[-1,0,1],'tower');quad(B[1,0,0],B[1,0,1],B[1,1,1],B[1,1,0],'tower')
    TOWERS.append((x,y))
# --- extrude a photo outline at height z (back-projected) down to the ground; roof hips up 'rise' metres
def photo_block(px,ze,rise,mwall,mroof,shrink=0.55):
    W_=[at_z(u_,w_,ze)[:2] for u_,w_ in px];W_=np.array(W_);c_=W_.mean(0);n=len(W_)
    lo=[v(*W_[i],0) for i in range(n)];hi=[v(*W_[i],ze) for i in range(n)]
    top=[v(*(c_+(W_[i]-c_)*shrink),ze+rise) for i in range(n)]
    cc=v(*c_,ze+rise)
    for i in range(n):
        j=(i+1)%n;quad(lo[i],lo[j],hi[j],hi[i],mwall);quad(hi[i],hi[j],top[j],top[i],mroof);tri(top[i],top[j],cc,mroof)
    return W_
HER=[  # heritage Members' and Ladies' stands: green-roof outlines read off the photo grid; eaves 13 m (brick wall heights measured 12.8-15.4 m)
 # Ladies' Stand: three stepped gabled sections read off g/hz4 (back block, middle block with the dormers, front block)
 ([(251,407),(306,402),(306,413),(318,433),(306,440),(248,447),(248,431),(245,417)],15.0,4.5),
 ([(234,432),(248,431),(248,447),(306,440),(318,433),(327,443),(333,458),(307,461),(254,482),(252,478),(239,462),(238,448)],14.0,4.0),
 ([(254,482),(307,461),(333,458),(343,482),(356,495),(350,503),(331,520),(303,523),(279,495),(258,501)],13.0,4.0),
 ([(350,503),(368,496),(388,505),(392,513),(413,521),(420,575),(408,580),(405,586),(391,583),(391,594),(384,590),(379,601),(355,599),(344,590),(343,581),(352,560),(342,556),(340,549),(322,539),(320,533),(312,528),(318,523),(331,526)],13.0,5.0),
 ([(422,528),(435,595),(447,601),(446,579),(452,554),(458,548),(471,549),(477,547),(462,544),(428,527)],11.0,3.0),
 ([(224,509),(229,519),(235,522),(233,535),(245,538),(271,526),(252,501),(235,498)],13.0,3.5),
 ([(300,528),(283,533),(279,541),(267,541),(274,556),(292,550),(294,545),(305,540)],12.0,3.0),
 ([(212,474),(220,492),(242,487),(246,482),(239,468),(222,468)],13.0,3.0)]
exec(open('herit.py').read())
HZ=[hiproof(px_world(px,ze),ze,0.75,rise,'hroof','brick',gable=True) for px,ze,rise in HER]
# Ladies' Stand roof: two dormer lanterns read off the photo grid (px 253-268 x 461-469 and 275-288 x 452-459)
for (u0,w0,u1,w1) in ((253,461,268,469),(275,452,288,459)):
    a_,b_=np.array(px_world([(u0,(w0+w1)/2)],14)[0]),np.array(px_world([(u1,(w0+w1)/2)],14)[0])
    c_=(a_+b_)/2;ln_=float(np.linalg.norm(b_-a_));wd_=float(np.linalg.norm(np.array(px_world([(u0,w1)],14)[0])-np.array(px_world([(u0,w0)],14)[0])))
    zr=HZ[1](c_);gablebox(c_[0],c_[1],math.atan2(*(b_-a_)[::-1]),ln_,wd_,zr-1.0,zr+1.6,1.2,'hroof','glassblk','hroof')
# Members Pavilion: the pediment gable facing the field under the clock tower (refs3/028)
_t=np.array([-62.5,70.2]);_f=np.array(PC)-_t;_f=_f/np.linalg.norm(_f);_c=_t+_f*4.5
gablebox(_c[0],_c[1],math.atan2(_f[1],_f[0]),9.0,10.0,0,13.0,3.6,'hroof','brick','stone')
# Ladies' Stand: round brick tower at the back corner (16.8 m across, read off the photo), domed green roof
prism(-107.0,41.8,8.4,28,0,13.0,'brick');cone(-107.0,41.8,8.9,28,13.0,18.5,'hroof',bulge=1)
# Ladies' Stand cupola on the field-side corner; Members' clock tower on the main roof (photo 306,443 / 397,535)
for cx,cy,w,z0,z1,z2 in ((-97.0,35.0,1.6,15.0,21.5,24.5),(-62.5,70.2,2.0,15.0,23.0,27.0)):
    prism(cx,cy,w,4,z0,z1,'stone',math.pi/4);cone(cx,cy,w*1.15,4,z1,z1+0.4,'hroof',math.pi/4);cone(cx,cy,w*0.95,16,z1+0.4,z2,'hroof',bulge=1)
    prism(cx,cy,0.08,4,z2,z2+1.6,'steel')
# dark glass building behind the Messenger stand (roof edge 35.5 m measured from its base)
pass   # removed: not part of the stadium (director: stadium only, background pass later)
# --- scoreboard (east-north-east, behind the O'Reilly/Messenger gap): level board, face yaw solved from the photo.
# Screen photo x 437..503, orange panel x 503..517 (same height); corners checked against the photo to 2-5 px.
SB=[(87.3,57.0),(91.2,31.8)];zb0,zb1=8.2,25.1
fx_,fy_=math.cos(math.radians(189)),math.sin(math.radians(189))
_sA,_sB=np.array(SB[0]),np.array(SB[1])
def _sbp(t):return _sA+(_sB-_sA)*t
DECALS={}
def sbpanel(t0,t1,z0,z1,m,depth=3.0):
    P0,P1=_sbp(t0),_sbp(t1)
    def q(X,z,off):return v(X[0]-fx_*off,X[1]-fy_*off,z)
    a1,a2,b2,b1=q(P0,z0,0),q(P1,z0,0),q(P1,z1,0),q(P0,z1,0)
    c1,c2,d2,d1=q(P0,z0,depth),q(P1,z0,depth),q(P1,z1,depth),q(P0,z1,depth)
    F.append(((a1,a2,b2,b1),m));quad(c2,c1,d1,d2,'facade2');quad(a2,c2,d2,b2,'facade2');quad(c1,a1,b1,d1,'facade2');quad(b1,b2,d2,d1,'facade2');quad(a1,c1,c2,a2,'facade2')
    d_=(P1-P0);W_=float(np.linalg.norm(d_));DECALS[m]={'o':[float(P0[0]),float(P0[1])],'d':[float(d_[0]/W_),float(d_[1]/W_)],'w':W_,'z0':z0,'z1':z1}
sbpanel(0.0,0.955,zb0,zb1,'sbface',0.8);sbpanel(0.955,1.165,zb0,zb1+0.5,'sbad',0.8)
sbpanel(0.02,0.62,4.0,zb0,'facade2',1.0)   # grey base wall under the board's left half (photo)
json.dump(DECALS,open('decals.json','w'))
for k_ in (0.1,0.5,0.85):   # legs down to the stand behind the board
    X0=_sbp(k_)
    q=[v(X0[0]+dx-fx_*1.5,X0[1]+dy-fy_*1.5,z) for dx,dy in ((-1,-1),(1,-1),(1,1),(-1,1)) for z in (0,zb0)]
    for i in range(4):j=(i+1)%4;quad(q[2*i],q[2*j],q[2*j+1],q[2*i+1],'facade2')
# --- close each roofed stand's end: seat bowl, back wall and facade make one solid cross-section
def earclip(pts):
    """triangulate a simple 2-D polygon (list of (x,y)); returns index triples. Drops repeated points first."""
    idx=[i for i in range(len(pts)) if i==0 or abs(pts[i][0]-pts[i-1][0])+abs(pts[i][1]-pts[i-1][1])>1e-6]
    if abs(pts[idx[-1]][0]-pts[idx[0]][0])+abs(pts[idx[-1]][1]-pts[idx[0]][1])<1e-6:idx=idx[:-1]
    A=sum(pts[idx[i]][0]*pts[idx[(i+1)%len(idx)]][1]-pts[idx[(i+1)%len(idx)]][0]*pts[idx[i]][1] for i in range(len(idx)))
    if A<0:idx=idx[::-1]
    cr=lambda a,b,c:(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def inside(p_,a,b,c):return cr(a,b,p_)>=-1e-9 and cr(b,c,p_)>=-1e-9 and cr(c,a,p_)>=-1e-9
    out=[];guard=0
    while len(idx)>3 and guard<5000:
        guard+=1;n=len(idx)
        for i in range(n):
            ia,ib,ic=idx[i-1],idx[i],idx[(i+1)%n];a,b,c=pts[ia],pts[ib],pts[ic]
            if cr(a,b,c)<=1e-9:continue
            if any(inside(pts[j],a,b,c) for j in idx if j not in(ia,ib,ic)):continue
            out.append((ia,ib,ic));idx.pop(i);break
        else:idx.pop(0)   # degenerate remainder
    if len(idx)==3:out.append(tuple(idx))
    return out
def stand_cap(d):
    o=OUT.get(round(d*2)/2%360)
    if not o:return
    lo,hi,zf,zo,k=o;a=math.radians(d);pr=seats(d);rb,zb=pr[-1]
    ring=[(pr[0][0],0)]+list(pr)+[(rb,zo-1.2),(hi,zo-1.2),(hi,0)]
    pv=[P(r_,a,z_) for r_,z_ in ring]
    for i,j,l in earclip(ring):tri(pv[i],pv[j],pv[l],'soffit' if k=='messenger' else 'facade')   # 063: dark stepped underside at the Messenger's east end
    # roof end strip
    rp=[(lo,zf-1.6)]+[(lo+(hi-lo)*t,zf+(zo-zf)*t) for t in np.linspace(0,1,7)]+[(hi,zo-1.2)]
    rv=[P(r_,a,z_) for r_,z_ in rp]
    for i,j,l in earclip(rp):tri(rv[i],rv[j],rv[l],'fascia')
def own_end(k,d,step):
    while (OUT.get(round(d*2)/2%360) or (0,0,0,0,None))[4]!=k:d+=step
    return d
for k,(a0,a1,*_) in STANDS.items():
    for d,st in ((a0,0.5),(min(a1,107) if k=='messenger' else a1,-0.5)):stand_cap(own_end(k,d,st))
# concourse columns under the Trumper and O'Reilly backs (Gate 9 photo), about every 9 m along the front line
for k_,a0_,a1_,share in (('trumper',-105.8,-30,0.22),('oreilly',-30,22,None)):
    for d_ in np.arange(a0_+1.5,a1_-1.0,0.5):
        o=OUT.get(round(d_*2)/2%360)
        if not o or o[4]!=k_:continue
        lo,hi,zf,zo,_k=o;rc=hi-0.6
        if int(round(d_*2))%int(round(2*math.degrees(9.0/rc)))!=0:continue
        a_=math.radians(d_);prism(PC[0]+rc*math.cos(a_),PC[1]+rc*math.sin(a_),0.45,12,0,(share*(zo-1.2) if share else ZC_J)-0.6,'conc')
