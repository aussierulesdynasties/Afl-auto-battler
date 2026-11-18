# Bowden McAdam Grandstand as it stands since the 2020 rebuild. Stand frame: s along the front (south->north),
# t back (west), z up. Sources: aerial ref.jpg (roof outline, cam.json), w04 (front, matched camera cam_w04b.json),
# c02/c06/c09 (south end, back), satellite + OSM (footprint).
import numpy as np,json,math
O=np.array([-72.4,-15.0]);A=np.array([-74.0,14.9])-O;L=float(np.linalg.norm(A));a=A/L
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
    ns2=57;S2=np.linspace(0,L,ns2);nt2=6;T2=np.linspace(P['cn_t0'],P['tB'],nt2);V=[];F=[]
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
    # set-back block south of the box (w04 x 230-310): cream with one window
    box('setback','cream',P['sb_s0'],s0,P['sb_t0'],t1,z0,P['sb_z1'],skip=('right',))
    quad('setback_win','glass_sb',[W(P['sb_s0']+0.2,P['sb_t0']-0.01,8.15),W(s0-0.1,P['sb_t0']-0.01,8.15),W(s0-0.1,P['sb_t0']-0.01,9.87),W(P['sb_s0']+0.2,P['sb_t0']-0.01,9.87)])
    # upper deck south of the set-back block, where the stair tower lands (c06, c09)
    quad('upper_deck','deck',[W(-4.0,2.0,z0),W(P['sb_s0'],2.0,z0),W(P['sb_s0'],t1,z0),W(-4.0,t1,z0)])
    quad('upper_deck_edge','cream',[W(-4.0,2.0,z0-0.4),W(P['sb_s0'],2.0,z0-0.4),W(P['sb_s0'],2.0,z0),W(-4.0,2.0,z0)])
    for s in np.arange(-4.0,P['sb_s0']+0.01,1.6):sbar('ud_post%.1f'%s,'steel_white',s,2.0,z0,s,2.0,z0+1.1,0.025,4)
    sbar('ud_rail','steel_white',-4.0,2.0,z0+1.1,P['sb_s0'],2.0,z0+1.1,0.03,4)
    # columns under the box front (w04: one per bay)
    for i,s in enumerate(P['col_s']):sbar('col%d'%i,'steel_white',s,P['col_t'],P['pl_z'],s,P['col_t'],z0,0.17,10)
    # plinth, front walkway, seat tiers (7 rows), concourse under the box
    pt,pz,ps0,ps1=P['pl_t'],P['pl_z'],P['pl_s0'],P['pl_s1']
    quad('plinth_front','plinth',[W(ps0,pt,0),W(ps1,pt,0),W(ps1,pt,pz),W(ps0,pt,pz)])
    t=pt;z=pz;quad('walkway','deck',[W(ps0,t,z),W(ps1,t,z),W(ps1,t+P['walk'],z),W(ps0,t+P['walk'],z)]);t+=P['walk']
    rows=[]
    for r in range(P['rows']):
        z1_=z+P['row_h'];quad('riser%d'%r,'riser',[W(ps0+2.5,t,z),W(ps1-1.0,t,z),W(ps1-1.0,t,z1_),W(ps0+2.5,t,z1_)])
        quad('tread%d'%r,'deck',[W(ps0+2.5,t,z1_),W(ps1-1.0,t,z1_),W(ps1-1.0,t+P['row_d'],z1_),W(ps0+2.5,t+P['row_d'],z1_)])
        rows.append((t,z1_));t+=P['row_d'];z=z1_
    P['conc_t']=t;P['conc_z']=z
    quad('concourse','deck',[W(ps0,t,z),W(ps1,t,z),W(ps1,P['wall_t'],z),W(ps0,P['wall_t'],z)])
    quad('rear_wall','rear_dark',[W(ps0,t+2.5,z),W(ps1,t+2.5,z),W(ps1,t+2.5,z0),W(ps0,t+2.5,z0)][::-1])
    # seats: one shell per seat, 0.5 m pitch (w04 counts)
    for r,(t,zz) in enumerate(rows):
        n=int((ps1-1.0-(ps0+2.5))/0.5)
        for i in range(n):
            s=ps0+2.5+0.25+i*0.5;mat='seat_white' if r<3 else 'seat_navy'   # w04 (2025 stand): three light-grey front rows, navy behind
            box('seat%d_%d'%(r,i),mat,s-0.21,s+0.21,t+0.15,t+0.55,zz+0.35,zz+0.42,skip=('bottom',))
            quad('seatback%d_%d'%(r,i),mat,[W(s-0.21,t+0.56,zz+0.40),W(s+0.21,t+0.56,zz+0.40),W(s+0.21,t+0.62,zz+0.85),W(s-0.21,t+0.62,zz+0.85)])
    # front balustrade and the two stairs (south up to the concourse, north down to the walkway)
    for s in np.arange(ps0+2.5,ps1-0.9,1.5):sbar('bal%.1f'%s,'steel_grey',s,pt+0.1,pz,s,pt+0.1,pz+1.0,0.025,4)
    sbar('bal_rail','steel_grey',ps0+2.5,pt+0.1,pz+1.0,ps1-1.0,pt+0.1,pz+1.0,0.03,4)
    sbar('stairS_rail','steel_grey',ps0+2.5,1.6,pz+1.0,ps0,4.0,P['conc_z']+1.0,0.03,4)
    sbar('stairN_rail','steel_grey',ps1-1.0,1.6,pz+1.0,ps1-4.5,5.5,P['conc_z']+1.0,0.03,4)
    # back wall: stone block (north) and dark cladding (south) to the wall head (c09)
    quad('back_stone','stone',[W(ps1,P['wall_t'],0),W(8.5,P['wall_t'],0),W(8.5,P['wall_t'],P['wall_z']),W(ps1,P['wall_t'],P['wall_z'])])
    quad('back_clad','cladding',[W(8.5,P['wall_t'],0),W(-1.0,P['wall_t'],0),W(-1.0,P['wall_t'],P['wall_z']),W(8.5,P['wall_t'],P['wall_z'])])
    quad('north_end','stone',[W(ps1,pt,0),W(ps1,P['wall_t'],0),W(ps1,P['wall_t'],P['wall_z']),W(ps1,pt,P['wall_z'])][::-1])
    # south block: cream wall up to the upper deck
    quad('south_front','cream',[W(-1.0,pt,0),W(ps0,pt,0),W(ps0,pt,z0-0.4),W(-1.0,pt,z0-0.4)])
    quad('south_end','cream',[W(-1.0,P['wall_t'],0),W(-1.0,pt,0),W(-1.0,pt,z0-0.4),W(-1.0,P['wall_t'],z0-0.4)])
    # portal frame at the south end (c02, c09): two posts and a head beam
    ps=P['portal_s']
    for tt in (8.4,10.0):sbar('portal%g'%tt,'steel_white',ps,tt,0,ps,tt,P['portal_z'],0.2,8)
    sbar('portal_head','steel_white',ps,8.2,P['portal_z'],ps,10.2,P['portal_z'],0.22,8)
    # external stair tower south of the block (c06, c09): two flights and a landing
    lz=z0/2
    quad('st_landing','steel_white',[W(-4.0,9.0,lz),W(-1.0,9.0,lz),W(-1.0,12.0,lz),W(-4.0,12.0,lz)])
    for (sa,ta,za,sb,tb,zb) in ((-1.0,13.5,0,-4.0,12.0,lz),(-4.0,9.0,lz,-1.0,4.0,z0)):
        n=12
        for i in range(n):
            f0=i/n;f1=(i+1)/n
            sA=sa+(sb-sa)*f0;tA=ta+(tb-ta)*f0;zA=za+(zb-za)*f1
            quad('st_step%g_%d'%(za,i),'steel_white',[W(sA-0.6,tA,zA),W(sA+0.6,tA,zA),W(sA+0.6,tA+(tb-ta)/n,zA),W(sA-0.6,tA+(tb-ta)/n,zA)])
        sbar('st_railA%g'%za,'steel_white',sa-0.6,ta,za+1.0,sb-0.6,tb,zb+1.0,0.03,4)
        sbar('st_railB%g'%za,'steel_white',sa+0.6,ta,za+1.0,sb+0.6,tb,zb+1.0,0.03,4)
    for (ss_,tt_) in ((-4.0,9.0),(-1.0,9.0),(-4.0,12.0),(-1.0,12.0)):sbar('st_post%g_%g'%(ss_,tt_),'steel_white',ss_,tt_,0,ss_,tt_,z0+1.1,0.08,6)
    return G
if __name__=='__main__':
    build();json.dump(dict(G=G,P=P,O=O.tolist(),a=a.tolist(),b=b.tolist(),L=L),open('stand.json','w'));print(len(G),'meshes L=%.2f B=%.2f'%(L,B))
