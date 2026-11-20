# Subiaco Oval 1997 (version B, redo to the new gate: texB/ hand-made 1024 px textures, photo-read ribs and aisles, daylight render), built in world metres (x east, y north, z up) from photo refs/c/17.jpg through
# the fitted camera camB.json; all positions from measureA.py -> layoutA.json. Hand-made textures in tex/.
#   blender -b --python buildA.py -- SPDIR OUT.glb RENDER.png
import bpy,bmesh,sys,math,json,os
import numpy as np
from mathutils import Vector,Matrix
SP,OUT,REN=sys.argv[sys.argv.index('--')+1:]
J=json.load(open(SP+'/layoutA.json'));C0=J['C0'];FJ=J['fence'];co=FJ['co'];K=FJ['K'];RK=J['RAKE']
def rf(a):
    t=math.radians(a);return sum(co[k]*math.cos(k*t) for k in range(K+1))+sum(co[K+k]*math.sin(k*t) for k in range(1,K+1))
FOT=json.load(open(SP+'/nsfo.json'));fo=lambda a:float(np.interp(a,[t[0] for t in FOT],[t[1] for t in FOT]))
WARP=None
def P(a,d,z):
    if WARP:a=a+WARP(a,d)
    r=rf(a)+d;t=math.radians(a);return Vector((C0[0]+r*math.cos(t),C0[1]+r*math.sin(t),z))
def unwrap(a,ref):
    while a<ref-180:a+=360
    while a>ref+180:a-=360
    return a
def fn(samples,col,ref):
    S=sorted((unwrap(s[0],ref),s[col]) for s in samples);A=[s[0] for s in S];D=[s[1] for s in S]
    return lambda a:float(np.interp(unwrap(a,ref),A,D))
bpy.ops.wm.read_factory_settings(use_empty=True)
me=bpy.data.meshes.new('subiacoB');ob=bpy.data.objects.new('subiacoB',me);bpy.context.scene.collection.objects.link(ob)
MI={}
def mat(name,rough=0.85):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(SP+'/texB/'+name+'.png')
    nt.links.new(t.outputs['Color'],b.inputs['Base Color']);b.inputs['Roughness'].default_value=rough
    import colorsys;m.diffuse_color=(*colorsys.hsv_to_rgb((len(MI)*0.618)%1,0.6,0.9),1);me.materials.append(m);MI[name]=len(me.materials)-1
for n in('turf','paint','terrace','seats','roof','roofd','wall','brick','under','fascia','asphalt','paving','picket','steel','can','glass','seatsb','facade','pad','bank','ads','lamps','facaded','aisle','roofcg'):mat(n)
bm=bmesh.new();uv=bm.loops.layers.uv.new()
def face(vs,m,uvs=None):
    if uvs is None:uvs=[(0,0),(1,0),(1,1),(0,1)]+[(0,0)]*max(0,len(vs)-4)
    f=bm.faces.new([bm.verts.new(v) for v in vs]);f.material_index=MI[m]
    for l,q in zip(f.loops,uvs):l[uv].uv=q
    return f
def angles(a0,a1,step=1.0):
    n=max(1,int(round(abs(a1-a0)/step)));return [a0+(a1-a0)*i/n for i in range(n+1)]
def sweep(a0,a1,prof,mats,tile=4.0,step=1.0,vabs=False):
    A=angles(a0,a1,step);cols=[[P(a,d,z) for d,z in prof(a)] for a in A];u=0.0
    for i in range(len(A)-1):
        c0,c1=cols[i],cols[i+1];du=(c1[0]-c0[0]).length/tile
        for k in range(len(c0)-1):
            if mats[k] is None:continue
            if vabs:  # vertical facades: v = height in metres / tile, so floor lines stay level between segments
                face([c0[k],c1[k],c1[k+1],c0[k+1]],mats[k],[(u,c0[k].z/tile),(u+du,c1[k].z/tile),(u+du,c1[k+1].z/tile),(u,c0[k+1].z/tile)]);continue
            l=(c0[k+1]-c0[k]).length/tile
            face([c0[k],c1[k],c1[k+1],c0[k+1]],mats[k],[(u,0),(u+du,0),(u+du,l),(u,l)])
        u+=du
def endcap(a,prof,m):
    pts=[P(a,d,z) for d,z in prof(a)]
    if len(pts)>=3:
        try:face(pts,m,[(i/len(pts),0) for i in range(len(pts))])
        except ValueError:pass
# ---------------- field
A=angles(-180,180,1.5);tc=Vector((C0[0],C0[1],0.0))
for i in range(len(A)-1):
    continue  # director 2026-11-18 'Leave field out': no turf, the game draws its own grass
    pa,pb=P(A[i],0,0),P(A[i+1],0,0);face([tc,pa,pb],'turf',[((q.x-C0[0])/32,(q.y-C0[1])/32) for q in(tc,pa,pb)])
Uv=Vector((J['U'][0],J['U'][1],0));Vv=Vector((-Uv.y,Uv.x,0));Cc=Vector((C0[0],C0[1],0));Lg=J['L']
def line(p0,p1,w=0.12,z=0.04):
    d=(p1-p0);n=Vector((-d.y,d.x,0)).normalized()*w;Z=Vector((0,0,z))
    return  # field markings belong to the field, left out with it
def poly(pts,closed=False,w=0.12):
    for i in range(len(pts)-(0 if closed else 1)):line(pts[i],pts[(i+1)%len(pts)],w)
au=math.degrees(math.atan2(Uv.y,Uv.x))
def gap(a):c=abs(math.cos(math.radians(a-au)));return 4.5+3.3*c**6
def angof(p):q=p-Cc;return math.degrees(math.atan2(q.y,q.x))
poly([P(a,-gap(a),0) for a in angles(-180,180,2)],True,0.1)                  # boundary line through both goal lines
sq=[Cc+Uv*sx*22.5+Vv*sy*22.5 for sx,sy in((1,1),(1,-1),(-1,-1),(-1,1))];poly(sq,True)   # 45 m centre square (pre-2004)
for r in(1.5,5.0):poly([Cc+Uv*r*math.cos(t)+Vv*r*math.sin(t) for t in np.linspace(0,2*math.pi,40)],True)
line(Cc+Uv*-2.0,Cc+Uv*2.0)
for s in(1,-1):
    g=Cc+Uv*s*Lg
    pts=[g+(Uv*math.cos(t)+Vv*math.sin(t))*50 for t in np.linspace(0,2*math.pi,360)]
    ins=[p for p in pts if (p-Cc).length<rf(angof(p))-gap(angof(p))-0.3 and (p-Cc).dot(Uv)*s<Lg]
    ins.sort(key=lambda p:math.atan2((p-g).dot(Vv),-(p-g).dot(Uv)*s));poly(ins)
    poly([g+Vv*3.2,g+Vv*3.2-Uv*s*9,g-Vv*3.2-Uv*s*9,g-Vv*3.2])                        # goal square 6.4 x 9
    for k,h in((-9.6,10.0),(-3.2,15.0),(3.2,15.0),(9.6,10.0)):                          # goal and behind posts
        continue  # director 2026-11-18 'Posts out': the game draws its own posts
        b=g+Vv*k;n=8
        for j in range(n):
            t0=2*math.pi*j/n;t1=2*math.pi*(j+1)/n;o0=Vector((math.cos(t0),math.sin(t0),0))*0.15;o1=Vector((math.cos(t1),math.sin(t1),0))*0.15
            face([b+o0,b+o1,b+o1+Vector((0,0,h)),b+o0+Vector((0,0,h))],'fascia')
# picket fence on the fence line
sweep(-180,180,lambda a:[(fo(a),0),(fo(a),1.1)],['picket'],tile=2.0,step=0.5)   # on the photo's fence line (fo, north side)
# ================= 1997 (version B) parts, all from layoutB.json (measured on refs/c/17.jpg through camB.json)
JB=json.load(open(SP+'/layoutB.json'))
def fD(S,ref):return fn(S,1,ref)
def fZ(S,ref):return fn(S,2,ref)
def fP(S,col,ref,deg=3):
    A_=np.array([unwrap(s[0],ref) for s in S]);V_=np.array([s[col] for s in S]);c=np.polyfit(A_,V_,min(deg,len(S)-1));lo,hi=A_.min(),A_.max()
    return lambda a:float(np.polyval(c,min(max(unwrap(a,ref),lo),hi)))
def block(pts,z1,wallm='wall',roofm='roof',z0=0.0):
    V=[P(a,d,z0) for a,d,*_ in pts];T=[P(a,d,z1) for a,d,*_ in pts];n=len(V)
    for i in range(n):face([V[i],V[(i+1)%n],T[(i+1)%n],T[i]],wallm,[(0,0),(1,0),(1,z1/4),(0,z1/4)])
    try:face(T,roofm,[((q.x)/8,(q.y)/8) for q in T])
    except ValueError:pass
def tube(b,h,r0,r1,m='steel',n=10):
    for j in range(n):
        t0=2*math.pi*j/n;t1=2*math.pi*(j+1)/n;c0=Vector((math.cos(t0),math.sin(t0),0));c1=Vector((math.cos(t1),math.sin(t1),0))
        face([b+c0*r0,b+c1*r0,b+c1*r1+Vector((0,0,h)),b+c0*r1+Vector((0,0,h))],m)
# ---- near bowl (south and near side, under one long roof): front rows from the fence, roof measured on both edges
SF=[[a,max(d,0.5),z] for a,d,z in JB['SF']];SB=JB['SB']
# the roof's west end is oblique in photo 17 (send.py): front edge ends at -133.7, back edge at -128.1; the last 20 deg
# of the near bowl are pulled in by up to that much, linear in depth, so the end edge lands on the photo's edge
WARP=lambda a,d:max(0.0,1-(a+141.4)/20.0)*min(13.3,max(6.5,7.7+(d-2.7)*5.6/14.7)) if a<-121.4 else 0.0
sfd,sfz,sbd,sbz=fP(SF,1,-70),fP(SF,2,-70),fP(SB,1,-70),fP(SB,2,-70)
def nb_prof(a):
    dF,zF,dB,zB=sfd(a),sfz(a),sbd(a),sbz(a)
    return [(0,0),(0,1.2),(0.8,1.2),(dB-1.0,zB-4.0),(dB,zB),(dF,zF),(dF,zF-1.0)]
NBM=['wall','fascia','seatsb','wall',None,'fascia']
sweep(-141.4,-4.3,nb_prof,NBM,tile=4)
sweep(-141.4,-95,lambda a:nb_prof(a)[4:6],['roof'],tile=4);sweep(-95,-4.3,lambda a:nb_prof(a)[4:6],['roofd'],tile=4)
sweep(-141.4,-4.3,lambda a:[(sbd(a),0),(sbd(a),sbz(a))],['facaded'],tile=16,vabs=True)
endcap(-141.4,lambda a:[(0,0),(sbd(a),0),(sbd(a),sbz(a)),(sfd(a),sfz(a)),(0,1.2)],'wall')
WARP=None
# ---- near-right stand: concrete multi-storey block with a dark flat roof
NRF,NRB=JB['NRF'],JB['NRB'];nfd,nfz,nbd=fD(NRF,10),fZ(NRF,10),fD(NRB,10)
def nr_prof(a):dF,z=nfd(a),nfz(a);dB=max(nbd(a),dF+8);return [(0,0),(0,1.2),(0.8,1.2),(dB-1,z-4),(dB,z),(dF,z),(dF,z-1.0)]
sweep(-4.3,33.2,nr_prof,['wall','fascia','seatsb','wall','roofd','fascia'],tile=4)
sweep(-4.3,33.2,lambda a:[(nr_prof(a)[4][0],0),nr_prof(a)[4]],['facade'],tile=16,vabs=True)
endcap(-4.3,lambda a:[(0,0),(nr_prof(a)[4][0],0),nr_prof(a)[4],nr_prof(a)[5],(0,1.2)],'wall')
endcap(-4.3,lambda a:[(0,0),(sbd(a),0),(sbd(a),sbz(a)),(sfd(a),sfz(a)),(0,1.2)],'wall')
endcap(33.2,lambda a:[(0,0),(nr_prof(a)[4][0],0),nr_prof(a)[4],nr_prof(a)[5],(0,1.2)],'wall')
# ---- north stand, measured on 17.jpg. Main section 62.3-119.5 is a straight stand: the s2 walkway, the white s1 walkway and the
# roof's front and back edges are straight parallel lines (strline.py -> nslines.json); the lower tier's white front wall
# follows fo(a), so the lower rake changes with depth and the walkway stays level. West section 119.5-136.5 (wsolve3.py): lower
# rows to the yellow s2 line, back rows to a white walkway at 12-13 m, a dark back wall, and its own light roof slab built from
# the four photo corners, about 3 m above the walkway. East end 33.2-62.3 keeps the older fitted profile (no roof).
BF=JB['BF'];bfd,bfz=fP(BF,1,100),fP(BF,2,100)
def rkm(a):return (bfz(a)-2.4)/(bfd(a)-0.8)
def pv(c,a,lo=75.0,hi=119.5):return float(np.polyval(c,min(max(a,lo),hi)))
LNS=json.load(open(SP+'/nslines2.json'))   # walkway lines re-fitted on the photo (walkfit.py)
def dline(a,k):
    (px,py),(ux,uy)=LNS[k];t=math.radians(a);ex,ey=math.cos(t),math.sin(t);px-=C0[0];py-=C0[1]
    return (px*uy-py*ux)/(ex*uy-ey*ux)-rf(a)
Z1C=6.2   # walkway level used by walkfit.py
ZRF,ZRB=pv([0.00254,-0.510358,38.626569],95),pv([-0.000627,0.113438,11.580262],95)
def nsM(a):  # main section: straight lines
    F=fo(a)+0.1;d2,d1f,d1b,dRF,dRB=[dline(a,k) for k in('d2','d1f','d1b','dRF','dRB')]
    m=(Z1C-1.2)/(d1f-F-0.8);rk=lambda d:1.2+(d-F-0.8)*m
    return dict(F=F,rk=rk,d2=d2,z2=rk(d2-0.6),d1f=d1f,z1=Z1C,d1b=d1b,dRF=dRF,zRF=ZRF,dRB=dRB,zRB=ZRB)
def nsE(a):  # east end: older fitted profile
    F=fo(a)+0.1;m=rkm(a);rk=lambda d:1.2+(d-F-0.8)*m
    d2=pv([0.000976,-0.175185,20.756503],a);d1f=pv([0.003841,-0.753024,53.632603],a);d1b=pv([0.000612,-0.168759,30.243754],a)
    return dict(F=F,rk=rk,d2=d2,z2=rk(d2-0.6),d1f=d1f,z1=rk(d1f),d1b=d1b)
WTOP=15.4
def nsW(a):  # west section, linear fits of the yellow line and the white walkway (wsolve3.py)
    F=fo(a)+0.1;m=rkm(a);rk=lambda d:1.2+(d-F-0.8)*m
    d2=17.85-0.245*(a-125.4);d1f=22.18-0.387*(a-129.04)
    return dict(F=F,rk=rk,d2=d2,z2=rk(d2-0.6),d1f=d1f,z1=rk(d1f),d1b=d1f+1.5)
def zr(N,d):return N['zRF']+(d-N['dRF'])*(N['zRB']-N['zRF'])/(N['dRB']-N['dRF'])
def zs(N,d):  # seat surface height at depth d
    if d<=N['d2']+0.6:return N['rk'](min(d,N['d2']-0.6))
    return N['z2']+(d-N['d2']-0.6)*(N['z1']-N['z2'])/(N['d1f']-N['d2']-0.6)
def prM(a):
    N=nsM(a);F=N['F']
    return [(F,0),(F,1.2),(F+0.8,1.2),(N['d2']-0.6,N['z2']),(N['d2']+0.6,N['z2']),(N['d1f'],N['z1']),(N['d1b'],N['z1']),(N['d1b'],zr(N,N['d1b'])-0.05)]
def prW(a):
    N=nsW(a);F=N['F']
    return [(F,0),(F,1.2),(F+0.8,1.2),(N['d2']-0.6,N['z2']),(N['d2']+0.6,N['z2']),(N['d1f'],N['z1']),(N['d1b'],N['z1']),(N['d1b'],WTOP)]
def prE(a):
    N=nsE(a);F=N['F']
    return [(F,0),(F,1.2),(F+0.8,1.2),(N['d2']-0.6,N['z2']),(N['d2']+0.6,N['z2']),(N['d1f'],N['z1']),(N['d1b'],N['z1']),(N['d1b'],0)]
SM=['wall','fascia','seatsb','aisle','seatsb','aisle','under']
sweep(33.2,62.3,prE,SM,tile=4)
sweep(62.3,119.5,prM,SM,tile=4)
sweep(119.5,136.5,prW,SM,tile=4)
sweep(119.5,136.5,lambda a:[(nsW(a)['d1b'],WTOP),(nsW(a)['d1b'],0)],['under'],tile=4)          # back of the west back wall
sweep(62.3,119.5,lambda a:[(nsM(a)['dRF'],ZRF-0.6),(nsM(a)['dRF'],ZRF),(nsM(a)['dRB'],ZRB)],['fascia','roof'],tile=4)
sweep(62.3,119.5,lambda a:[(nsM(a)['dRB'],ZRB-0.05),(nsM(a)['dRF'],ZRF-0.6)],['under'],tile=4)   # soffit
sweep(62.3,119.5,lambda a:[(nsM(a)['dRB'],0),(nsM(a)['dRB'],ZRB-0.05)],['wall'],tile=4,vabs=True)  # outer back wall
for a in(62.3,119.5):
    N=nsM(a);pr=prM(a)
    endcap(a,lambda a_:pr[:-1]+[(pr[-1][0],zr(N,pr[-1][0])),(N['dRF'],N['zRF']-0.6),(N['dRF'],N['zRF']),(N['dRB'],N['zRB']),(N['dRB'],0)],'under' if a>100 else 'wall')   # west end in shadow in photo 17
endcap(62.3,lambda a:prE(a),'wall');endcap(33.2,lambda a:prE(a),'wall')
endcap(119.5,lambda a:prW(a)+[(nsW(a)['d1b'],0)],'wall');endcap(136.5,lambda a:prW(a)+[(nsW(a)['d1b'],0)],'wall')
# west roof slab: corners back-projected from the photo (front edge z 16.0, back edge z 17.5), fascia round the edge
WR=[Vector(v) for v in([-71.48,80.11,16.0],[-56.48,89.23,16.0],[-58.56,98.24,17.5],[-72.36,89.41,17.5])]   # WF EF EB WB
face(WR,'roof',[((q.x)/8,(q.y)/8) for q in WR])
D6=Vector((0,0,-0.6))
for i in range(4):
    p,q=WR[i],WR[(i+1)%4];face([p+D6,q+D6,q,p],'fascia')
face([q+D6 for q in WR[::-1]],'under')
face([WR[3]+D6,WR[2]+D6,Vector((WR[2].x,WR[2].y,0)),Vector((WR[3].x,WR[3].y,0))],'under')                   # back wall, dark in photo 17
face([WR[0]+D6,WR[3]+D6,Vector((WR[3].x,WR[3].y,0)),Vector((WR[0].x,WR[0].y,0))],'under')                    # west side, in shadow
# low grey building at the stand's west end (wsolve3.py, top at 3 m)
block([(142.35,32.35),(142.66,40.03),(138.19,40.33),(137.99,33.6)],3.0,'under','asphalt')
# corner block: dark sides, mid-grey corrugated roof whose valleys run along (-0.172,0.985), 6.5 m apart (crvalley.py)
CRP=[P(a,d,0) for a,d,*_ in JB['CR']];CRT=[P(a,d,18.0) for a,d,*_ in JB['CR']]
for i in range(len(CRP)):face([CRP[i],CRP[(i+1)%len(CRP)],CRT[(i+1)%len(CRP)],CRT[i]],'under',[(0,0),(1,0),(1,4.5),(0,4.5)])
cd_,cn_=Vector((-0.172,0.985,0)),Vector((-0.985,-0.172,0))
face(CRT,'roofcg',[((q.dot(cn_)+66.35)/6.5,q.dot(cd_)/6.5) for q in CRT])
# ---- west end under construction: bare lit pad, grass bank, perimeter boards
W1,W2=JB['W1'],JB['W2'];w1d,w2d=fD(W1,170),fD(W2,170)
sweep(136.0,196.0,lambda a:[(fo(a)+0.1,0.05),(w1d(a),0.3)],['pad'],tile=12)
sweep(136.0,196.0,lambda a:[(w1d(a),0.3),(w2d(a),3.0)],['bank'],tile=8)
sweep(142.0,192.0,lambda a:[(w2d(a),3.0),(w2d(a),5.4)],['wall'],tile=24)
sweep(196.0,218.6,lambda a:[(0.1,0.05),(w1d(a)*0.9,0.3)],['pad'],tile=12)                 # SW corner pad to the near roof
# two low white site buildings on the west pad, roofs back-projected from photo 17 (wbld.py): B1 mono-pitch, B2 gable
WB=json.load(open(SP+'/wbld.json'));V=lambda q:Vector(q);G0=lambda q:Vector((q[0],q[1],0.0))
def wq(vs,m):
    L=(Vector(vs[1])-Vector(vs[0])).length/4;face([V(q) if not isinstance(q,Vector) else q for q in vs],m,[(0,0),(L,0),(L,1),(0,1)]+[(0,0)]*max(0,len(vs)-4))
def wall(q0,q1,m='wall'):wq([G0(q0),G0(q1),V(q1),V(q0)],m)
r=WB['B1']['roof']
face([V(q) for q in r],'roof',[(q[0]/4,q[1]/4) for q in r])
for i in range(4):wall(r[i],r[(i+1)%4])
we,rg,ee=WB['B2']['we'],WB['B2']['rg'],WB['B2']['ee']
face([V(we[0]),V(we[1]),V(rg[1]),V(rg[0])],'roof',[(q[0]/4,q[1]/4) for q in(we[0],we[1],rg[1],rg[0])])
face([V(rg[0]),V(rg[1]),V(ee[1]),V(ee[0])],'roof',[(q[0]/4,q[1]/4) for q in(rg[0],rg[1],ee[1],ee[0])])
wall(we[0],we[1]);wall(ee[1],ee[0])
for k in(0,1):face([G0(we[k]),V(we[k]),V(rg[k]),V(ee[k]),G0(ee[k])],'wall',[(0,0),(0,0.7),(0.5,0.9),(1,0.7),(1,0)])   # gable ends
block(JB['FL1'],8.0,'brick','roofd');block(JB['FL2'],5.0,'wall','roofd')
# ---- four light towers: tapered (thicker at the base), lamp head facing the centre
for x,y,h in JB['TOW']:
    b=Vector((x,y,0));tube(b,h-3.0,0.9,0.45,'steel',12)
    c=Vector((x,y,h-3.0));t=(Cc-c);t.z=0;t.normalize();s=Vector((-t.y,t.x,0))*3.2;up=Vector((0,0,3.0))+t*0.6
    face([c-s,c+s,c+s+up*2,c-s+up*2],'lamps',[(0,0),(1,0),(1,1),(0,1)]);face([c-s-t*0.4,c-s-t*0.4+up*2,c+s-t*0.4+up*2,c+s-t*0.4],'steel')

# ---------------- details read off the photo (ribB.py: pale lines in zB_nr2.png / zB_ns2.png -> fence angles via camB)
def bar(p0,p1,w,h,m):
    dv=(p1-p0);n=Vector((-dv.y,dv.x,0)).normalized()*w/2;Z=Vector((0,0,h))
    c=[p0-n,p0+n,p1+n,p1-n]
    face([c[0],c[3],c[3]+Z,c[0]+Z],m);face([c[2],c[1],c[1]+Z,c[2]+Z],m);face([c[0]+Z,c[3]+Z,c[2]+Z,c[1]+Z],m)
# near roof: white steel roof girders running front to back over the sheeting
for a in(-92.8,-77.8,-65.0,-55.2,-46.2,-39.2,-34.5,-30.8,-26.5,-21.8,-16.2,-10.8,-5.0):
    bar(P(a,sfd(a)+0.3,sfz(a)),P(a,sbd(a)-0.3,sbz(a)),0.45,0.35,'fascia')
if os.environ.get('ZONEDUMP'):
    out={}
    for zone,fs in((0,[0.15,0.3,0.45,0.6,0.75,0.9]),(1,[0.15,0.35,0.55,0.75,0.9])):
        for f in fs:
            rows=[]
            for i in range(560,1370):
                a=i/10;NF=nsM if a<119.5 else nsW
                if a<62.3:continue
                N=NF(a);d=(N['F']+0.8+f*(N['d2']-0.6-N['F']-0.8)) if zone==0 else (N['d2']+0.6+f*(N['d1f']-N['d2']-0.6))
                q=P(a,d,zs(N,d));rows.append([a,q.x,q.y,q.z])
            out['%d_%.2f'%(zone,f)]=rows
    json.dump(out,open(SP+'/zonedump.json','w'))
# north stand aisles, read off 17.jpg on the corrected stand (nsais2.py): 1.2 m white strips, each a straight line in
# (angle, depth fraction) from its front angle a0 to its back angle a1; lower zone front wall -> s2, back zone s2 -> s1
def aisle(a0,a1,NF,zone):
    pts=[]
    for i in range(11):
        f=i/10;a=a0+(a1-a0)*f;N=NF(a)
        d=(N['F']+0.8+f*(N['d2']-0.6-N['F']-0.8)) if zone==0 else (N['d2']+0.6+f*(N['d1f']-N['d2']-0.6))
        w=math.degrees(0.6/(rf(a)+d));pts.append((P(a-w,d,zs(N,d)+0.03),P(a+w,d,zs(N,d)+0.03)))
    L=0.0
    for i in range(10):
        l=(pts[i+1][0]-pts[i][0]).length/4;face([pts[i][0],pts[i][1],pts[i+1][1],pts[i+1][0]],'aisle',[(0,L),(0.3,L),(0.3,L+l),(0,L+l)]);L+=l
for a0,a1 in((59.8,56.6),(65.3,63.3),(75.6,73.3),(85.0,83.8),(94.9,93.9),(104.9,103.3),(115.0,112.2)):aisle(a0,a1,nsM,0)
for a0,a1 in((123.5,118.7),(128.9,123.1),(134.5,128.9)):aisle(a0,a1,nsW,0)
for a0,a1 in((74.6,73.4),(83.8,82.0),(93.9,91.6),(101.6,101.6),(110.3,111.4),(119.0,119.8)):aisle(a0,a1,nsM,1)
for a0,a1 in((125.8,123.6),(130.8,130.0)):aisle(a0,a1,nsW,1)
# ---------------- matched-camera render
def daylight(sc):
    try:sc.render.engine='BLENDER_EEVEE'
    except TypeError:sc.render.engine='BLENDER_EEVEE_NEXT'
    w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;bg=w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value=(0.62,0.72,0.86,1);bg.inputs['Strength'].default_value=0.75
    ld=bpy.data.lights.new('sun','SUN');ld.energy=3.2;ld.angle=math.radians(0.6)
    so=bpy.data.objects.new('sun',ld);sc.collection.objects.link(so)
    el,az=math.radians(52),math.radians(28)                          # sun to the north, a little west (shadows fall south in the photo)
    tosun=Vector((-math.sin(az)*math.cos(el),math.cos(az)*math.cos(el),math.sin(el)))
    so.rotation_euler=(-tosun).to_track_quat('-Z','Y').to_euler()
    try:sc.eevee.taa_render_samples=48
    except Exception:pass
    sc.view_settings.view_transform='AgX'
def render(cf,W,H,out,geo=False):
    Jc=json.load(open(SP+'/'+cf));cam=Jc['p']
    cy_,sy_=math.cos(cam[3]),math.sin(cam[3]);cp,sp=math.cos(cam[4]),math.sin(cam[4]);cr,sr=math.cos(cam[5]),math.sin(cam[5])
    f=Vector((cy_*cp,sy_*cp,sp));r=Vector((sy_,-cy_,0));u=r.cross(f);R0=r*cr+u*sr;R1=-r*sr+u*cr
    cd=bpy.data.cameras.new('c');co_=bpy.data.objects.new('c',cd);bpy.context.scene.collection.objects.link(co_)
    co_.matrix_world=Matrix(((R0.x,R1.x,-f.x,cam[0]),(R0.y,R1.y,-f.y,cam[1]),(R0.z,R1.z,-f.z,cam[2]),(0,0,0,1)))
    cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=cam[6]/W*36;cd.shift_x=0;cd.shift_y=0
    cd.clip_end=20000;sc_=bpy.context.scene;sc_.camera=co_
    if geo:sc_.render.engine='BLENDER_WORKBENCH';sc_.display.shading.color_type='MATERIAL';sc_.display.shading.light='STUDIO'
    else:daylight(sc_)
    sc_.render.resolution_x=W;sc_.render.resolution_y=H;sc_.render.film_transparent=True;sc_.render.filepath=out
    bpy.ops.render.render(write_still=True)
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-4);bm.normal_update();bm.to_mesh(me);bm.free()
bpy.ops.export_scene.gltf(filepath=OUT,export_format='GLB',use_selection=False)
render('camB.json',1000,600,REN.replace('.png','_geo.png'),True)
render('camB.json',1000,600,REN)
