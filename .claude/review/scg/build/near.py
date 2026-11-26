# Brewongle + Clive Churchill (near stand) outer facade, modelled bay by bay from the unwrapped 2012 aerial (g/uw16b, uw16c)
# and the Gate B close-up (refs2/c/07.jpg). s = metres along the roof edge from 168 deg.
MATS.update({'conc':(206,200,188),'buff':(214,182,128),'glassd':(48,56,66),'slab':(228,228,224),'dark':(40,38,36)})
_J=json.load(open('g/uw16b.png.json'));_S=np.array(_J['s']);_D=np.array(_J['ds'])
def sdeg(s):return float(np.interp(s,_S,_D)) if s<=_S[-1] else float(_D[-1]+(s-_S[-1])/(_S[-1]-_S[-2])*(_D[-1]-_D[-2]))
def hiR(d):o=OUT.get(round(d*2)/2%360);return o[1] if o else None
def zoR(d):o=OUT.get(round(d*2)/2%360);return o[3] if o else None
def box(d0,d1,r0,r1,z0,z1,m,mt=None):
    """polar box between angles d0..d1 (deg), radii r0..r1 (functions or numbers), heights z0..z1"""
    f=lambda r,d:r(d) if callable(r) else r
    ds=np.linspace(d0,d1,max(2,int(abs(d1-d0)/0.5)+1))
    rows=[[P(f(r0,d),math.radians(d),z0),P(f(r1,d),math.radians(d),z0),P(f(r1,d),math.radians(d),z1),P(f(r0,d),math.radians(d),z1)] for d in ds]
    for i in range(len(rows)-1):
        A,B=rows[i],rows[i+1]
        quad(A[1],B[1],B[2],A[2],m)        # outer face
        quad(A[3],B[3],B[0],A[0],m)        # inner face
        quad(A[2],B[2],B[3],A[3],mt or m)  # top
        quad(A[0],B[0],B[1],A[1],m)        # bottom
    A=rows[0];B=rows[-1];quad(A[0],A[1],A[2],A[3],m);quad(B[3],B[2],B[1],B[0],m)
def fin(sc,hw):   # photo: fins run from the wall out to the fascia face and stop 0.4 m above the roof line
    d0,d1=sdeg(sc-hw),sdeg(sc+hw);box(d0,d1,lambda d:rw(d)-0.5,lambda d:max(hiR(d),rw(d))+0.3,0,zoR(0.5*(d0+d1))+0.4,'conc')
D0=168.0;dA1=sdeg(80.5);dB1=222.0;dC1=256.0
# fascia band round the whole stand: front face at the roof edge, from 2.3 m below the roof line to the roof line
band(lambda d:None if hiR(d) is None else [(hiR(d)-1.6,zoR(d)-2.3),(hiR(d),zoR(d)-2.3),(hiR(d),zoR(d))],D0+1,dC1,'fascia')
# --- A: brick bays 168 deg -> s 80.5
box(sdeg(-1.5),sdeg(2.5),lambda d:rw(d)-6,lambda d:rw(d)+1.2,0,23.5,'conc')           # west stair tower
band(lambda d:[(rw(d)-1.0,zoR(d)-2.3),(rw(d)+0.4,zoR(d)-2.3),(rw(d)+0.4,16.3)] ,sdeg(2.5),dA1,['conc','buff'])   # soffit under fascia, upper brick band
band(lambda d:[(rw(d)+0.4,16.3),(rw(d)+0.6,16.3),(rw(d)+0.6,15.6),(rw(d)-2.5,15.6)],sdeg(2.5),dA1,'conc')          # beam + soffit
REC=[(19.5,27.2),(44.3,52.2),(69.4,76.6)];GREY=(52.5,69.4)
def inrec(s):return any(a<=s<=b for a,b in REC)
cuts=sorted([2.5,80.5]+[x for ab in REC for x in ab])
for i in range(len(cuts)-1):
    s0,s1=cuts[i],cuts[i+1];d0,d1=sdeg(s0),sdeg(s1)
    if inrec((s0+s1)/2):
        band(lambda d:[(rw(d)-4.0,3.0),(rw(d)-4.0,15.6)],d0,d1,'dark')                                  # recessed back wall
        for za,zb in((4.3,5.8),(7.1,8.7)):box(d0+0.15,d1-0.15,lambda d:rw(d)-3.6,lambda d:rw(d)-0.4,za,zb,'conc')   # curved balconies
        for dd in(d0,d1):box(dd-0.15,dd+0.15,lambda d:rw(d)-4.0,lambda d:rw(d)+0.1,3.0,15.6,'buff')      # side walls
    else:
        zg=9.0 if (GREY[0]<=s0 and s1<=GREY[1]) else 15.6
        band(lambda d:[(rw(d),3.7),(rw(d),zg)],d0,d1,'buff')
        if zg<15.6:box(d0,d1,lambda d:rw(d),lambda d:rw(d)+2.5,3.7,15.0,'facade2')                          # grey clad box projecting 2.5 m (photo)
        for za,zb in((5.2,5.7),(9.4,9.9)):box(d0,d1,lambda d:rw(d),lambda d:rw(d)+0.25,za,min(zb,zg) if za<zg else zb,'conc')
# ground floor: canopy slab over a recessed colonnade
band(lambda d:[(rw(d)-1.6,0),(rw(d)-1.6,3.0),(rw(d)+0.9,3.0),(rw(d)+0.9,3.7),(rw(d),3.7)],sdeg(2.5),dA1,['dark','conc','conc','conc'])
for sc,hw in((9.5,1.0),(35.6,0.9),(55.6,0.6),(61.4,1.0),(68.0,0.6),(87.0,1.0)):fin(sc,hw)
# --- B: stepped glass block with white floor slabs, 205-222 deg; plan from the OSM steps
dB0=dA1
box(dB0,sdeg(84.5),lambda d:rw(d)-4,lambda d:rw(d)+0.5,0,21.5,'conc')                                  # grey lift core
band(lambda d:[(rw(d)-0.4,0),(rw(d)-0.4,13.0)],sdeg(84.5),dB1,'glassd')
for z in(3.2,6.4,9.6):box(sdeg(84.5),dB1,lambda d:rw(d)-0.4,lambda d:rw(d)+0.6,z-0.25,z+0.3,'slab')
band(lambda d:[(rw(d)+0.6,12.6),(rw(d)+0.6,13.4),(min(rw(d),hiR(d))-1.0,13.4)],sdeg(84.5),dB1,'slab')   # block roof
band(lambda d:[(min(rw(d),hiR(d))-1.0,13.4),(min(rw(d),hiR(d))-1.0,zoR(d)-2.3)],sdeg(84.5),dB1,'facade2')   # wall above the block
# --- C: Clive Churchill glass curtain wall with white bands, 222-256 deg
band(lambda d:[(rw(d),0),(rw(d),zoR(d)-2.3),(hiR(d)-1.6,zoR(d)-2.3)],dB1,dC1,['glassd','roofu'])
for z in(4.0,8.0,12.0,16.0):box(dB1,dC1,lambda d:rw(d),lambda d:rw(d)+0.5,z-0.3,z+0.3,'slab')
