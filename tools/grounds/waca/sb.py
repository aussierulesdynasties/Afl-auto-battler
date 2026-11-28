# Scoreboard (east end) and the two billboards beyond the SE corner, read off p92.png (u 887-1248, v 445-515).
# Scoreboard face plane: behind the east terrace, facing west across the ground (1954 board, still standing, never moved).
# Position (28 Nov 2026): 2000-2008 Google Earth aerials, checked against a GE 3D height grid (15-20 m long, ~15 m top).
# Placed on the 2008 aerial (same frame as the model's fence): roof x 120-125, y -11..-31, west face x ~120.
# Board 2.8 m lower than first built: at this spot the 1992 photo's board edges need it, and GE gives a ~15 m top.
SL=(0.05,0.999);SN=(-0.999,0.05);SC=(120.3,-21.0);DZ=-2.8     # SN faces the ground (west); s runs north
def SBP(s,d,z):return (SC[0]+SL[0]*s+SN[0]*d,SC[1]+SL[1]*s+SN[1]*d,z+DZ if z>0 else z)
def sq(m,pts):quad(m,[SBP(*p) for p in pts])
def sbox(m,s0,s1,d0,d1,z0,z1,top=None):boxpts(m,[SBP(s0,d0,0)[:2],SBP(s1,d0,0)[:2],SBP(s1,d1,0)[:2],SBP(s0,d1,0)[:2]],z0+DZ if z0>0 else z0,z1+DZ,top)
sbox('board',-7.6,7.6,-2.0,0.0,10.8,17.1)                 # black face box
sbox('white',7.6,8.6,-2.0,0.05,10.8,16.5);sbox('white',-8.1,-7.6,-2.0,0.05,10.8,16.5)   # white end pillars
sbox('crownred',-8.1,8.6,-2.0,0.0,16.5,19.1)               # crown band body
for s,(o) in ((-3.5,0),(3.5,0)):sbox('concrete',s-0.5,s+0.5,-1.5,-0.5,0,10.8)            # legs
# arched yellow pediment over the crown (ends 19.1, peak 20.2 at s -0.5)
ARC=[(s,19.1+1.1*max(0,1-((s+0.5)/8.6)**2)) for s in [8.6-k*16.7/16 for k in range(17)]]
sq('yellow',[(8.6,0.06,19.1)]+[(s,0.06,z) for s,z in ARC]+[(-8.1,0.06,19.1)])
for (s0,z0),(s1,z1) in zip(ARC,ARC[1:]):sq('yellow',[(s0,0.06,z0),(s1,0.06,z1),(s1,-2.0,z1),(s0,-2.0,z0)])
# hand-drawn faces, explicit UVs, read left to right in the photo (s decreasing)
F0=SBP(7.6,0.08,10.8);quad('sbface',[F0,SBP(-7.6,0.08,10.8),SBP(-7.6,0.08,17.1),(F0[0],F0[1],17.1+DZ)])   # 8 cm proud of the box: 3 cm z-fought
SIGNS['sbface']=(F0,(-SL[0],-SL[1]),15.2,10.8+DZ,6.3)
C0=SBP(8.6,0.09,16.5);quad('sbcrown',[C0,SBP(-8.1,0.09,16.5),SBP(-8.1,0.09,19.1),(C0[0],C0[1],19.1+DZ)])
SIGNS['sbcrown']=(C0,(-SL[0],-SL[1]),16.7,16.5+DZ,2.6)
