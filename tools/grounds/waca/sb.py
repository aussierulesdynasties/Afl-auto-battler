# Scoreboard behind the east terrace (1954 board; first modelled from p92.png).
# Scoreboard face plane: behind the east terrace, facing west across the ground (1954 board, still standing, never moved).
# Position (28 Nov 2026): 2000-2008 Google Earth aerials, checked against a GE 3D height grid (15-20 m long, ~15 m top).
# Placed where Google Earth 3D (no lean) and the May 2008 aerial agree: west face x 122-123 (north half) to
# 121.5-122 (south half), y -14..-33, north end turned ~6 deg east. Aerials of other dates lean the 15 m roof by
# up to 7 m, so a single one misleads. Board 2.8 m lower than first built: GE gives the block top ~14-15 m above the turf.
SL=(0.105,0.994);SN=(-0.994,0.105);SC=(122.0,-23.5);DZ=-2.8     # SN faces the ground (west); s runs north
# DZ drops every part that starts above ground (z>0) by 2.8 m; parts at z=0 (the legs' feet) stay on the ground.
# A new part with 0 < z < 2.8 would be pushed below ground: give such parts z=0 or handle them separately.
def SBP(s,d,z):return (SC[0]+SL[0]*s+SN[0]*d,SC[1]+SL[1]*s+SN[1]*d,z+DZ if z>0 else z)
def sq(m,pts):quad(m,[SBP(*p) for p in pts])
def sbox(m,s0,s1,d0,d1,z0,z1,top=None):boxpts(m,[SBP(s0,d0,0)[:2],SBP(s1,d0,0)[:2],SBP(s1,d1,0)[:2],SBP(s0,d1,0)[:2]],z0+DZ if z0>0 else z0,z1+DZ,top)
sbox('board',-7.6,7.6,-2.0,0.0,10.8,16.5)                 # black face box (stops under the crown: 17.1 z-fought its back)
quad('board',[SBP(s,d,10.8) for s,d in ((-7.6,0.0),(7.6,0.0),(7.6,-2.0),(-7.6,-2.0))])   # its underside (boxpts makes no bottoms), facing down
sbox('white',7.6,8.6,-2.0,0.05,10.8,16.5);sbox('white',-8.1,-7.6,-2.0,0.05,10.8,16.5)   # white end pillars
sbox('crownred',-8.1,8.6,-2.0,0.0,16.5,19.1)               # crown band body
for s,(o) in ((-3.5,0),(3.5,0)):sbox('concrete',s-0.5,s+0.5,-1.5,-0.5,0,10.8)            # legs
# arched yellow pediment over the crown (ends 19.1, peak 20.2 at s -0.5)
ARC=[(s,19.1+1.1*max(0,1-((s+0.5)/8.6)**2)) for s in [8.6-k*16.7/16 for k in range(17)]]
# Front at d 0.09, flush with the crown sign: at 0.06 it left a 3 cm slit above the sign that showed the red crown as crawling specks.
sq('yellow',[(-8.1,0.09,19.1)]+[(s,0.09,z) for s,z in reversed(ARC)])   # front, facing west (ARC[0] is already (8.6,19.1))
sq('yellow',[(s,-2.0,z) for s,z in ARC]+[(-8.1,-2.0,19.1)])               # back, facing east
for (s0,z0),(s1,z1) in zip(ARC,ARC[1:]):sq('yellow',[(s0,0.09,z0),(s1,0.09,z1),(s1,-2.0,z1),(s0,-2.0,z0)])   # top, facing up
sq('yellow',[(-8.1,-2.0,19.1),(-8.1,-2.0,ARC[-1][1]),(-8.1,0.09,ARC[-1][1]),(-8.1,0.09,19.1)])   # south end, 0.24 m tall, facing south (the north end meets the crown at 19.1)
# hand-drawn faces, explicit UVs, read left to right in the photo (s decreasing)
F0=SBP(7.6,0.08,10.8);quad('sbface',[F0,SBP(-7.6,0.08,10.8),SBP(-7.6,0.08,16.5),(F0[0],F0[1],16.5+DZ)])   # 8 cm proud of the box (3 cm z-fought); stops under the crown sign
SIGNS['sbface']=(F0,(-SL[0],-SL[1]),15.2,10.8+DZ,6.3)
C0=SBP(8.6,0.09,16.5);quad('sbcrown',[C0,SBP(-8.1,0.09,16.5),SBP(-8.1,0.09,19.1),(C0[0],C0[1],19.1+DZ)])
SIGNS['sbcrown']=(C0,(-SL[0],-SL[1]),16.7,16.5+DZ,2.6)
