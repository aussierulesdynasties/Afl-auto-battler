# Bowden McAdam Grandstand as it stands since the 2020 rebuild. Stand frame: s along the front (south->north),
# t back (west), z up. Sources: aerial ref.jpg (roof outline, cam.json), w04 (front, matched camera cam_w04b.json),
# c02/c06/c09 (south end, back), satellite + OSM (footprint).
import numpy as np,json,math
# Plan from the satellite (Google, after the rebuild): roof front edge x -68.6 running due north (-0.7 deg),
# roof south edge y -7.5; the length (29.9 m) and every s/t/z measure stay the photo values.
O=np.array([-68.6,-7.5]);A=np.array([-68.96,22.44])-O;L=float(np.linalg.norm(A));a=A/L
b=np.array([-a[1],a[0]]);b=-b if b[0]>0 else b   # back = west
def W(s,t,z):p=O+s*a+t*b;return [float(p[0]),float(p[1]),float(z)]
G=[]
def mesh(name,mat,V,F,uv=None):G.append(dict(name=name,mat=mat,V=V,F=F,**({'UV':uv} if uv else {})))
def quad(name,mat,P4):mesh(name,mat,P4,[[0,1,2,3]])
def box(name,mat,s0,s1,t0,t1,z0,z1,skip=()):
    V=[W(s0,t0,z0),W(s1,t0,z0),W(s1,t1,z0),W(s0,t1,z0),W(s0,t0,z1),W(s1,t0,z1),W(s1,t1,z1),W(s0,t1,z1)]
    F={'bottom':[0,3,2,1],'top':[4,5,6,7],'front':[0,1,5,4],'right':[1,2,6,5],'back':[2,3,7,6],'left':[3,0,4,7]}
    for k,f in F.items():
        if k not in skip:mesh(name+'_'+k,mat if isinstance(mat,str) else mat.get(k,mat['*']),V,[f])
def tube(name,mat,P0,P1,r0,r1,n=8):
    P0=np.array(P0,float);P1=np.array(P1,float);d=P1-P0;d/=np.linalg.norm(d)
    u=np.cross(d,[0,0,1.]) if abs(d[2])<0.9 else np.cross(d,[1.,0,0]);u/=np.linalg.norm(u);v=np.cross(d,u)
    V=[];F=[]
    for i in range(n):
        an=2*math.pi*i/n;e=u*math.cos(an)+v*math.sin(an);V+=[list(P0+r0*e),list(P1+r1*e)]
    for i in range(n):j=(i+1)%n;F.append([2*i,2*j,2*j+1,2*i+1])
    mesh(name,mat,[[float(x) for x in p] for p in V],F)
def sbar(name,mat,s0,t0,z0,s1,t1,z1,r=0.04,n=6):tube(name,mat,W(s0,t0,z0),W(s1,t1,z1),r,r,n)
# ---------------- measurements (metres) ----------------
B=L/7   # bay: 7 equal bays; masts and fin brackets sit on the joints (w04 brackets, c09 masts, columns 4.3 m apart)
P=dict(zF=11.45,zC=10.9,tC=11.4,tB=24.4,zBack=6.8,fasc=0.35,step=0.22,
       cn_t0=10.4,cn_z0=10.3,scal=0.55,
       box_s0=7.9,box_s1=25.55,box_t0=4.0,box_t1=10.8,box_z0=7.3,box_z1=10.75,
       bn_z=9.75,gl_z=7.95,                       # banner bottom, glass bottom (w04 back-projected)
       sb_s0=6.4,sb_t0=6.0,sb_z1=10.0,            # set-back window block south of the box
       pl_s0=5.5,pl_s1=28.5,pl_t=0.6,pl_z=2.0,rows=7,row_d=0.7,row_h=0.385,walk=1.0,
       col_s=[7.3,11.42,15.71,20.05,24.7],col_t=4.0,
       wall_t=21.8,wall_z=4.35,mast_t=18.0,mast_z=16.5,mast_s=[2.3,7.6,13.0,18.4,23.4],strut_s=[2.3,7.6,13.0,18.4,23.4,28.7],portal_s=-1.6,portal_z=12.3)
def roof_z(s,t):
    # bays 1-3 form one flat panel; bays 4-7 are shingled: each falls `step` from its south to its north joint
    k=min(6,int(s/B));f=0.0 if k<3 else (s-k*B)/B-0.5
    droop=2.6*max(0.0,(11.0-s)/11.0)**1.6     # south panel curves down to the south end (w04 edge, t 0: z 9.19 at s 0.9)
    return P['zF']-P['step']*f-droop+(P['zC']-P['zF'])*t/P['tC']
def build():
    G.clear()
    # main roof: panel by panel so the shingle steps show at the joints
    panels=[(0,3*B)]+[(k*B,(k+1)*B) for k in range(3,7)];T=np.linspace(0,P['tC'],4)
    for i,(s0,s1) in enumerate(panels):
        S=np.linspace(s0+1e-3,s1-1e-3,16 if i==0 else 2);V=[];F=[];ns=len(S)
        for t in T:
            for s in S:V.append(W(s,t,roof_z(s,t)))
        for j in range(len(T)-1):
            for k in range(ns-1):F.append([j*ns+k,j*ns+k+1,(j+1)*ns+k+1,(j+1)*ns+k])
        mesh('roof_top%d'%i,'roof_top',V,F)
        mesh('roof_soffit%d'%i,'roof_soffit',[[x,y,z-P['fasc']] for x,y,z in V],[f[::-1] for f in F])
        Vf=[];Ff=[]
        for k,s in enumerate(S):Vf+=[W(s,0,roof_z(s,0)-P['fasc']),W(s,0,roof_z(s,0))]
        for k in range(ns-1):Ff.append([2*k,2*k+2,2*k+3,2*k+1])
        mesh('roof_fascia%d'%i,'fascia',Vf,Ff)
        for s,end in((S[0],0),(S[-1],1)):
            Ve=[];Fe=[]
            for t in T:Ve+=[W(s,t,roof_z(s,t)-P['fasc']),W(s,t,roof_z(s,t))]
            for j in range(len(T)-1):Fe.append([2*j,2*j+1,2*j+3,2*j+2] if end==0 else [2*j,2*j+2,2*j+3,2*j+1])
            mesh('roof_end%d_%d'%(i,end),'fascia',Ve,Fe)
    # fin brackets at the joints 3..7: white X frames proud of the fascia (c06, w04)
    for k in range(3,8):
        s=k*B-1e-3;z=roof_z(s,0)
        for (t0,z0,t1,z1) in ((-0.9,z-0.55,0.1,z+0.05),(-0.9,z+0.05,0.1,z-0.55),(-0.9,z-0.55,-0.9,z+0.05),(-0.9,z+0.05,0.1,z+0.05)):
            sbar('fin%d_%g'%(k,t0+z0),'steel_white',s,t0,z0,s,t1,z1,0.05)
    # tapered rafters under the roof at each shingle joint (w04: cream beams running back from every bracket)
    for k in range(3,8):
        sk=min(k*B,L)-0.12;V=[];F=[]
        for t_,dep in ((0.3,0.55),(P['tC']-0.2,0.3)):
            zt=roof_z(min(sk,L-0.01),t_)-P['fasc']
            for ds in(-0.12,0.12):V+=[W(sk+ds,t_,zt),W(sk+ds,t_,zt-dep)]
        F=[[0,1,5,4],[2,6,7,3],[1,3,7,5],[0,2,3,1]]
        mesh('rafter%d'%k,'cream',V,F)
    # back canopy: scalloped edge, low between masts, high at each mast (c09)
    # c09/c06: the back canopy starts over the south wing's upper volume (s 3.0)
    ns2=53;S2=np.linspace(3.0,L,ns2);nt2=6;T2=np.linspace(P['cn_t0'],P['tB'],nt2);V=[];F=[]
    for t in T2:
        u=(t-P['cn_t0'])/(P['tB']-P['cn_t0'])
        for s in S2:
            sc=-P['scal']*abs(math.sin(math.pi*(s-2.3)/5.3))*u*u
            V.append(W(s,t,P['cn_z0']+(P['zBack']-P['cn_z0'])*u+sc))
    for j in range(nt2-1):
        for i in range(ns2-1):F.append([j*ns2+i,j*ns2+i+1,(j+1)*ns2+i+1,(j+1)*ns2+i])
    mesh('canopy_top','canopy',V,F);mesh('canopy_under','canopy_under',[[x,y,z-0.15] for x,y,z in V],[f[::-1] for f in F])
    Ve=[];Fe=[]
    for i,s in enumerate(S2):
        u=1;sc=-P['scal']*abs(math.sin(math.pi*(s-2.3)/5.3));z=P['zBack']+sc;Ve+=[W(s,P['tB'],z-0.3),W(s,P['tB'],z)]
    for i in range(ns2-1):Fe.append([2*i+2,2*i,2*i+1,2*i+3])
    mesh('canopy_edge','fascia',Ve,Fe)
    # masts (6, on the joints) and back struts from the wall head to the canopy edge (c09)
    for k,s in enumerate(P['mast_s']):
        sbar('mast%d'%k,'steel_white',s,P['mast_t'],6.0,s,P['mast_t'],P['mast_z']-0.9,0.24,10)
        tube('mast%d_tip'%k,'steel_white',W(s,P['mast_t'],P['mast_z']-0.9),W(s,P['mast_t']+0.45,P['mast_z']),0.24,0.12,10)
    for k,s in enumerate(P['strut_s']):
        sbar('strut%d'%k,'steel_white',s,P['wall_t'],P['wall_z']+0.3,s,P['tB']-0.3,P['zBack']-0.1,0.16,8)
    # corporate box: banner over glass over cream band; returns and soffit
    s0,s1,t0,t1,z0,z1=P['box_s0'],P['box_s1'],P['box_t0'],P['box_t1'],P['box_z0'],P['box_z1']
    quad('box_banner','banner',[W(s0,t0,P['bn_z']),W(s1,t0,P['bn_z']),W(s1,t0,z1),W(s0,t0,z1)])
    quad('box_glass','glass',[W(s0,t0,P['gl_z']),W(s1,t0,P['gl_z']),W(s1,t0,P['bn_z']),W(s0,t0,P['bn_z'])])
    quad('box_band','cream_band',[W(s0,t0,z0),W(s1,t0,z0),W(s1,t0,P['gl_z']),W(s0,t0,P['gl_z'])])
    quad('box_endN','cream',[W(s1,t0,z0),W(s1,t1,z0),W(s1,t1,z1),W(s1,t0,z1)])
    quad('box_under','soffit_box',[W(s0,t1,z0),W(s1,t1,z0),W(s1,t0,z0),W(s0,t0,z0)])
    # ---- south wing (s -1..7.9), measured on w04 (cam_w04s), c06, c08, c09 ----
    # upper volume: z 6.05 up to the roof soffit, chamfered 45 deg from (s7.9,t4.0) to (s3.0,t8.9), one window on the chamfer
    def sof(ss,tt):return roof_z(ss,tt)-P['fasc']
    UV=[(7.9,4.0),(3.0,8.9),(3.0,10.8),(7.9,10.8)]
    for (sa,ta),(sb_,tb),nm in ((UV[0],UV[1],'chamfer'),(UV[1],UV[2],'south')):
        quad('uv_'+nm,'cream',[W(sa,ta,6.05),W(sb_,tb,6.05),W(sb_,tb,sof(sb_,tb)),W(sa,ta,sof(sa,ta))])
    quad('uv_win','glass_sb',[W(7.75,4.14,8.12),W(6.3,5.59,8.12),W(6.3,5.59,9.62),W(7.75,4.14,9.62)])
    # box underside continues over the chamfer gap between z 6.05 and the box (s 7.9 face)
    quad('uv_north','cream',[W(7.9,4.0,6.05),W(7.9,4.0,z0),W(7.9,10.8,z0),W(7.9,10.8,6.05)])
    # level 2 deck (z 6.05) behind a solid cream parapet (6.05-7.3) on the front line; cream band 5.45-6.05 under it
    quad('l2_deck','deck',[W(-1.0,0.6,6.05),W(7.9,0.6,6.05),W(7.9,10.8,6.05),W(-1.0,10.8,6.05)])
    box('l2_parapet','cream',-1.0,7.9,0.6,0.8,6.05,7.3,skip=('bottom',))
    quad('l2_band','cream',[W(-1.0,0.6,5.45),W(7.9,0.6,5.45),W(7.9,0.6,6.05),W(-1.0,0.6,6.05)])
    quad('l1_ceiling','cream',[W(-1.0,0.6,5.45),W(-1.0,11.0,5.45),W(7.9,11.0,5.45),W(7.9,0.6,5.45)])
    # level 1 (floor z 3.1): open front, bar balustrade 3.1-4.2, white posts at s 1.25 and 4.5, dark back wall at t 11;
    # cream slab band 2.7-3.1 over light grey render 0-2.7
    quad('l1_floor','deck',[W(-1.0,0.6,3.1),W(7.9,0.6,3.1),W(7.9,11.0,3.1),W(-1.0,11.0,3.1)])
    quad('l1_back','rear_dark',[W(7.9,11.0,3.1),W(-1.0,11.0,3.1),W(-1.0,11.0,5.45),W(7.9,11.0,5.45)])
    quad('wing_render','render_grey',[W(-1.0,0.6,0),W(6.6,0.6,0),W(6.6,0.6,2.7),W(-1.0,0.6,2.7)])
    quad('wing_band','cream',[W(-1.0,0.6,2.7),W(6.6,0.6,2.7),W(6.6,0.6,3.1),W(-1.0,0.6,3.1)])
    quad('wing_bal','rail_bars',[W(-1.0,0.65,3.1),W(6.6,0.65,3.1),W(6.6,0.65,4.2),W(-1.0,0.65,4.2)])
    sbar('wing_bal_top','steel_white',-1.0,0.65,4.2,6.6,0.65,4.2,0.03,4)
    for ss in (1.25,4.5):sbar('wing_post%g'%ss,'steel_white',ss,0.75,3.1,ss,0.75,5.45,0.12,8)
    # south face (s -1): light grey render from the ground to level 2, one door near the back (c09)
    quad('wing_south','render_grey',[W(-1.0,21.8,0),W(-1.0,0.6,0),W(-1.0,0.6,6.05),W(-1.0,21.8,6.05)])
    quad('wing_south_door','door_panel',[W(-1.01,18.6,0),W(-1.01,17.5,0),W(-1.01,17.5,2.2),W(-1.01,18.6,2.2)])
    # c09: black louvres on the south face west of the door, and (w04: dark interior) the middle level's north side closed
    quad('wing_louvre','louvre_black',[W(-1.01,21.6,0.2),W(-1.01,18.9,0.2),W(-1.01,18.9,3.8),W(-1.01,21.6,3.8)])
    quad('l1_side','rear_dark',[W(7.9,0.8,3.1),W(7.9,11.0,3.1),W(7.9,11.0,5.45),W(7.9,0.8,5.45)])
    quad('wing_roof','deck',[W(-1.0,10.8,6.05),W(8.0,10.8,6.05),W(8.0,21.8,6.05),W(-1.0,21.8,6.05)])
    # front south stair: lane t 0.6-1.6 rising from the walkway (s 11.3, z 2.0) to level 1 (s 6.6, z 3.1);
    # grey render upstand on the front line (top 3.25 at s 6.6 falling to 2.2 at s 10.9); bar rail 1 m over the treads
    n=8
    for i in range(n):
        sA=11.3-(11.3-6.6)*i/n;sB=11.3-(11.3-6.6)*(i+1)/n;zz=2.0+(3.1-2.0)*(i+1)/n
        # the stair passes over the arch (w04: arch s 9.0-10.9 open to its 1.75 m crown), so steps there start at the crown
        for (a_,b_,z_) in ((sB,min(sA,9.0),0),(max(sB,9.0),min(sA,10.9),1.75),(max(sB,10.9),sA,0)):
            if b_-a_>1e-6:box('fst_step%d_%g'%(i,a_),'render_grey',a_,b_,0.6,1.6,z_,zz,skip=('bottom','back'))
    # the front face is front_wall below (it carries the arch cut); no second face on the front line
    # arch head: the rounded corner and flat ceiling, t 0.6 to the back wall at 2.4
    ar_=1.3;arc_=[(9.0+ar_-ar_*math.cos(q),1.75-ar_+ar_*math.sin(q)) for q in np.linspace(0,math.pi/2,9)]+[(10.9,1.75)]
    for k_ in range(len(arc_)-1):
        (s1_,z1_),(s2_,z2_)=arc_[k_],arc_[k_+1]
        quad('arch_head%d'%k_,'render_grey',[W(s1_,0.6,z1_),W(s2_,0.6,z2_),W(s2_,2.4,z2_),W(s1_,2.4,z1_)])
    quad('fst_bars','rail_bars',[W(11.3,1.55,2.0),W(6.6,1.55,3.1),W(6.6,1.55,4.1),W(11.3,1.55,3.0)])
    sbar('fst_rail','steel_grey',11.3,1.55,3.0,6.6,1.55,4.1,0.03,4)
    # columns under the box front (w04: one per bay); the south one stands on level 1 and stops at its ceiling
    for i,s in enumerate(P['col_s']):sbar('col%d'%i,'steel_white',s,P['col_t'],3.1 if i==0 else P['pl_z'],s,P['col_t'],5.45 if i==0 else z0,0.17,10)
    # plinth, front walkway, seat tiers (7 rows), concourse under the box
    pt,pz,ps0,ps1=P['pl_t'],P['pl_z'],P['pl_s0'],P['pl_s1']
    # under the seat deck (w04): the slab runs to the front line (fascia 1.8-2.2, s 10.9-28.5) over a recessed charcoal
    # wall at t 2.4 with one lighter door panel; white wall benches in front of it (back-projected on w04)
    quad('deck_fascia','cream',[W(10.9,pt,1.8),W(ps1,pt,1.8),W(ps1,pt,pz+0.2),W(10.9,pt,pz+0.2)])
    quad('deck_soffit','soffit_box',[W(10.9,2.4,1.8),W(ps1,2.4,1.8),W(ps1,pt,1.8),W(10.9,pt,1.8)])
    quad('under_wall','under_wall',[W(10.9,2.4,0),W(ps1,2.4,0),W(ps1,2.4,1.8),W(10.9,2.4,1.8)])
    quad('under_door','door_panel',[W(13.0,2.39,0),W(14.3,2.39,0),W(14.3,2.39,1.75),W(13.0,2.39,1.75)])
    for (sa,sb_) in ((11.6,13.8),(14.9,18.1),(22.5,25.5),(26.5,28.4)):
        box('bench%g'%sa,'bench_white',sa,sb_,1.95,2.35,0.40,0.46)
        for ss in (sa+0.15,sb_-0.15):box('bench_leg%g'%ss,'bench_white',ss-0.03,ss+0.03,2.05,2.3,0,0.40,skip=('bottom','top'))
    # front wall south of the deck (light grey render, s 6.6-10.9) with the arch s 9.0-10.9, z 0-1.75, top-south corner r 1.3
    ar=1.3
    arc=[(9.0+ar-ar*math.cos(q),1.75-ar+ar*math.sin(q)) for q in np.linspace(0,math.pi/2,9)]
    left=[(6.6,0),(9.0,0)]+arc+[(10.9,1.75),(10.9,2.2),(6.6,3.25)]
    # fan from (6.6,0): arc points are visible from that corner, so the outline is star-shaped about it
    V=[W(ss,pt,zz) for ss,zz in left];F=[[0,i,i+1] for i in range(1,len(left)-1)]
    mesh('front_wall','render_grey',V,F)
    quad('arch_back','rear_dark',[W(10.9,2.4,0),W(9.0,2.4,0),W(9.0,2.4,1.75),W(10.9,2.4,1.75)])
    quad('arch_side','render_grey',[W(9.0,2.4,0),W(9.0,pt,0),W(9.0,pt,1.75-ar),W(9.0,2.4,1.75-ar)])
    t=pt;z=pz;quad('walkway','deck',[W(11.3,t,z),W(ps1,t,z),W(ps1,t+P['walk'],z),W(11.3,t+P['walk'],z)]);t+=P['walk']
    rows=[]
    for r in range(P['rows']):
        z1_=z+P['row_h'];quad('riser%d'%r,'riser',[W(ps0+2.5,t,z),W(ps1-1.0,t,z),W(ps1-1.0,t,z1_),W(ps0+2.5,t,z1_)])
        quad('tread%d'%r,'deck',[W(ps0+2.5,t,z1_),W(ps1-1.0,t,z1_),W(ps1-1.0,t+P['row_d'],z1_),W(ps0+2.5,t+P['row_d'],z1_)])
        rows.append((t,z1_));t+=P['row_d'];z=z1_
    P['conc_t']=t;P['conc_z']=z
    quad('concourse','deck',[W(8.0,t,z),W(ps1,t,z),W(ps1,P['wall_t'],z),W(8.0,P['wall_t'],z)])
    quad('rear_wall','rear_dark',[W(8.0,t+2.5,z),W(ps1,t+2.5,z),W(ps1,t+2.5,z0),W(8.0,t+2.5,z0)][::-1])
    # cheek wall closing the seat rows at their south end (s 8.0), walkway level up to the concourse
    quad('cheek_S','render_grey',[W(8.0,pt+P['walk'],pz),W(8.0,t,pz),W(8.0,t,z+0.05),W(8.0,pt+P['walk'],z+0.05)][::-1])
    # seats: one shell per seat, 0.5 m pitch (w04 counts)
    import random;_rng=random.Random(404)   # fixed seed: same seat pattern every build
    for r,(t,zz) in enumerate(rows):
        n=int((ps1-1.0-(ps0+2.5))/0.5)
        for i in range(n):
            s=ps0+2.5+0.25+i*0.5;mat='seat_white' if _rng.random()<(0.92,0.92,0.88,0.6,0.12,0.08,0.06)[min(r,6)] else 'seat_navy'   # w04 zoom: white front rows with odd navy seats, a mixed 4th row, navy behind with odd white seats
            box('seat%d_%d'%(r,i),mat,s-0.21,s+0.21,t+0.15,t+0.55,zz+0.35,zz+0.42,skip=('bottom',))
            quad('seatback%d_%d'%(r,i),mat,[W(s-0.21,t+0.56,zz+0.40),W(s+0.21,t+0.56,zz+0.40),W(s+0.21,t+0.62,zz+0.85),W(s-0.21,t+0.62,zz+0.85)])
    # front balustrade and the two stairs (south up to the concourse, north down to the walkway)
    quad('bal_bars','rail_bars',[W(10.9,pt+0.1,pz+0.2),W(ps1,pt+0.1,pz+0.2),W(ps1,pt+0.1,pz+1.2),W(10.9,pt+0.1,pz+1.2)])
    sbar('bal_rail','steel_grey',10.9,pt+0.1,pz+1.2,ps1,pt+0.1,pz+1.2,0.03,4)
    sbar('stairN_rail','steel_grey',ps1-1.0,1.6,pz+1.0,ps1-4.5,5.5,P['conc_z']+1.0,0.03,4)
    # back wall: stone block (north) and dark cladding (south) to the wall head (c09)
    quad('back_stone','stone',[W(ps1,P['wall_t'],0),W(8.5,P['wall_t'],0),W(8.5,P['wall_t'],P['wall_z']),W(ps1,P['wall_t'],P['wall_z'])])
    quad('back_clad','cladding',[W(8.5,P['wall_t'],0),W(-1.0,P['wall_t'],0),W(-1.0,P['wall_t'],P['wall_z']),W(8.5,P['wall_t'],P['wall_z'])])
    # north end (w04): no solid face in front of the seats; the dark under-deck wall below the deck, and a grey cheek
    # under the seat rake (as cheek_S at the south end), so the seat ends and the north stair show
    quad('north_under','under_wall',[W(ps1,2.4,pz),W(ps1,P['wall_t'],pz),W(ps1,P['wall_t'],0),W(ps1,2.4,0)])
    mesh('cheek_N','render_grey',[W(ps1,P['conc_t'],P['conc_z']),W(ps1,P['wall_t'],P['conc_z']),W(ps1,P['wall_t'],pz),W(ps1,pt+P['walk'],pz)],[[0,1,2,3]])
    # ---- stair tower south of the wing (c02, c06, c09): white steel, two landings, two flights, canopy blade, portal ----
    box('st_L1','steel_white',-4.5,-1.0,3.0,18.0,2.9,3.1)
    box('st_L2','steel_white',-4.5,-1.0,3.0,12.0,5.85,6.05)
    # c09: the blade is a cantilever off the stand's south face (no posts under it)
    box('st_blade','steel_white',-5.0,-1.0,2.5,12.0,9.0,9.6)
    # c09: the portal posts are fat round columns (about 0.7 m across, read against the 1.1 m landing rail)
    for tt in (9.2,11.7):sbar('portal%g'%tt,'steel_white',-4.5,tt,0,-4.5,tt,P['portal_z'],0.35,12)
    sbar('portal_head','steel_white',-4.5,9.0,P['portal_z'],-4.5,11.9,P['portal_z'],0.22,8)
    for (ta,za,tb,zb,nm) in ((12.0,6.05,16.5,3.1,'up'),(18.0,3.1,22.6,0.0,'lo')):
        n=int(round((za-zb)/0.18))
        for i in range(n):
            tA=ta+(tb-ta)*i/n;tB=ta+(tb-ta)*(i+1)/n;zz=za-(za-zb)*(i+1)/n
            box('st_%s%d'%(nm,i),'steel_white',-4.5,-3.1,min(tA,tB),max(tA,tB),zz+0.13,zz+0.18,skip=('bottom',))
        for ss in (-4.5,-3.1):
            quad('st_%s_bars%g'%(nm,ss),'rail_bars',[W(ss,ta,za),W(ss,tb,zb),W(ss,tb,zb+1.0),W(ss,ta,za+1.0)])
            sbar('st_%s_rail%g'%(nm,ss),'steel_white',ss,ta,za+1.0,ss,tb,zb+1.0,0.03,4)
            sbar('st_%s_string%g'%(nm,ss),'steel_white',ss,ta,za,ss,tb,zb,0.08,6)
    for (zl,t1_) in ((3.1,18.0),(6.05,12.0)):
        quad('st_bars_s%g'%zl,'rail_bars',[W(-4.5,3.0,zl),W(-4.5,t1_,zl),W(-4.5,t1_,zl+1.1),W(-4.5,3.0,zl+1.1)])
        quad('st_bars_f%g'%zl,'rail_bars',[W(-4.5,3.0,zl),W(-1.0,3.0,zl),W(-1.0,3.0,zl+1.1),W(-4.5,3.0,zl+1.1)])
        sbar('st_top_s%g'%zl,'steel_white',-4.5,3.0,zl+1.1,-4.5,t1_,zl+1.1,0.03,4)
        sbar('st_top_f%g'%zl,'steel_white',-4.5,3.0,zl+1.1,-1.0,3.0,zl+1.1,0.03,4)
    # c09: no tall posts at the front corners; only the lower landing stands on posts
    for (ss_,tt_,zt) in ((-4.5,18.0,3.1),(-1.0,18.0,3.1)):
        sbar('st_post%g_%g'%(ss_,tt_),'steel_white',ss_,tt_,0,ss_,tt_,zt,0.1,6)
    return G
if __name__=='__main__':
    build();json.dump(dict(G=G,P=P,O=O.tolist(),a=a.tolist(),b=b.tolist(),L=L),open('stand.json','w'));print(len(G),'meshes L=%.2f B=%.2f'%(L,B))
