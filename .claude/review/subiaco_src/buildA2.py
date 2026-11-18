# Subiaco Oval 1991 (version A), built in world metres (x east, y north, z up) from photo refs/c/01.jpg through
# the fitted camera camA_final.json; all positions from measureA.py -> layoutA.json. Hand-made textures in tex/.
#   blender -b --python buildA.py -- SPDIR OUT.glb RENDER.png
import bpy,bmesh,sys,math,json
import numpy as np
from mathutils import Vector,Matrix
SP,OUT,REN=sys.argv[sys.argv.index('--')+1:]
J=json.load(open(SP+'/layoutA.json'));C0=J['C0'];FJ=J['fence'];co=FJ['co'];K=FJ['K'];RK=J['RAKE']
def rf(a):
    t=math.radians(a);return sum(co[k]*math.cos(k*t) for k in range(K+1))+sum(co[K+k]*math.sin(k*t) for k in range(1,K+1))
def P(a,d,z):
    r=rf(a)+d;t=math.radians(a);return Vector((C0[0]+r*math.cos(t),C0[1]+r*math.sin(t),z))
def unwrap(a,ref):
    while a<ref-180:a+=360
    while a>ref+180:a-=360
    return a
def fn(samples,col,ref):
    S=sorted((unwrap(s[0],ref),s[col]) for s in samples);A=[s[0] for s in S];D=[s[1] for s in S]
    return lambda a:float(np.interp(unwrap(a,ref),A,D))
bpy.ops.wm.read_factory_settings(use_empty=True)
me=bpy.data.meshes.new('subiacoA');ob=bpy.data.objects.new('subiacoA',me);bpy.context.scene.collection.objects.link(ob)
MI={}
def mat(name,rough=0.85):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(SP+'/texA/'+name+'.png')
    nt.links.new(t.outputs['Color'],b.inputs['Base Color']);b.inputs['Roughness'].default_value=rough
    import colorsys;m.diffuse_color=(*colorsys.hsv_to_rgb((len(MI)*0.618)%1,0.6,0.9),1);me.materials.append(m);MI[name]=len(me.materials)-1
for n in('turf','paint','terrace','seats','roof','roofd','wall','brick','under','fascia','asphalt','paving','picket','steel','can','glass','score','concrete','rail'):mat(n)
bm=bmesh.new();uv=bm.loops.layers.uv.new()
def face(vs,m,uvs=None):
    if uvs is None:uvs=[(0,0),(1,0),(1,1),(0,1)]+[(0,0)]*max(0,len(vs)-4)
    f=bm.faces.new([bm.verts.new(v) for v in vs]);f.material_index=MI[m]
    for l,q in zip(f.loops,uvs):l[uv].uv=q
    return f
def angles(a0,a1,step=1.0):
    n=max(1,int(round(abs(a1-a0)/step)));return [a0+(a1-a0)*i/n for i in range(n+1)]
def sweep(a0,a1,prof,mats,tile=4.0,step=1.0):
    A=angles(a0,a1,step);cols=[[P(a,d,z) for d,z in prof(a)] for a in A];u=0.0
    for i in range(len(A)-1):
        c0,c1=cols[i],cols[i+1];du=(c1[0]-c0[0]).length/tile
        for k in range(len(c0)-1):
            if mats[k] is None:continue
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
sweep(-180,180,lambda a:[(0,0),(0,1.1)],['picket'],tile=2.0,step=0.5)
# ---------------- great grandstand (photo: lower tier from the fence, white balcony, roofed upper tier, flat roof)
GS=[g for g in J['GS'] if 92<=g[0]<=166];HR=J['HR']
_cb=np.polyfit([g[0] for g in GS],[g[1] for g in GS],4);_cf=np.polyfit([g[2] for g in GS],[g[3] for g in GS],4)
def dB(a):return float(np.polyval(_cb,min(max(a,92),166)))
def dF(a):return float(np.polyval(_cf,min(max(a,92),166)))
def gs_prof(a):
    df,db=dF(a),dB(a)
    return [(0,0),(0,1.1),(0.4,1.1),(df-0.6,7.6),(df-0.6,8.7),(df+1.0,8.7),(db-0.6,15.4),(db-0.6,16.0),(db,16.0),(db,0)]
GA0,GA1=89.5,168.0
sweep(GA0,GA1,gs_prof,['wall','wall','seats','fascia','under','seats','wall','wall','brick'],tile=4)
for a in(GA0,GA1):endcap(a,gs_prof,'brick')
def gs_roof(a):df,db=dF(a),dB(a);return [(df-0.4,HR-1.0),(df-0.4,HR),(db+0.3,HR),(db+0.3,HR-0.6),(df-0.4,HR-0.6)]
sweep(GA0,GA1,gs_roof,['fascia','roof','fascia','under'],tile=4)
for a in(GA0,GA1):endcap(a,gs_roof,'fascia')
sweep(GA0,GA1,lambda a:[(dB(a),16.0),(dB(a),HR-0.6)],['brick'],tile=4)   # back wall up to the roof
def column(p0,p1,b,m='fascia'):
    for e0,e1 in(((b,b),(-b,b)),((-b,b),(-b,-b)),((-b,-b),(b,-b)),((b,-b),(b,b))):
        o0=Vector((e0[0],e0[1],0));o1=Vector((e1[0],e1[1],0));face([p0+o0,p0+o1,p1+o1,p1+o0],m)
for a in angles(GA0+2,GA1-2,8):column(P(a,dF(a)+0.6,8.7),P(a,dF(a)+0.6,HR-0.6),0.18)
# ---------------- west stand with the dark ribbed roof (sloping 10 m front to 12 m back)
rF=fn(J['RIBF'],1,180);rB=fn(J['RIBB'],1,180);RA0,RA1=168.0,195.8
def rib_prof(a):df,db=rF(a),rB(a);return [(0,0),(0,1.1),(0.4,1.1),(db-0.6,9.6),(db,9.6),(db,0)]
sweep(RA0,RA1,rib_prof,['wall','wall','seats','wall','brick'],tile=4)
for a in(RA0,RA1):endcap(a,rib_prof,'brick')
def rib_roof(a):df,db=rF(a),rB(a);return [(df,9.4),(df,10.0),(db+0.3,12.0),(db+0.3,11.5),(df,9.4)]
sweep(RA0,RA1,rib_roof,['fascia','roofd','fascia','under'],tile=4)
for a in(RA0,RA1):endcap(a,rib_roof,'roofd')
sweep(RA0,RA1,lambda a:[(rB(a),9.6),(rB(a),11.5)],['brick'],tile=4)
for a in angles(RA0+1.5,RA1-1.5,6):column(P(a,rF(a)+0.8,1.1+(rF(a)+0.8)*8.5/max(1,rB(a))),P(a,rF(a)+0.8,9.6),0.15)
# ---------------- north stand (photo x 634-770): straight building; terrace to its front wall, seats, flat roof at 14 m
NSr=J['NS'];NSF=J['NSF2'];NA0,NA1=NSr[3][0],NSr[0][0]
def lerp(p,q,t):return p+(q-p)*t
def ns_cols(t):
    fw=lerp(P(NSF[1][0],NSF[1][1],0),P(NSF[0][0],NSF[0][1],0),t);bk=lerp(P(NSr[2][0],NSr[2][1],0),P(NSr[1][0],NSr[1][1],0),t)
    rf_=lerp(P(NSr[3][0],NSr[3][1],0),P(NSr[0][0],NSr[0][1],0),t);a=angof(fw);fe=P(a,0,0);ed=(fw-fe).length;zf=0.5+RK*ed
    dirn=(bk-fw).normalized();Z=lambda z:Vector((0,0,z))
    body=[fe,fe+Z(1.1),fe+(fw-fe).normalized()*0.4+Z(0.5),fw+Z(zf),fw+Z(zf+1.2),fw+dirn*0.4+Z(zf+1.2),bk-dirn*0.6+Z(11.0),bk+Z(11.0),bk]
    mid=lerp(rf_,bk+dirn*0.3,0.5);roof=[rf_+Z(13.2),rf_+Z(13.6),mid+Z(15.0),bk+dirn*0.3+Z(13.6),bk+dirn*0.3+Z(13.2),rf_+Z(13.2)]
    return body,roof,bk,fw,zf,dirn
def sweepT(fn_,mats,n=24,tile=4.0):
    cols=[fn_(i/n) for i in range(n+1)];u=0.0
    for i in range(n):
        c0,c1=cols[i],cols[i+1];du=(c1[0]-c0[0]).length/tile
        for k in range(len(c0)-1):
            if mats[k] is None:continue
            l=(c0[k+1]-c0[k]).length/tile;face([c0[k],c1[k],c1[k+1],c0[k+1]],mats[k],[(u,0),(u+du,0),(u+du,l),(u,l)])
        u+=du
    return cols
cb=sweepT(lambda t:ns_cols(t)[0],['wall','wall','terrace','fascia','fascia','seats','wall','brick'])
cr=sweepT(lambda t:ns_cols(t)[1],['fascia','roof','roof','fascia','under'])
for c in(cb[0],cb[-1]):
    try:face(c,'brick',[(0,0)]*len(c))
    except ValueError:pass
for c in(cr[0],cr[-1]):
    try:face(c[:5],'fascia')
    except ValueError:pass
sweepT(lambda t:[ns_cols(t)[2]+Vector((0,0,11.0)),ns_cols(t)[2]+Vector((0,0,13.4))],['brick'])
for i in range(6):
    t=(i+0.5)/6;_,_,bk,fw,zf,dn=ns_cols(t);b=fw+dn*0.6;column(b+Vector((0,0,zf+1.2)),b+Vector((0,0,13.2)),0.15)
def nsRB(a):return 26.0
# ---------------- open terraces: concrete steps from the fence up to the outer wall (photo crowd edge, rake 0.15)
def terr_prof(do,top=1.2):
    zo=0.5+RK*do;return [(0,0),(0,1.1),(0.4,0.5),(do,zo),(do,zo+top),(do+0.35,zo+top),(do+0.35,0)]
TM=['wall','wall','terrace','wall','wall','wall']
oE=fn(J['OUT'],1,10);sweep(-44.0,53.4,lambda a:terr_prof(oE(a),1.0),TM,tile=4)
WL=J['WALL']+[(-44.0,oE(-44.0),0)];oS=fn(WL,1,-100)
sweep(-153.6,-44.0,lambda a:terr_prof(oS(a),1.2),TM,tile=4)
def oSW(a):return oS(-153.6)+(a+153.6)/(-10.6)*(rB(-164.2)-oS(-153.6))
sweep(-164.2,-153.6,lambda a:terr_prof(oSW(a),1.2),TM,tile=4)
sweep(82.6,89.5,lambda a:terr_prof(20.0,1.2),TM,tile=4)
for a,do in((-164.2,rB(-164.2)),(53.4,oE(53.4)),(82.6,20.0),(89.5,20.0)):endcap(a,lambda a,do=do:terr_prof(do)[2:],'wall')
# SE white screens standing on the terrace (photo x 934-1022; heights measured off the photo, 4.5-7 m)
PN=J['PAN2']
for (a0,d0,z0,h0),(a1,d1,z1,h1) in zip(PN,PN[1:]):
    q=[P(a0,d0,z0),P(a1,d1,z1),P(a1,d1+0.4,z1),P(a0,d0+0.4,z0)];H0=Vector((0,0,h0));H1=Vector((0,0,h1))
    face([q[0],q[1],q[1]+H1,q[0]+H0],'wall');face([q[3],q[2],q[2]+H1,q[3]+H0],'wall');face([q[0]+H0,q[1]+H1,q[2]+H1,q[3]+H0],'wall')
# ---------------- buildings embedded in the stadium (roof outlines from the photo, heights per building)
def block(pts,z1,wallm='wall',roofm='roof',z0=0.0):
    V=[P(a,d,z0) for a,d,*_ in pts];T=[P(a,d,z1) for a,d,*_ in pts];n=len(V)
    for i in range(n):face([V[i],V[(i+1)%n],T[(i+1)%n],T[i]],wallm,[(0,0),(1,0),(1,z1/4),(0,z1/4)])
    try:face(T,roofm,[((q.x)/8,(q.y)/8) for q in T])
    except ValueError:pass
block(J['B1'],5.0);block(J['B4'],4.0);block(J['K1'],9.6,'wall','roof',6.5);block(J['B2'],4.0);block(J['B3'],4.0)
block(J['ADM'],10.0,'wall','roof')
ca,cd,_=J['CAN'];cb=P(ca,cd,5.0)
for j in range(16):
    t0=2*math.pi*j/16;t1=2*math.pi*(j+1)/16;o0=Vector((math.cos(t0),math.sin(t0),0))*2.2;o1=Vector((math.cos(t1),math.sin(t1),0))*2.2
    face([cb+o0,cb+o1,cb+o1+Vector((0,0,6.5)),cb+o0+Vector((0,0,6.5))],'can',[(j/16,0),((j+1)/16,0),((j+1)/16,1),(j/16,1)])
face([cb+Vector((math.cos(2*math.pi*j/16)*2.2,math.sin(2*math.pi*j/16)*2.2,6.5)) for j in range(16)],'steel',[(0,0)]*16)
# SE light pole: tapered, thicker at the base (0.45 m radius to 0.2 m), small lamp frame on top
px,py,ph=J['POLE'];pb=Vector((px,py,0))
for j in range(10):
    t0=2*math.pi*j/10;t1=2*math.pi*(j+1)/10;c0=Vector((math.cos(t0),math.sin(t0),0));c1=Vector((math.cos(t1),math.sin(t1),0))
    face([pb+c0*0.45,pb+c1*0.45,pb+c1*0.2+Vector((0,0,ph)),pb+c0*0.2+Vector((0,0,ph))],'steel')
hc=pb+Vector((0,0,ph+0.8))
face([hc+Vector((-1.5,0,-0.8)),hc+Vector((1.5,0,-0.8)),hc+Vector((1.5,0,0.8)),hc+Vector((-1.5,0,0.8))],'steel')


# back walls: pilasters every 5 degrees and the first-floor slab edge (era concrete frame showing through the brick)
for a in angles(GA0+1,GA1-1,5):column(P(a,dB(a)+0.3,0),P(a,dB(a)+0.3,HR-0.6),0.3,'concrete')
sweep(GA0,GA1,lambda a:[(dB(a)+0.05,8.3),(dB(a)+0.45,8.3),(dB(a)+0.45,8.9),(dB(a)+0.05,8.9)],['concrete','concrete','concrete'],tile=4)
for a in angles(RA0+1,RA1-1,5):column(P(a,rB(a)+0.3,0),P(a,rB(a)+0.3,11.5),0.3,'concrete')
# ---------------- crush barriers on the open terraces: galvanised rail 1.0 m above the step, 7 m bays with 1.5 m gaps,
# rows every 4.5 m up the slope, alternate rows staggered half a bay; posts every 2.3 m
def bar(p0,p1,w,h,m):
    dv=(p1-p0);n=Vector((-dv.y,dv.x,0)).normalized()*w/2;Z=Vector((0,0,h))
    c=[p0-n,p0+n,p1+n,p1-n]
    face([c[0],c[3],c[3]+Z,c[0]+Z],m);face([c[2],c[1],c[1]+Z,c[2]+Z],m);face([c[0]+Z,c[3]+Z,c[2]+Z,c[1]+Z],m)
def barriers(a0,a1,dout):
    k=0
    while True:
        d=3.5+4.5*k
        if all(d>dout(a)-1.5 for a in angles(a0,a1,2)):break
        r=rf((a0+a1)/2)+d;bay=math.degrees(7.0/r);gp=math.degrees(1.5/r);a=a0+(bay+gp)*(0.5 if k%2 else 0.0)+gp/2
        while a+bay<a1:
            if d<dout(a)-1.5 and d<dout(a+bay)-1.5:
                z0=0.5+RK*d;A_=angles(a,a+bay,1.0)
                for i in range(len(A_)-1):bar(P(A_[i],d,z0+0.96),P(A_[i+1],d,z0+0.96),0.06,0.06,'rail')
                m=max(2,int(7.0/2.3))
                for j in range(m+1):
                    aj=a+bay*j/m;column(P(aj,d,z0),P(aj,d,z0+0.96),0.025,'rail')
            a+=bay+gp
        k+=1
# radial aisles: 1.2 m stair strips (0.2 m half-steps) every 9 degrees across each terrace
def aisles(a0,a1,dout,every=9.0):
    a=a0+every/2
    while a<a1-1:
        r=rf(a);w=math.degrees(0.6/(r+10));do=dout(a);zo=0.5+RK*do
        q=[P(a-w,0.4,0.53),P(a+w,0.4,0.53),P(a+w,do,zo+0.03),P(a-w,do,zo+0.03)];L=(do-0.4)/math.cos(math.atan(RK))
        face(q,'terrace',[(0,0),(0.3,0),(0.3,L/2),(0,L/2)]);a+=every
for a0,a1,fo in((-44.0,53.4,oE),(-153.6,-44.0,oS),(-164.2,-153.6,oSW)):
    barriers(a0,a1,fo);aisles(a0,a1,fo)
barriers(82.6,89.5,lambda a:20.0)
# ---------------- west stand: white steel girders sitting on the dark deck (photo zA_Wb: long back runs, short front stubs)
for a in angles(RA0+1.8,RA1-1.8,3.6):
    df,db=rF(a),rB(a);zr=lambda d:10.0+(d-df)/(db+0.3-df)*2.0
    for d0,d1 in((db,db-0.45*(db-df)),(df+0.15*(db-df),df+0.3)):
        bar(P(a,d0,zr(d0)),P(a,d1,zr(d1)),0.35,0.55,'fascia')
# ---------------- east scoreboard (K1): the box sits on the terrace top; its face looks across the ground
KB=J['K1'];kz0,kz1=6.5,9.6
fq=[P(KB[3][0],KB[3][1]-0.05,kz0),P(KB[0][0],KB[0][1]-0.05,kz0),P(KB[0][0],KB[0][1]-0.05,kz1),P(KB[3][0],KB[3][1]-0.05,kz1)]
face(fq,'score',[(1,0),(0,0),(0,1),(1,1)])
for kk in(1,2):column(P(KB[kk][0],KB[kk][1],0),P(KB[kk][0],KB[kk][1],kz0),0.15,'steel')
# ---------------- ground apron (paved surround) under the whole footprint
def outer(a):
    if -44<=a<=53.4:return oE(a)
    if -153.6<=a<-44:return oS(a)
    if -164.2<=a<-153.6:return oSW(a)
    if 89.5<=a<=168:return dB(a)
    if a>168 or a<-164.2:return rB(a)
    if 53.4<a<82.6:return nsRB(a)
    return 20.0
A=angles(-44,53.4,1.5)
for i in range(len(A)-1):
    a,b=A[i],A[i+1]
    face([P(a,outer(a)+0.4,0.01),P(b,outer(b)+0.4,0.01),P(b,outer(b)+10,0.01),P(a,outer(a)+10,0.01)],'paving',[(0,0),(1,0),(1,2),(0,2)])
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
if len(sys.argv)>sys.argv.index('--')+4:pass
render(sys.argv[-1] if sys.argv[-1].endswith('.json') else 'camA_final.json',1200,676,REN.replace('.png','_geo.png'),True)
render('camA_final.json',1200,676,REN)
