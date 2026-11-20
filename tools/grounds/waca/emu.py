# EMU Club (NW stand), street face toward the 1992 camera. exec'd by build.py after north.py/south.py.
# Frame: EO at the west end of the street face (photo u 1993), EU along it eastward (to u 1286), EN into the stand.
# Heights back-projected from p92.png onto the street plane; deck far edge, lattice nodes via at_z (cam.py).
EO=(-108.16,53.93);EU2=(0.7365,0.6764);EN=(0.6764,-0.7365);EL=69.3
def EP(a,d,z):return (EO[0]+EU2[0]*a+EN[0]*d,EO[1]+EU2[1]*a+EN[1]*d,z)
def eq(m,pts):quad(m,[EP(*p) for p in pts])
def ebox(m,a0,a1,d0,d1,z0,z1,top=None):
    boxpts(m,[EP(a0,d0,0)[:2],EP(a1,d0,0)[:2],EP(a1,d1,0)[:2],EP(a0,d1,0)[:2]],z0,z1,top)
def bar(m,p,q,w=0.35,h=0.35):
    # square steel member from p to q (a,d,z), lying on the deck
    P0,P1=EP(*p),EP(*q);dx,dy=P1[0]-P0[0],P1[1]-P0[1];L=math.hypot(dx,dy) or 1;sx,sy=-dy/L*w/2,dx/L*w/2
    c=[(P0[0]+sx,P0[1]+sy,P0[2]),(P1[0]+sx,P1[1]+sy,P1[2]),(P1[0]-sx,P1[1]-sy,P1[2]),(P0[0]-sx,P0[1]-sy,P0[2])]
    t=[(x,y,z+h) for x,y,z in c]
    quad(m,t);quad(m,[c[0],c[1],t[1],t[0]]);quad(m,[c[2],c[3],t[3],t[2]])
POSTS=[0.8,13.1,26.9,41.1,54.3,68.0];CEN=[7.0,20.2,33.9,47.7,61.3]
ZF,ZB,DR=13.4,13.8,21.0          # deck: front eave z, far edge z, far edge depth
def zdeck(d):return ZF+(ZB-ZF)*max(0,d)/DR
# roof deck, underside, fascia
eq('emuroof',[(0,-0.6,ZF),(EL,-0.6,ZF),(EL,DR,ZB),(0,DR,ZB)])
eq('loft',[(0,-0.6,ZF-0.5),(EL,-0.6,ZF-0.5),(EL,DR,ZB-0.5),(0,DR,ZB-0.5)])
eq('emufascia',[(0,-0.6,ZF-0.5),(EL,-0.6,ZF-0.5),(EL,-0.6,ZF),(0,-0.6,ZF)])
eq('emufascia',[(0,DR,ZB-0.5),(EL,DR,ZB-0.5),(EL,DR,ZB),(0,DR,ZB)])
for a in (0,EL):eq('emufascia',[(a,-0.6,ZF-0.5),(a,DR,ZB-0.5),(a,DR,ZB),(a,-0.6,ZF)])
# steel lattice on the deck: per bay a diamond front-centre (d 3.2) -> post (d 9.7) -> back-centre (d 21) -> post
for i,c in enumerate(CEN):
    f=(c,3.2,zdeck(3.2));b=(c,DR-0.3,zdeck(DR-0.3))
    for pa in (POSTS[i],POSTS[i+1]):
        m=(pa,9.7,zdeck(9.7));bar('emutruss',f,m);bar('emutruss',m,b)
# street face bands (z from the photo: soffit 12.2-12.9, white band 10.2-12.2, deck 6.0-10.2, ledge 5.5-6.0,
# brick 2.0-5.5, shadow line 1.0-2.0, ground floor 0-1.0)
eq('dark',[(0,1.5,12.2),(EL,1.5,12.2),(EL,1.5,ZF-0.5),(0,1.5,ZF-0.5)])
eq('emuband',[(0,0,10.2),(EL,0,10.2),(EL,0,12.2),(0,0,12.2)])
eq('emuband',[(0,0,12.2),(EL,0,12.2),(EL,1.5,12.2),(0,1.5,12.2)])
eq('emuband',[(0,0,10.2),(EL,0,10.2),(EL,2.5,10.2),(0,2.5,10.2)])
for i in range(5):                     # K-braces in the white band
    a0,a1=POSTS[i],POSTS[i+1]
    for pa,pb in ((a0,a0+3.2),(a1,a1-3.2)):
        A=EP(pa,-0.05,12.1);B=EP(pb,-0.05,10.3);dx,dy=B[0]-A[0],B[1]-A[1]
        quad('dark',[(A[0],A[1],A[2]+0.12),(B[0],B[1],B[2]+0.12),(B[0],B[1],B[2]-0.12),(A[0],A[1],A[2]-0.12)])
eq('dark',[(0,2.5,6.0),(EL,2.5,6.0),(EL,2.5,10.2),(0,2.5,10.2)])        # open viewing deck behind glass
for a in POSTS:ebox('dark',a-0.18,a+0.18,0.1,0.46,6.0,ZF-0.5)          # bay posts
for a0,a1 in ((58.2,61.6),(24.4,29.3),(6.7,8.9)):                       # yellow chairs on the deck
    k=a0
    while k<a1-0.4:ebox('chair',k,k+0.45,1.0,1.5,6.0,6.9);k+=0.6
ebox('ledge',0,EL,-0.4,2.5,5.5,6.0)
eq('emubrick',[(0,0,2.0),(EL,0,2.0),(EL,0,5.5),(0,0,5.5)])
eq('dark',[(0,1.2,1.0),(EL,1.2,1.0),(EL,1.2,2.0),(0,1.2,2.0)])
eq('emubrick',[(0,0,2.0),(EL,0,2.0),(EL,1.2,2.0),(0,1.2,2.0)])
eq('gf',[(0,0,0),(EL,0,0),(EL,0,1.0),(0,0,1.0)])
ebox('emubrick',34.2,36.7,-1.0,0.2,0,14.2)                              # brick pier through the roof line
# EMU CLUB sign (hand-drawn texture, explicit UVs): a 34.3 -> 15.6 (photo u 1645-1835), z 10.5-12.6, just proud of the band
SG0=EP(34.3,-0.15,10.5);SG1=EP(15.6,-0.15,10.5)
quad('emusign',[(SG0[0],SG0[1],10.5),(SG1[0],SG1[1],10.5),(SG1[0],SG1[1],12.6),(SG0[0],SG0[1],12.6)])
SIGNS['emusign']=(SG0,(-EU2[0],-EU2[1]),18.7,10.5,2.1)
# end walls to the fence (field side hidden in the photo; seating stays the sector terrace)
def efence(a):
    d=10.0
    while d<60:
        x,y,_=EP(a,d,0)
        if math.hypot(x-EC[0],y-EC[1])<=frad(tof(x,y))+1.5:return d
        d+=0.25
    return d
for a in (0,EL):
    fd=efence(a);dt=0.35*fd;zt=8.0-(DR-dt)/(fd-dt)*7.2     # terrace: z 8 at s 0.65 down to 0.8 at the fence
    eq('emubrick',[(a,0,0),(a,0,ZF-0.5),(a,DR,ZB-0.5),(a,DR,zt),(a,fd,0.8),(a,fd,0)])
