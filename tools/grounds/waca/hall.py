# Halls east of the north stand (1992 photo u 520-700, v 530-690; order checked on the 1987 aerial).
# Heights solved from the photo: hall B eave 12 m (front wall base hidden at v 733), hall A eave 14 m.
def lin(c):return tuple((v/255)**2.2 for v in c)
C.update({'hallbrick':lin((118,40,28)),'ebrick':lin((196,70,30)),'hallroofA':lin((174,191,214)),'hallroofB':lin((226,236,248)),
          'hallfascia':lin((91,79,103)),'hallwin':lin((60,85,130)),'croof':lin((198,167,135)),'droof':lin((224,85,22)),'eroof':lin((218,203,225))})
# ---- hall A: flat roof, blue fascia, red brick; north face carries two wall air conditioners
A=[(73.8,97.0),(49.4,102.9),(59.3,77.6),(83.7,71.7)]
boxpts('hallbrick',A,0,13.5,top='hallroofA')
for (x0,y0),(x1,y1) in zip(A,A[1:]+A[:1]):quad('hallfascia',[(x0,y0,13.5),(x1,y1,13.5),(x1,y1,14.0),(x0,y0,14.0)])
quad('hallroofA',[(x,y,14.0) for x,y in A])
FA=(-0.972,0.235);NA_=(0.235,0.972)          # along A's north face, outward normal
def fa(a,z,o=0):return (73.8+FA[0]*a+NA_[0]*o,97.0+FA[1]*a+NA_[1]*o,z)
for a0,a1,z0,z1 in ((3.0,7.3,7.4,9.1),(9.7,13.9,7.5,9.5)):
    for o0,o1 in ((0,0.9),):
        c=[fa(a0,0,o0)[:2],fa(a1,0,o0)[:2],fa(a1,0,o1)[:2],fa(a0,0,o1)[:2]];boxpts('aisle',c,z0,z1)
# ---- hall B: mono-pitch pale roof, eave 12 m at the street, 15 m at the back, 13 m deep
BL,BR=(53.9,106.8),(10.6,114.9);S=(-0.185,-0.983);D=13.0
BLb=(BL[0]+S[0]*D,BL[1]+S[1]*D);BRb=(BR[0]+S[0]*D,BR[1]+S[1]*D)
quad('hallbrick',[(*BL,0),(*BR,0),(*BR,12),(*BL,12)]);quad('hallbrick',[(*BLb,0),(*BRb,0),(*BRb,15),(*BLb,15)])
quad('hallbrick',[(*BL,0),(*BLb,0),(*BLb,15),(*BL,12)]);quad('hallbrick',[(*BR,0),(*BRb,0),(*BRb,15),(*BR,12)])
quad('hallroofB',[(*BL,12),(*BR,12),(*BRb,15),(*BLb,15)])
EB=((BR[0]-BL[0])/44.05,(BR[1]-BL[1])/44.05);NB=(-S[0],-S[1])
def fb(a,z,o=0.05):return (BL[0]+EB[0]*a+NB[0]*o,BL[1]+EB[1]*a+NB[1]*o,z)
for z0,z1,m in ((9.4,9.9,'blue'),(8.6,9.4,'hallwin'),(8.2,8.6,'blue'),(11.6,12.0,'dark')):
    quad(m,[fb(0,z0),fb(44.05,z0),fb(44.05,z1),fb(0,z1)])
for k in range(15):
    a=1.5+k*3.0;quad('blue',[fb(a,8.6,0.08),fb(a+0.25,8.6,0.08),fb(a+0.25,9.4,0.08),fb(a,9.4,0.08)])
quad('aisle',[fb(33.5,4.0,0.2),fb(33.8,4.0,0.2),fb(33.8,9.4,0.2),fb(33.5,9.4,0.2)])   # downpipe (photo u 651)
# ---- low buildings in front of B (photo u 525-690, v 650-730), each solved from its visible edges:
# C: wedge against B's wall, roof deck 6.3 m (orange), cream canopy along its street edge 6.0 -> 4.9 m, white fascia
P1,P2=(48.6,115.2),(31.1,111.2);P3=(48.6,BL[1]+(BL[0]-48.6)*(-EB[1]/EB[0]))
boxpts('white',[P1,P2,P3],0,6.0,top='droof')
F=(0.204,1.082)
quad('croof',[(*P1,6.0),(*P2,6.0),(P2[0]+F[0],P2[1]+F[1],4.9),(P1[0]+F[0],P1[1]+F[1],4.9)])
quad('white',[(P1[0]+F[0],P1[1]+F[1],4.0),(P2[0]+F[0],P2[1]+F[1],4.0),(P2[0]+F[0],P2[1]+F[1],4.9),(P1[0]+F[0],P1[1]+F[1],4.9)])
# E: shallow orange brick block on B's wall, 7.8 m, pale roof
def bf(x):return (x,BL[1]+(BL[0]-x)*(-EB[1]/EB[0]))
boxpts('ebrick',[(29.5,112.4),(20.0,114.2),bf(20.0),bf(29.5)],0,7.8,top='eroof')
# G: small white gable house at street level (photo apex v 690, eave v 704, base v 728)
g0,g1=(30.2,116.8),(26.3,113.2);GD=(0.68,-0.735);gd=3.0
def gp(p,t,z):return (p[0]+GD[0]*t,p[1]+GD[1]*t,z)
gm=((g0[0]+g1[0])/2,(g0[1]+g1[1])/2)
for t in (0,gd):quad('white',[gp(g0,t,0),gp(g1,t,0),gp(g1,t,2.7),gp(gm,t,4.2),gp(g0,t,2.7)])
quad('white',[gp(g0,0,0),gp(g0,gd,0),gp(g0,gd,2.7),gp(g0,0,2.7)]);quad('white',[gp(g1,0,0),gp(g1,gd,0),gp(g1,gd,2.7),gp(g1,0,2.7)])
quad('croof',[gp(g0,0,2.7),gp(g0,gd,2.7),gp(gm,gd,4.2),gp(gm,0,4.2)]);quad('croof',[gp(g1,0,2.7),gp(g1,gd,2.7),gp(gm,gd,4.2),gp(gm,0,4.2)])
