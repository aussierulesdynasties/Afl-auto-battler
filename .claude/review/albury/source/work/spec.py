# Albury Sports Ground exterior: one spec read by the wireframe check (wire.py) and the Blender build.
# Metres, x east, y north, z up from ground. Footprints from OSM (osm/geo.json); heights read off Earth views.
import json,math,os
_D=json.load(open(os.path.join(os.path.dirname(__file__),'..','osm','geo.json'),encoding='utf-8'))
def fp(i):
    p=_D[str(i)]['pts']
    if p[0]==p[-1]:p=p[:-1]
    return [tuple(q) for q in p]
def obb(pts):
    best=None
    for i in range(len(pts)):
        a,b=pts[i],pts[(i+1)%len(pts)];ang=math.atan2(b[1]-a[1],b[0]-a[0]);c,s=math.cos(ang),math.sin(ang)
        us=[x*c+y*s for x,y in pts];vs=[-x*s+y*c for x,y in pts]
        A=(max(us)-min(us))*(max(vs)-min(vs))
        if best is None or A<best[0]:
            u0,u1,v0,v1=min(us),max(us),min(vs),max(vs);uc,vc=(u0+u1)/2,(v0+v1)/2
            best=(A,(uc*c-vc*s,uc*s+vc*c),u1-u0,v1-v0,math.degrees(ang))
    _,cen,L,W,a=best
    if W>L:L,W,a=W,L,a+90
    return dict(c=cen,L=L,W=W,a=a)
def rect(c,L,W,a):
    ca,sa=math.cos(math.radians(a)),math.sin(math.radians(a));u=(ca,sa);v=(-sa,ca)
    return [(c[0]+su*L/2*u[0]+sv*W/2*v[0],c[1]+su*L/2*u[1]+sv*W/2*v[1]) for su,sv in((-1,-1),(1,-1),(1,1),(-1,1))]
# Each building: walls = footprint polygon to eave height; roofs = list of parts on oriented rectangles.
B={}
def bld(name,i,eave,roofs,mat='brick',roofmat='steel_grey'):
    B[name]=dict(fp=fp(i),eave=eave,roofs=roofs,mat=mat,roofmat=roofmat)
def part(r,kind,eave,ridge,over=0.4):
    return dict(r=r,kind=kind,eave=eave,ridge=ridge,over=over)
o=obb(fp(482327969));bld('grandstand',482327969,8.5,[part(o,'hip',8.5,12.5)])
o=dict(obb(fp(482327971)));o['a']-=180;bld('north_hall',482327971,5.0,[part(o,'hip0',5.0,7.2)])  # u east: hip at the west end, gable at the east end (g_nw_180)
o=obb(fp(482327966));bld('west_bldg',482327966,6.0,[part(o,'gable',6.0,8.5)])
o=obb(fp(482327972));bld('ne_bldg',482327972,4.0,[part(o,'hip',4.0,6.5)],roofmat='roof_bluegrey')
o=obb(fp(482327955));bld('ne_corner',482327955,3.0,[part(o,'gable',3.0,4.5)])
o=obb(fp(482330189));bld('n_small',482330189,2.8,[part(o,'gable',2.8,4.0)])
o=obb(fp(482327967));bld('w_small',482327967,3.0,[part(o,'flat',3.0,3.0)])
# club_n: 4.2 m main block, lower 3.2 m ribbed strip at the north end (g_e_270 step at y -17.4)
_s=[(78.48,-17.4),(77.06,-27.33),(78.26,-27.70),(78.04,-29.38),(80.12,-29.63),(80.46,-28.06),(87.77,-29.21),(89.40,-17.74),(87.24,-17.4)]
_n=[(79.63,-13.92),(79.26,-16.11),(78.68,-16.01),(78.48,-17.4),(87.24,-17.4),(85.40,-17.11),(85.98,-14.97)]
B['club_n']=dict(fp=_s,eave=4.2,roofs=[part(obb(_s),'flat',4.2,4.2)],mat='brick',roofmat='roof_white')
B['club_n2']=dict(fp=_n,eave=3.2,roofs=[part(obb(_n),'flat',3.2,3.2)],mat='brick',roofmat='roof_deck')
o=obb(fp(482327956));bld('club',482327956,8.5,[part(o,'flat',8.5,8.5)])
o=obb(fp(482327962));bld('se_a',482327962,3.5,[part(o,'gable',3.5,5.0)])
o=obb(fp(482327963));bld('se_b',482327963,3.5,[part(o,'gable',3.5,5.0)],roofmat='roof_white')
# se_c (OSM 482327960) left out: white fabric marquee, free-standing (lead ruling 2026-11-18)
o1=obb([(-47.0,66.7),(-48.7,68.8),(-54.9,65.1),(-59.9,59.1),(-66.0,63.8),(-63.2,67.0),(-63.8,68.6),(-50.6,77.3)]);o2=obb([(-46.6,80.2),(-40.5,71.3),(-47.0,66.7),(-53.1,75.6)])
def _trim(o,pt):  # cut the box's east end back to pt (projected on its long axis): the main roof ends inside the cross wing
    a=math.radians(o['a']);ux,uy=math.cos(a),math.sin(a)
    if o['L']<o['W']:ux,uy=-uy,ux
    if ux<0:ux,uy=-ux,-uy
    L=o['L'] if o['L']>=o['W'] else o['W'];w0=-L/2;w1=(pt[0]-o['c'][0])*ux+(pt[1]-o['c'][1])*uy;m=(w0+w1)/2
    return dict(c=(o['c'][0]+ux*m,o['c'][1]+uy*m),L=w1-w0,W=min(o['L'],o['W']),a=math.degrees(math.atan2(uy,ux)))
o1=_trim(o1,(-46.8,73.45))
bld('nw_wing',482327970,4.0,[part(o1,'hip0',4.0,6.5),part(o2,'hip',4.0,6.5)],mat='brick_dark',roofmat='roof_bluegrey')  # long block + cross wing at the east end (g_nw_180)
TANKS=[(fp(482330184),6.0),(fp(482330185),6.0)]
