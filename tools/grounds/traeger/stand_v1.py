# Bowden McAdam Grandstand, real geometry. Stand frame: s along the front (south->north), t back (into the stand), z up.
# Field frame = pitch centre origin, y along the pitch. Measurements: aerial ref.jpg (front edge), satellite (depth), t7/w04 (heights).
import numpy as np,json,math
O=np.array([-72.4,-15.0]);A=np.array([-74.0,14.9])-O;L=float(np.linalg.norm(A));a=A/L;b=np.array([a[1]*-1,a[0]])*-1
b=np.array([-a[1],a[0]]);b=-b if b[0]>0 else b   # back = west
def W(s,t,z):p=O+s*a+t*b;return [float(p[0]),float(p[1]),float(z)]
G=[]
def mesh(name,mat,V,F):G.append(dict(name=name,mat=mat,V=V,F=F))
def box(name,mat,s0,s1,t0,t1,z0,z1,faces='all'):
    V=[W(s0,t0,z0),W(s1,t0,z0),W(s1,t1,z0),W(s0,t1,z0),W(s0,t0,z1),W(s1,t0,z1),W(s1,t1,z1),W(s0,t1,z1)]
    F={'bottom':[0,3,2,1],'top':[4,5,6,7],'front':[0,1,5,4],'right':[1,2,6,5],'back':[2,3,7,6],'left':[3,0,4,7]}
    for k,f in F.items():
        if faces=='all' or k in faces:mesh(name+'_'+k,mat if isinstance(mat,str) else mat.get(k,mat['*']),V,[f])
def quad(name,mat,P4):mesh(name,mat,P4,[[0,1,2,3]])
# ---------------- parameters (metres) ----------------
P=dict(zF=11.45,zC=10.9,tC=11.4,tB=24.4,zBack=6.8,flare=0.5,cn_t0=10.4,cn_z0=10.3,scal=0.5,flareL=3.0,fasc=0.35,
       box_s0=2.8,box_s1=26.9,box_t0=4.8,box_t1=10.8,box_z0=6.52,box_z1=10.0,
       pl_s0=1.7,pl_s1=28.3,pl_t=0.6,pl_z=2.25,rows=7,row_d=0.7,row_h=0.3,walk=1.0,
       wall_t=21.8,wall_z=4.35,south_s=-5.0,tw_s0=27.2,tw_s1=29.9,tw_t0=5.0,tw_t1=10.0,tw_z=10.0)
def roof_z(s,t):
    z=P['zF']+(P['zC']-P['zF'])*t/P['tC']
    e=max(0.0,1-min(s,L-s)/P['flareL']);f=max(0.0,1-t/P['tC'])
    return z+P['flare']*e*e*f
def build():
    G.clear()
    # main roof blade: a grid so the end flares bend
    ns,nt=11,4;S=np.linspace(0,L,ns);T=np.linspace(0,P['tC'],nt);V=[];F=[]
    for t in T:
        for s in S:V.append(W(s,t,roof_z(s,t)))
    for j in range(nt-1):
        for i in range(ns-1):F.append([j*ns+i,j*ns+i+1,(j+1)*ns+i+1,(j+1)*ns+i])
    mesh('roof_top','roof_top',V,F)
    Vu=[[x,y,z-P['fasc']] for x,y,z in V];mesh('roof_soffit','roof_soffit',Vu,[f[::-1] for f in F])
    # fascia (front edge) and ends
    V=[];F=[]
    for i,s in enumerate(S):V+= [W(s,0,roof_z(s,0)-P['fasc']),W(s,0,roof_z(s,0))]
    for i in range(ns-1):F.append([2*i,2*i+2,2*i+3,2*i+1])
    mesh('roof_fascia','roof_fascia',V,F)
    for s,nm in((0,'S'),(L,'N')):
        V=[];F=[]
        for t in T:V+=[W(s,t,roof_z(s,t)-P['fasc']),W(s,t,roof_z(s,t))]
        for j in range(nt-1):F.append([2*j,2*j+1,2*j+3,2*j+2] if nm=='S' else [2*j,2*j+2,2*j+3,2*j+1])
        mesh('roof_end'+nm,'roof_fascia',V,F)
    # back canopy: starts under the main roof, falls to the back edge; edge scalloped (high mid-bay, low at struts)
    nb=5;ns2=41;S2=np.linspace(0,L,ns2);nt2=6;T2=np.linspace(P['cn_t0'],P['tB'],nt2);V=[];F=[]
    for t in T2:
        u=(t-P['cn_t0'])/(P['tB']-P['cn_t0'])
        for s in S2:
            sc=P['scal']*abs(math.sin(math.pi*nb*s/L))*u*u
            V.append(W(s,t,P['cn_z0']+(P['zBack']-P['cn_z0'])*u+sc))
    for j in range(nt2-1):
        for i in range(ns2-1):F.append([j*ns2+i,j*ns2+i+1,(j+1)*ns2+i+1,(j+1)*ns2+i])
    mesh('canopy_top','canopy',V,F);mesh('canopy_under','canopy_under',[[x,y,z-0.15] for x,y,z in V],[f[::-1] for f in F])
    # box (corporate level)
    zt=lambda t:P['box_z1']
    s0,s1,t0,t1,z0=P['box_s0'],P['box_s1'],P['box_t0'],P['box_t1'],P['box_z0']
    quad('box_front','box_front',[W(s0,t0,z0),W(s1,t0,z0),W(s1,t0,zt(t0)),W(s0,t0,zt(t0))])
    quad('box_back','box_back',[W(s1,t1,z0),W(s0,t1,z0),W(s0,t1,zt(t1)),W(s1,t1,zt(t1))])
    quad('box_endS','box_end',[W(s0,t1,z0),W(s0,t0,z0),W(s0,t0,zt(t0)),W(s0,t1,zt(t1))])
    quad('box_endN','box_end',[W(s1,t0,z0),W(s1,t1,z0),W(s1,t1,zt(t1)),W(s1,t0,zt(t0))])
    quad('box_under','box_under',[W(s0,t1,z0),W(s1,t1,z0),W(s1,t0,z0),W(s0,t0,z0)])
    # ground floor: plinth front, the seat deck, concourse floor, back wall
    pt,pz=P['pl_t'],P['pl_z']
    quad('plinth_front','plinth',[W(P['pl_s0'],pt,0),W(P['pl_s1'],pt,0),W(P['pl_s1'],pt,pz),W(P['pl_s0'],pt,pz)])
    t=pt;z=pz;quad('walkway','deck',[W(P['pl_s0'],t,z),W(P['pl_s1'],t,z),W(P['pl_s1'],t+P['walk'],z),W(P['pl_s0'],t+P['walk'],z)]);t+=P['walk']
    V=[];F=[]
    for r in range(P['rows']):
        z1=z+P['row_h'];k=len(V)
        V+=[W(P['pl_s0'],t,z),W(P['pl_s1'],t,z),W(P['pl_s1'],t,z1),W(P['pl_s0'],t,z1),W(P['pl_s1'],t+P['row_d'],z1),W(P['pl_s0'],t+P['row_d'],z1)]
        F+=[[k,k+1,k+2,k+3],[k+3,k+2,k+4,k+5]];t+=P['row_d'];z=z1
    mesh('seat_tiers','seats',V,F)
    zc=z;P['conc_t']=t
    quad('concourse','deck',[W(P['pl_s0'],t,zc),W(P['pl_s1'],t,zc),W(P['pl_s1'],P['wall_t'],zc),W(P['pl_s0'],P['wall_t'],zc)])
    quad('back_wall','back_wall',[W(P['pl_s1'],P['wall_t'],0),W(P['south_s'],P['wall_t'],0),W(P['south_s'],P['wall_t'],zc),W(P['pl_s1'],P['wall_t'],zc)])
    quad('rear_under','soffit_dark',[W(P['pl_s0'],t,0.01),W(P['pl_s1'],t,0.01),W(P['pl_s1'],t,zc),W(P['pl_s0'],t,zc)])
    # south block: tan wall carrying the stair from level 1 down to the walkway
    ss=P['south_s']
    quad('south_front','south_wall',[W(ss,pt,0),W(P['pl_s0'],pt,0),W(P['pl_s0'],pt,zc),W(ss,pt,zc)])
    quad('south_end','south_wall',[W(ss,P['wall_t'],0),W(ss,pt,0),W(ss,pt,zc),W(ss,P['wall_t'],zc)])
    quad('south_top','deck',[W(ss,pt,zc),W(P['pl_s0'],pt,zc),W(P['pl_s0'],P['wall_t'],zc),W(ss,P['wall_t'],zc)])
    # north lift tower
    box('lift',{'*':'lift'},P['tw_s0'],P['tw_s1'],P['tw_t0'],P['tw_t1'],0,P['tw_z'])
    return G
if __name__=='__main__':
    build();json.dump(dict(G=G,P=P,O=O.tolist(),a=a.tolist(),b=b.tolist(),L=L),open('stand.json','w'));print(len(G),'meshes L=%.2f'%L,'a',a,'b',b)
