# SCG model geometry in world metres (x east, y north, z up), from OSM footprints + photo back-projection.
exec(open('meas.py').read())
MATS={'glasst':(48,104,176),'spand':(158,164,168),'cladl':(208,211,212),'ground':(70,70,72),'grass':(95,140,55),'apron':(120,120,115),'seat':(45,105,100),'seatm':(104,40,46),'wall':(200,195,185),
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
def rw(d):return interp(SP['bot_o'],wrap(d,-250))-0.5     # near-stand wall line: 0.5 m inside the satellite roof edge
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
TF={'203':{42:38,47:36,52:34.5,57:33.4,62:31.5,67:30.6,72:29.8,77:30.8,82:31.5,89:29.5,95.5:27.5,98.5:29.2,102:31.5,106:34.5,107:35.3},   # 95.5-106: heritage field photo, back-projected
    '203o':{42:37,47:37,57:39.8,62:41.5,67:43,72:44,77:46.9,87:51,97:43,107:37},
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
exec(open('sat_plan.py').read())
def _sp(k):return lambda d:interp(SP[k],d)
_mf0=_sp('mes_f');_mes_o=_sp('mes_o')
def _mes_f(d):return float(np.mean([_mf0(d+e) for e in np.arange(-1.5,1.51,0.25)]))   # +-1.5 deg mean: rounds the corners of the hand-traced satellite polyline (the real field edge is one smooth curve)
def _mes_zf(d):return interp(TF['203'],d)
def _mes_zo(d):return interp(TF['203o'],d)
MLOW=97.5   # heritage photo: the Messenger's upper tier and podium end here; only the low bowl and roof tip go on
STANDS['messenger']=(42.5,107,   # roof end at 42.5 deg: photo 063 (solved camera) puts the roof end at 41.8 with the NE light tower (41.7 deg, r 115.3) standing at its back corner; 42.5 leaves 0.5 m clear of the shaft
  _mes_f,_mes_zf,_mes_o,_mes_zo)
STANDS['oreilly']=(-34,18,_sp('ore_f'),lambda d:interp({-32:24.3,22:24.0},d),_sp('ore_o'),lambda d:interp({-32:26.5,22:25.8},d))
_trf=osm_r('195513200',0)
STANDS['trumper']=(-99.5,-34.5,_sp('tru_f'),lambda d:interp(TF['200'],d),_sp('tru_o'),lambda d:interp(TF['200o'],d))
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
STANDS['bottom']=(-190.5,-100,lambda d:interp(SP['bot_f'],wrap(d,-250)),_xzf0,lambda d:interp(SP['bot_o'],wrap(d,-250)),_xzo0)
OUT={}
for k,(a0,a1,rf,zf,ro,zo) in STANDS.items():
    def prof(d,rf=rf,zf=zf,ro=ro,zo=zo):
        lo,hi=rf(d),ro(d)
        if np.isnan(lo) or np.isnan(hi) or hi-lo<4:return None
        return [(lo,zf(d)-1.6)]+[(lo+(hi-lo)*t,zf(d)+(zo(d)-zf(d))*t) for t in np.linspace(0,1,7)]
    if k=='messenger':
        # photos (reference + 063): a thin white rim at the field edge, then glazing with cross ribs sloping up 4 m to the
        # white blade (widest ~9 m mid-span, tapering to nothing at both ends); the blade rises from there to the back edge
        def _gw0(d):return max(0.0,interp(SP['mes_w'],d)-_mes_f(d)-1.5)
        def gw(d):return float(np.mean([_gw0(d+e) for e in np.arange(-2.5,2.51,0.25)]))   # +-2.5 deg mean: the two satellite traces have knots at different angles, raw difference ripples ~1 m (saw-tooth glass top)
        def pmes(d,rf=rf,zf=zf,ro=ro,zo=zo):
            lo,hi=rf(d),ro(d)
            if np.isnan(lo) or np.isnan(hi) or hi-lo<0.3:return None
            w=gw(d);r1=lo+min(1.5,0.3*(hi-lo));r2=min(r1+w,lo+0.7*(hi-lo));w=r2-r1;rise=GRISE*min(1,w/4)
            Z=lambda r:(zf(d)+rise)+(zo(d)-zf(d)-rise)*(r-r2)/max(hi-r2,0.5)   # blade line from the glazing top to the back edge
            dp=0.3*min(1.0,w/1.5)   # glass sits 0.3 m below the rim; the step fades out where the glazing tapers to nothing
            return [(lo,zf(d)-1.6),(lo,zf(d)),(r1,zf(d)),(r1,zf(d)-dp),(r2,zf(d)+rise-dp),(r2,zf(d)+rise)]+                   [(r2+(hi-r2)*t,Z(r2+(hi-r2)*t)) for t in np.linspace(0,1,6)[1:]]
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
        if k=='messenger' and (d>107 or d<42):continue   # roof only before 42 deg (satellite: white roof over the scoreboard end, no stand body)   # the roof tip past 107 deg overhangs; the bowl below keeps its own line
        if k=='messenger':   # stand body on the OSM outer line; the fitted roof overhangs it (up to 16 m at the west end)
            hb=min(_mo(d),hi);zu=(zf(d)-1.6)+((zo(d)-1.2)-(zf(d)-1.6))*(hb-lo)/(hi-lo);OUT[round(d*2)/2%360]=(lo,hb,zf(d),zu+1.2,k);continue
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
band(trumback,-99.5,-34.5,['dark','slab','slab','glasst','spand','glasst','spand','glasst','cladl','glassblk','facade'])
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
band(oreback,-34,18,['dark','slab','slab','glassm','spand','glassm','cladl','glassblk','facade'])
# Trumper/O'Reilly join: the Trumper's last slice (-30.5) reaches 123 m out, the O'Reilly's first (-30) only 94.6 m, so the
# seat rake twists across the wedge between them. A radial end wall at -30 carries the O'Reilly's bands out to the
# Trumper's wall and up to the Trumper's top, so the two backs meet and no seats show.
def _joinwall(d=-34.0):
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
band(mesback,44.5,MLOW,['stone','glass','glass','slab','wall','glassm','wall','dark'])
def mescore(d):   # 42-44.5 deg: concrete stair core beside the podium (063 photo x 690-755)
    o=OUT.get(round(d*2)/2%360)
    if not o or o[4]!='messenger':return None
    lo,hi,zf,zo,k=o;return [(hi,0),(hi,MPOD+2),(hi-5,MPOD+2),(hi-5,max(MPOD+3,mund(d,hi-5,lo)))]
band(mescore,42,44.5,['conc','slab','dark'])
_d=44.0
while _d<MLOW-1:
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
    if 110<d%360<169.5:return None   # heritage bowl: its own band (hseats)
    if o is None and 106.5<d%360<110:o=OUT[106.5]   # photo: the Messenger lower bowl runs on past its roof to the Members' Pavilion
    if o is None:
        rb,zb=g+22,10.0
    else:
        lo,hi,zf,zo,k=o;rb=nearclamp(d,hi-(5.0 if k=='messenger' else 1.0));zb=min(zf*0.62,zo-4)
        if k=='messenger' and d%360>=MLOW:rb,zb,o=g+7.5,4.0,None   # heritage photo: only a low ~8-row bowl from 97.5 deg to the Members'
    sl=lambda r:1.2+(zb-1.2)*(r-g-0.5)/(rb-g-0.5)
    dd=(d+180)%360-180;D=interp(RIB,dd) if -104<=dd<=30 and o is not None else None
    if D is None or not(g+8<g+D<rb-4):
        rD=(g+0.5+rb)/2;zD=sl(rD);mid=[(rD,zD)]*6
    else:
        rD=g+D;zD=sl(rD-3.0);mid=[(rD-3.0,zD),(rD,zD),(rD,zD+1.2),(rD-1.0,zD+1.2),(rD-1.0,zD+2.2),(rD-0.4,zD+2.2)]   # photo: a shaded cross-aisle (~2 m seen) under the ribbon's 1 m overhang
    lower=[(g+0.5+(mid[0][0]-g-0.5)*t,sl(g+0.5+(mid[0][0]-g-0.5)*t)) for t in (0.5,)]
    u0=mid[-1];upper=[(u0[0]+(rb-u0[0])*t,u0[1]+(zb-u0[1])*t) for t in (0.33,0.67,1.0)]
    return [(g,0.05),(g+0.5,1.2)]+lower+mid+upper   # director: leave the field out (game draws grass inside the fence)
band(seats,-180,180,['fence','seat','seat','dark','dark','dark','ribbon','slab','seat','seat','seat'])
# heritage bowl (110-169.5 deg): maroon lower-tier seats from the fence up to the stands' field edge (satellite + field
# photo), topping out 1.5 m under the verandah so the stand faces show from the verandah up
exec(open('blds.py').read())
_HF=[fr_xy('L',-3,0),fr_xy('L',42,0),fr_xy('M',0,0),fr_xy('M',47.5,0)]
def hfront(d):
    a=math.radians(d);dx,dy=math.cos(a),math.sin(a);best=None
    for (x0,y0),(x1,y1) in zip(_HF[:-1],_HF[1:]):
        ex,ey=x1-x0,y1-y0;den=dx*(-ey)-dy*(-ex)
        if abs(den)<1e-9:continue
        qx,qy=x0-PC[0],y0-PC[1];t=(qx*(-ey)-qy*(-ex))/den;u=(dx*qy-dy*qx)/den
        if t>0 and -1e-6<=u<=1+1e-6:best=t if best is None else min(best,t)
    return best
HZB={'L':2.4,'M':1.0}   # lower-tier floor at the stand front, back-projected from the field photo (column bases)
_LM=math.degrees(math.atan2(_HF[1][1]-PC[1],_HF[1][0]-PC[0]))%360   # Ladies'/Members' join angle
def hseats(d):
    g=rr_at(GR,d)[1];rb=hfront(d)
    if rb is None:rb=g+14
    return [(g,0.05),(g+0.5,1.2),(rb,HZB['L'] if d%360>_LM else HZB['M'])]
band(hseats,110,169.5,['fence','seatm'])
# end wall where that bowl stops at the Members' Pavilion (112 deg)
_pr=seats(109.9);_a=math.radians(110);_rb=_pr[-1][0];_b=P(_rb,_a,0)
_pv=[P(r_,_a,z_) for r_,z_ in _pr]
for i in range(len(_pv)-1):tri(_b,_pv[i+1],_pv[i],'wall')
# sandstone end pier of the stand beside the Members' Pavilion (photo x 442-488, y 535-647): 165-169.5 deg, r 99-121, 16 m
def polar_box(a0,a1,r0,r1,z,m):
    A0,A1=math.radians(a0),math.radians(a1)
    c=[P(r_,a_,h_) for h_ in (0,z) for a_ in (A0,A1) for r_ in (r0,r1)]
    for f in ((0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5),(4,5,7,6)):quad(*[c[i] for i in f],m)
polar_box(165,169.5,99,121,16.0,'ashlar')
# Messenger end beside the Members' (heritage photo x 1000-1200): low bowl's back wall and concourse deck, then a dark
# brick block set back (photo x 1060-1160, top y 380 = 19.5 m at r 110)
def mlowback(d):
    g=rr_at(GR,d)[1];return [(g+7.5,4.0),(g+7.5,7.0),(g+16,7.0)]
band(mlowback,MLOW,110,['wall','slab'])
polar_box(105,110,108,120,19.5,'brick')
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
exec(open('herit.py').read())
exec(open('herbld.py').read())   # heritage stands: clean gabled/hipped buildings (blds.py)
# Ladies' Stand: round tower at the back (satellite/OSM curve), brick with sash windows, green dome
_rx,_ry=fr_xy(*ROT[:3]);prism(_rx,_ry,ROT[3],40,0,11.0,'hw110');cone(_rx,_ry,ROT[3]+0.4,40,11.0,15.2,'hroof',bulge=1)
finial(_rx,_ry,15.2,1.8)
def facewin(cx,cy,r,n,z0,z1,m,rot,wf=0.55,arch=True):   # one arched window per face of an n-sided drum, 3 cm proud
    for i in range(n):
        t=rot+2*math.pi*(i+0.5)/n;rr_=r*math.cos(math.pi/n)+0.03;ex,ey=-math.sin(t),math.cos(t);hw_=r*math.sin(math.pi/n)*wf
        bx,by=cx+rr_*math.cos(t),cy+rr_*math.sin(t);zs=z1-hw_ if arch else z1
        P_=lambda s_,z_:v(bx+s_*ex,by+s_*ey,z_)
        quad(P_(-hw_,z0),P_(hw_,z0),P_(hw_,zs),P_(-hw_,zs),m)
        if arch:
            for k in range(6):
                a0_,a1_=math.pi*k/6,math.pi*(k+1)/6
                tri(P_(0,zs),P_(hw_*math.cos(a0_),zs+hw_*math.sin(a0_)),P_(hw_*math.cos(a1_),zs+hw_*math.sin(a1_)),m)
# Ladies' cupola (field photo): cream octagonal drum with arched windows, green dome and finial on the ridge
_cx,_cy=fr_xy(*CUP);prism(_cx,_cy,1.15,8,17.6,21.0,'ashlar',math.pi/8);facewin(_cx,_cy,1.15,8,19.0,20.6,'glassblk',math.pi/8)
cone(_cx,_cy,1.3,8,21.0,21.25,'trim',math.pi/8);cone(_cx,_cy,1.2,16,21.25,22.9,'hroof',bulge=1);finial(_cx,_cy,22.9,1.4)
# Members' clock tower (field photo): square green clock stage with a white clock face on each side, flared green
# pyramid cap, flagpole
_kx,_ky=fr_xy(*CLK);KW=1.75   # stage 3.5 m wide (field photo, 32 px at 145 m)
_O,_U,_W=_fr('M');_KR=math.atan2(_U[1],_U[0])+math.pi/4   # square sides parallel to the pavilion
prism(_kx,_ky,3.1*1.414,4,13.6,14.6,'hroof',_KR);bell(_kx,_ky,3.1*1.414,KW*1.414+0.1,14.6,16.45,'hroof',_KR,p=1.8)   # on the ridge   # flared base, 6.2 m foot (photo: foot 14.6 at the front)
prism(_kx,_ky,KW*1.414,4,16.45,18.85,'hroof',_KR)   # clock stage 16.45-18.85 m (back-projected at the tower's depth)
for i in range(4):
    nrm=[_U,_W,-_U,-_W][i];tg=np.array([-nrm[1],nrm[0]]);c_=np.array([_kx,_ky])+nrm*(KW+0.03);zc=17.5
    ring=[v(*(c_+tg*0.6*math.cos(t)),zc+0.6*math.sin(t)) for t in np.linspace(0,2*math.pi,17)[:-1]];cc=v(*c_,zc)
    for k in range(16):tri(cc,ring[k],ring[(k+1)%16],'btrim')
    for (ln_,ang_) in ((0.5,math.pi/2),(0.38,-0.5)):   # hands at ten to twelve
        c2=c_+nrm*0.02;e_=tg*math.cos(ang_);ez=math.sin(ang_)
        quad(v(*(c2-tg*0.03),zc),v(*(c2+tg*0.03),zc),v(*(c2+tg*0.03+e_*ln_),zc+ez*ln_),v(*(c2-tg*0.03+e_*ln_),zc+ez*ln_),'dark')
cone(_kx,_ky,KW*1.414+0.25,4,18.85,19.1,'trim',_KR)
_rings=[];_n=4;_r0=(KW+0.45)*1.414
for k in range(7):
    t=k/6;rk=0.7+(_r0-0.7)*(1-t)**1.7;zk=19.1+1.8*t   # flared cap to a small lantern (photo top 21.5)
    _rings.append([v(_kx+rk*math.cos(_KR+2*math.pi*i/_n),_ky+rk*math.sin(_KR+2*math.pi*i/_n),zk) for i in range(_n)])
for k in range(6):
    for i in range(_n):j=(i+1)%_n;quad(_rings[k][i],_rings[k][j],_rings[k+1][j],_rings[k+1][i],'hroof')
prism(_kx,_ky,0.5,4,20.9,21.25,'hroof',_KR);cone(_kx,_ky,0.6,4,21.25,21.5,'hroof',_KR)
prism(_kx,_ky,0.07,6,21.5,28.6,'steel')
# dark glass building behind the Messenger stand (roof edge 35.5 m measured from its base)
pass   # removed: not part of the stadium (director: stadium only, background pass later)
# --- scoreboard (east-north-east, behind the O'Reilly/Messenger gap): level board, face yaw solved from the photo.
# Screen photo x 437..503, orange panel x 503..517 (same height); corners checked against the photo to 2-5 px.
SB=[(87.3,57.0),(91.2,31.8)];zb0,zb1=8.2,25.1
fx_,fy_=math.cos(math.radians(189)),math.sin(math.radians(189))
_sA,_sB=np.array(SB[0]),np.array(SB[1])
def _sbp(t):return _sA+(_sB-_sA)*t
DECALS=dict(HDEC)
def sbpanel(t0,t1,z0,z1,m,depth=3.0):
    P0,P1=_sbp(t0),_sbp(t1)
    def q(X,z,off):return v(X[0]-fx_*off,X[1]-fy_*off,z)
    a1,a2,b2,b1=q(P0,z0,0),q(P1,z0,0),q(P1,z1,0),q(P0,z1,0)
    c1,c2,d2,d1=q(P0,z0,depth),q(P1,z0,depth),q(P1,z1,depth),q(P0,z1,depth)
    F.append(((a1,a2,b2,b1),m));quad(c2,c1,d1,d2,'facade2');quad(a2,c2,d2,b2,'facade2');quad(c1,a1,b1,d1,'facade2');quad(b1,b2,d2,d1,'facade2');quad(a1,c1,c2,a2,'facade2')
    d_=(P1-P0);W_=float(np.linalg.norm(d_));DECALS[m]={'o':[float(P0[0]),float(P0[1])],'d':[float(d_[0]/W_),float(d_[1]/W_)],'w':W_,'z0':z0,'z1':z1}
sbpanel(0.0,0.955,zb0,zb1,'sbface',0.8);sbpanel(0.955,1.165,zb0,zb1+0.5,'sbad',0.8)
sbpanel(0.02,0.62,4.0,zb0,'facade2',1.0)   # grey base wall under the board's left half (photo)
# --- the ground's own signs (director: ground's own lettering yes, no sponsor boards). Raised letters on the scoreboard
# roof, 'SYDNEY CRICKET GROUND' (refs3/101.jpg): about 90% of the board width, set just behind the face, facing the field.
_sc=_sbp(0.4775);SIGNS=[{'txt':'SYDNEY CRICKET GROUND','x':float(_sc[0]-fx_*0.4),'y':float(_sc[1]-fy_*0.4),'z':zb1,
  'nx':float(fx_),'ny':float(fy_),'w':0.9*0.955*float(np.linalg.norm(_sB-_sA)),'h':1.55,'d':0.25,'m':'steel'},
  # 'BREWONGLE STAND' on the roof fascia beside the Ladies (refs3/044.jpg): dark letters, 40 x 4 photo px -> 2.7 x 0.3 m,
  # 1.5 m under the roof edge; point ray-cast from a matched field view (rc.py, brew185 pixel 674,462)
  # front face of the roof fascia (ray-cast: x -84.65 at y -27.98, z 14.15-15.75, normal 0.996,0.094); letters 14.6-14.9 m, lower-middle of the band as in the photo
  {'txt':'BREWONGLE STAND','x':-84.65+0.996*0.06,'y':-27.98+0.094*0.06,'z':14.45,'nx':0.996,'ny':0.094,'w':2.7,'h':0.3,'d':0.04,'m':'dark'}]   # letter height: ~55 of ~600 photo px on the 17 m board face
json.dump(SIGNS,open('signs.json','w'))
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
# Messenger roof end at 39.5 deg (roof only, the stand body starts at 42): close the roof section end-on
_a=STANDS['messenger'];_d=_a[0];_lo,_hi,_zf,_zo=_a[2](_d),_a[4](_d),_a[3](_d),_a[5](_d);_an=math.radians(_d)
_rp=[(_lo,_zf-1.6)]+[(_lo+(_hi-_lo)*t,_zf+(_zo-_zf)*t) for t in np.linspace(0,1,7)]+[(_hi,_zo-1.2)];_rv=[P(r_,_an,z_) for r_,z_ in _rp]
for i,j,l in earclip(_rp):tri(_rv[i],_rv[j],_rv[l],'fascia')
# concourse columns under the Trumper and O'Reilly backs (Gate 9 photo), about every 9 m along the front line
for k_,a0_,a1_,share in (('trumper',-99.5,-34.5,0.22),('oreilly',-34,18,None)):
    for d_ in np.arange(a0_+1.5,a1_-1.0,0.5):
        o=OUT.get(round(d_*2)/2%360)
        if not o or o[4]!=k_:continue
        lo,hi,zf,zo,_k=o;rc=hi-0.6
        if int(round(d_*2))%int(round(2*math.degrees(9.0/rc)))!=0:continue
        a_=math.radians(d_);prism(PC[0]+rc*math.cos(a_),PC[1]+rc*math.sin(a_),0.45,12,0,(share*(zo-1.2) if share else ZC_J)-0.6,'conc')
