import json
from subC2 import *
R=lambda L:[[round(float(x),2) for x in p] for p in L]
# roof front edge pixels read off zC3_L / zC3_R / full photo, ring order west -> south -> east -> north-east
FRONT=[(225,262),(200,280),(170,300),(150,320),(140,350),(140,385),(170,402),(220,412),(300,432),(400,437),(500,432),(600,416),(680,396),(760,356),(820,310),(830,250),(805,215),(780,180),(700,163),(620,160),(540,158)]
for zf in (16,20,24):
    print('zf',zf,[tuple(round(x,1) for x in pol(u,v,zf)[:2]) for u,v in FRONT])
