# World geometry for everything except the Gorringe (gor.py), as (verts, material) faces -> geo2.json.
# Plans and heights from world.json (aerial 1182_185). Stand sections from the 2023 photo (hr_three) where the stand stood in 1992.
import json,math,numpy as np,shapely
from shapely.geometry import Polygon,LineString,Point
D=json.load(open('world.json'));C0=np.array([-5.0,-1.6])
OBJ={}
def F(name,vs,mat):OBJ.setdefault(name,[]).append(([[float(c) for c in v] for v in vs],mat))
def tris(poly):
    g=shapely.constrained_delaunay_triangles(poly)
    return [list(t.exterior.coords)[:3] for t in g.geoms]
def ring_ccw(c):
    c=list(c);A=sum(c[i][0]*c[(i+1)%len(c)][1]-c[(i+1)%len(c)][0]*c[i][1] for i in range(len(c)));return c if A>0 else c[::-1]
def prism(name,poly,z0,z1,top,side,bot=None):
    if poly.is_empty:return
    for p in getattr(poly,'geoms',[poly]):
        if p.geom_type!='Polygon' or p.area<1e-4:continue
        for t in tris(p):
            t=ring_ccw(t);F(name,[(x,y,z1) for x,y in t],top)
            if bot:F(name,[(x,y,z0) for x,y in t[::-1]],bot)
        for ring in [p.exterior]+list(p.interiors):
            c=list(ring.coords)
            for i in range(len(c)-1):
                (a,b),(cc,d)=c[i],c[i+1];F(name,[(a,b,z0),(cc,d,z0),(cc,d,z1),(a,b,z1)],side)
def rows(name,poly,front,z0,tread,riser,zmax,bench=True,top='tread',side='concrete'):
    # stepped rows by distance from the front line, clipped to the plan; last level is a flat walkway
    k=0
    while True:
        a=front.buffer(k*tread,cap_style='flat') if k else None
        b=front.buffer((k+1)*tread,cap_style='flat')
        band=poly.intersection(b) if a is None else poly.intersection(b).difference(a)
        z=min(zmax,z0+(k+1)*riser)
        if band.is_empty and k>0 and poly.difference(b).is_empty:break
        last=z>=zmax or poly.difference(b).area<0.5
        if last:band=poly.difference(a) if a is not None else poly
        prism(name,band,0,z,top,side)
        if bench and not last:
            s=poly.intersection(front.buffer(k*tread+0.7,cap_style='flat')).difference(front.buffer(k*tread+0.35,cap_style='flat'))
            prism(name+'_bench',s,z,z+0.42,'bench','bench')
        if last:break
        k+=1
def wall(name,p,q,z0,z1,mat):F(name,[(p[0],p[1],z0),(q[0],q[1],z0),(q[0],q[1],z1),(p[0],p[1],z1)],mat)
def post(name,c,z0,z1,w,mat):
    x,y=c;h=w/2;P=[(x-h,y-h),(x+h,y-h),(x+h,y+h),(x-h,y+h)]
    for i in range(4):wall(name,P[i],P[(i+1)%4],z0,z1,mat)
def flatroof(name,poly,z,top,under,edge,th=0.6):
    prism(name,poly,z-th,z,top,edge,bot=under)
def S(n):return next(s for s in D['structs'] if s['name']==n)
def xy(v):return np.array(v[:2],float)
def front_edges(L):
    n=len(L);sc=[]
    for i in range(n):
        a,b=L[i],L[(i+1)%n];m=(a+b)/2;t=b-a;nrm=np.array([t[1],-t[0]]);nrm/=np.linalg.norm(nrm)
        if np.dot(nrm,m-np.mean(L,0))<0:nrm=-nrm
        sc.append(np.dot(nrm,(C0-m)/np.linalg.norm(C0-m)))
    return sc
# ---------- Ryde St stand: hip roof, field slope painted white (aerial), seating rows under
s=S('ryde_stand');V=[np.array(v) for v in s['v']];L=[xy(V[i]) for i in s['walls']]
plan=Polygon(L);fr=LineString([L[2],L[3]])
rows('ryde',plan.buffer(-0.3),fr,0.6,0.8,0.4,4.6)
for (i,j) in[(0,1),(1,2),(3,0)]:wall('ryde',L[i],L[j],0,7.9,'cladding_grey')
for t in np.linspace(0,1,6):post('ryde',L[2]+(L[3]-L[2])*t,0,7.9,0.25,'steel_dark')
for f,mat in[([0,1,5,4],'roof_iron'),([1,2,5],'roof_white'),([2,3,4,5],'roof_white'),([3,0,4],'roof_white')]:   # hip ends white (aerial)
    F('ryde_roof',[V[i] for i in f][::-1],mat);F('ryde_roof',[V[i]-np.array([0,0,0.15]) for i in f],'steel_dark')
for i in range(4):a,b=V[i],V[(i+1)%4];wall('ryde_roof',a[:2],b[:2],7.6,7.9,'fascia')
_e0,_e1=V[2][:2],V[3][:2];_ed=(_e1-_e0)/np.linalg.norm(_e1-_e0)
def _foot(q):return np.r_[_e0+_ed*np.dot(q[:2]-_e0,_ed),7.9]
_n=np.cross(V[4]-_foot(V[4]),V[5]-V[4]);_n=_n/np.linalg.norm(_n)*(1 if np.cross(V[4]-_foot(V[4]),V[5]-V[4])[2]>0 else -1)*0.03
F('ryde_nab',[_foot(V[4])+_n,_foot(V[5])+_n,V[5]+_n,V[4]+_n],'roof_nab')
# ---------- SE (Cazaly) stand, section from the 1965 and 2009 photos (same stand): white front plinth 2.5, bench rows
# to 9.3, open ends with a raked concrete side wall and a glazed screen on the back part, back columns, thin roof slab
# with a dark underside on tapered lattice trusses. Plan and roof height (12.6) from the aerial. Back wall clad (no photo).
s=S('se_white_stand');L=[xy(v) for v in s['v']];plan=Polygon(L);fr=LineString([L[3],L[0]])
rows('se',plan.buffer(-0.2),fr,2.5,0.8,0.45,9.3)
wall('se',L[1],L[2],0,12.3,'cladding_grey');wall('se',L[3],L[0],0,2.5,'render_cream')
def beam(name,p,q,w,mat):
    p,q=np.array(p,float),np.array(q,float);d=q-p;d/=np.linalg.norm(d);u=np.cross(d,[0,0,1]);u=u/np.linalg.norm(u) if np.linalg.norm(u)>1e-6 else np.array([1,0,0]);v=np.cross(u,d)
    c=[(u*a+v*b)*w/2 for a,b in((-1,-1),(1,-1),(1,1),(-1,1))]
    for k in range(4):F(name,[p+c[k],p+c[(k+1)%4],q+c[(k+1)%4],q+c[k]],mat)
dep=np.linalg.norm(L[1]-L[0]);rk=lambda f:2.5+(9.3-2.5)*f+1.0     # side wall top: rake + 1 m parapet
for fr_,bk_,sg in((L[0],L[1],1),(L[3],L[2],-1)):
    dd=(bk_-fr_)/dep;inn=np.array([-dd[1],dd[0]])*sg*0.0
    F('se',[(*fr_,0),(*bk_,0),(*bk_,rk(1)),(*fr_,rk(0))],'concrete')
    g0=fr_+dd*dep*0.4;F('se_glass',[(*g0,rk(0.4)),(*bk_,rk(1)),(*bk_,12.3),(*g0,12.3)],'glass_screen')
for t in np.linspace(0.02,0.98,6):
    b=L[1]+(L[2]-L[1])*t;f=L[0]+(L[3]-L[0])*t;dd=(f-b)/np.linalg.norm(f-b);b=b+dd*0.6
    post('se',b,0,12.3,0.4,'steel_dark')
    n=int(np.linalg.norm(f-b)//1.5);top=lambda s_:np.r_[b+(f+dd*0.3-b)*s_,12.25];bot=lambda s_:np.r_[b+(f+dd*0.3-b)*s_,11.0+0.9*s_]
    beam('se_truss',top(0),top(1),0.14,'steel_dark');beam('se_truss',bot(0),bot(1),0.14,'steel_dark')
    for k in range(n):beam('se_truss',bot(k/n),top((k+1)/n),0.08,'steel_dark');beam('se_truss',top(k/n),bot(k/n),0.08,'steel_dark')
flatroof('se_roof',plan.buffer(0.3,join_style='mitre'),12.6,'roof_white','steel_dark','trim_white',th=0.35)
# ---------- Lewis St stand: hip roof (aerial hips), stand floor on the bank (5.12), skylight strip on the rear slope
s=S('lewis_stand');V=[np.array(v) for v in s['v']];L=[xy(V[i]) for i in range(4)]
ax=(L[1]-L[0])/np.linalg.norm(L[1]-L[0]);E5,H5=13.0,15.5
m0=(np.r_[L[0],0]+np.r_[L[3],0])/2;m1=(np.r_[L[1],0]+np.r_[L[2],0])/2;hd=np.linalg.norm(L[0]-L[3])/2
r0=np.r_[(m0[:2]+ax*hd),H5];r1=np.r_[(m1[:2]-ax*hd),H5];E=[np.r_[l,E5] for l in L]
for f,mat in[([E[0],E[1],r1,r0],'roof_iron'),([E[1],E[2],r1],'roof_iron'),([E[2],E[3],r0,r1],'roof_iron'),([E[3],E[0],r0],'roof_iron')]:
    F('lewis_roof',f[::-1],mat);F('lewis_roof',[p-np.array([0,0,0.15]) for p in f],'steel_dark')
# skylight strip on the street-side slope, 1.3-3.0 m (plan) down from the ridge, between the hips (aerial g_lewis)
# strip centreline read off the aerial: (3885,3047)->(4173,2767), ~1.6 m wide; laid on the plane of the rear slope
_M={};exec(open('meas.py').read(),_M);Wm=lambda u,v,h:np.array([float(c) for c in _M['at_z'](_M['p'],*_M['F2']((u,v)),h)])
rr=(r1-r0)[:2];rr/=np.linalg.norm(rr);nn=np.array([rr[1],-rr[0]])
if np.dot(nn,L[3]-L[0])<0:nn=-nn
pit=(H5-E5)/hd
def onroof(q):d=np.dot(q-r0[:2],nn);return np.r_[q,H5-pit*d+0.03]
c0,c1=Wm(3885,3047,14.4)[:2],Wm(4173,2767,14.4)[:2]
q=[onroof(c0-nn*0.8),onroof(c1-nn*0.8),onroof(c1+nn*0.8),onroof(c0+nn*0.8)];F('lewis_roof',q,'roof_clear')
for i in range(4):wall('lewis_roof',L[i],L[(i+1)%4],E5-0.3,E5,'fascia')
plan=Polygon(L);fr=LineString([L[0],L[1]])
rows('lewis',plan.buffer(-0.3),fr,5.12,0.8,0.4,10.3)
for (i,j) in[(1,2),(2,3),(3,0)]:wall('lewis',L[i],L[j],0,E5,'cladding_grey')
for t in np.linspace(0,1,5):post('lewis',L[0]+(L[1]-L[0])*t,5.12,E5,0.3,'steel_dark')
# ---------- Letitia St stand: white flat roof 15.0, curved field face, rows under, columns at the back
s=S('letitia_stand');L=[xy(v) for v in s['v']];plan=Polygon(L);fr=LineString([L[1],L[2],L[3],L[4]])
rows('letitia',plan.buffer(-0.2),fr,2.0,0.8,0.45,11.0)
for (i,j) in[(4,5),(5,6),(6,7),(7,8),(8,0),(0,1)]:wall('letitia',L[i],L[j],0,14.4,'cladding_grey')
for i in(5,6,7,8):post('letitia',L[i]+(np.mean(L,0)-L[i])/np.linalg.norm(np.mean(L,0)-L[i])*0.6,0,14.4,0.4,'steel_dark')
flatroof('letitia_roof',plan.buffer(0.3,join_style='mitre'),15.0,'roof_white','steel_dark','trim_white')
# sheds, small buildings and trees removed: director 2026-11-18 'just get the stadium model done not extra stuff'
for n in('bench0','bench1','bench2'):
    s=S(n);L=[xy(v) for v in s['v']];prism(n,Polygon(L),0,1.5,'roof_white','trim_white')
# ---------- scoreboards. NE board per the 1990 photo: grey base, black number board, red header (lettering left off)
# top at 10.0 m to match the 1992 aerial (ground lead 2026-11-19); base and face heights scaled together from the 12.8 m build
SBT=10.0;SBB=3.4*SBT/12.8
s=S('ne_board');L=[xy(v) for v in s['v']];sc=front_edges(L);fi=int(np.argmax(sc))
P=Polygon(L);prism('ne_board',P,0,SBT,'steel_dark','cladding_grey')
a,b=L[fi],L[(fi+1)%4];o=np.array([b[1]-a[1],-(b[0]-a[0])]);o/=np.linalg.norm(o)
if np.dot(o,(a+b)/2-np.mean(L,0))<0:o=-o
a2,b2=a+o*0.03,b+o*0.03
OBJ.setdefault('ne_board_face',[]).append(([[*b2,SBB],[*a2,SBB],[*a2,SBT],[*b2,SBT]],'sb_face'))
s=S('scoreboard_n');L=[xy(v) for v in s['v']];prism('scoreboard_n',Polygon(L),0,8.5,'roof_white','render_cream')   # 1992 aerial: pale roof, long shadow; world.json col cream; face unknown (no photo)
# ---------- light poles (aerial shadows), terraces, fence, wall, trees, ground
for i,p in enumerate(D['poles']):
    for k in range(8):
        t0,t1=2*math.pi*k/8,2*math.pi*(k+1)/8;r0,r1=0.2,0.08;x,y=p['xy']
        F('poles',[(x+r0*math.cos(t0),y+r0*math.sin(t0),0),(x+r0*math.cos(t1),y+r0*math.sin(t1),0),(x+r1*math.cos(t1),y+r1*math.sin(t1),p['h']),(x+r1*math.cos(t0),y+r1*math.sin(t0),p['h'])],'pole_grey')
T=D['terraces'][0]['grid'];fr_,bk_=np.array(T[0]),np.array(T[1]);n=len(fr_);NS=8;RZ=bk_[0][2]/NS
for k in range(NS):
    t0,t1=k/NS,(k+1)/NS;z=(k+1)*RZ
    A=fr_[:,:2]+(bk_[:,:2]-fr_[:,:2])*t0;B=fr_[:,:2]+(bk_[:,:2]-fr_[:,:2])*t1
    for i in range(n-1):
        F('north_terrace',[(*A[i],z),(*A[i+1],z),(*B[i+1],z),(*B[i],z)][::-1] if ((A[i+1]-A[i])[0]*(B[i]-A[i])[1]-(A[i+1]-A[i])[1]*(B[i]-A[i])[0])<0 else [(*A[i],z),(*A[i+1],z),(*B[i+1],z),(*B[i],z)],'tread')
        F('north_terrace',[(*A[i],z-RZ),(*A[i+1],z-RZ),(*A[i+1],z),(*A[i],z)],'concrete')
    F('north_terrace',[(*A[0],0),(*B[0],0),(*B[0],z),(*A[0],z)],'concrete');F('north_terrace',[(*A[-1],0),(*B[-1],0),(*B[-1],z),(*A[-1],z)],'concrete')
for i in range(n-1):F('north_terrace',[(*bk_[i,:2],0),(*bk_[i+1,:2],0),(*bk_[i+1,:2],NS*RZ),(*bk_[i,:2],NS*RZ)],'concrete')
eb=D['slabs'][0]['v'];P=Polygon([q[:2] for q in eb]).buffer(0)
fr=LineString([q[:2] for q in eb[:4]]);dmax=max(fr.distance(Point(q[:2])) for q in eb);nr=max(1,int(dmax/0.8));rows('east_bank',P,fr,eb[0][2],dmax/nr,2.4/nr,eb[0][2]+2.4,bench=False)
for f in D['fences']:
    pts=f['xy']+([f['xy'][0]] if f.get('closed') else [])
    for i in range(len(pts)-1):wall(f['name'],pts[i],pts[i+1],0,f['h'],'fence_white' if f['col']=='white' else 'render_cream')
# fence boards removed: director 2026-11-18 sponsor boards 'C: no boards', bare fence at every ground
# goal and behind posts removed: director 2026-11-18 'Posts out' (the game draws its own posts)
# ground outside the boundary fence only: director 2026-11-18 "Leave field out" (the game draws its own grass inside)
import shapely
_ring=Polygon(D['base']).buffer(0).difference(Polygon(D['fences'][0]['xy']).buffer(0))
_tri=[list(t.exterior.coords)[:3] for t in shapely.constrained_delaunay_triangles(_ring).geoms]
print('ground ring area',round(_ring.area),'tris',len(_tri))
json.dump(dict(objs=OBJ,base=D['base'],fence=D['fences'][0]['xy'],ground_tris=_tri),open('geo2.json','w'))
print({k:len(v) for k,v in OBJ.items()})
