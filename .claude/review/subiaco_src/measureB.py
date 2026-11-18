# Subiaco 1997 (photo B, refs/c/17.jpg): every line read off the gridded zooms gB_*.png, back-projected through camB.
# New stands: seats raked 0.5 (z = 1 + 0.5 d); roofs ride dz above that rake. West end: bare pad, grass bank, ad boards.
import json
from subB import *
def R(pts,s=0.5,dz=0.0):return [list(map(float,pol_rake(u,v,s,0.5,dz))) for u,v in pts]
def Z(pts,z):return [[float(a),float(d),float(z)] for a,d,_ in (pol(u,v,z) for u,v in pts)]
J=json.load(open('layoutB.json'))
J['W1']=Z([(205,200),(250,180),(300,168),(350,160),(400,158),(450,160),(500,163),(540,168),(565,176)],0.3)
J['W2']=Z([(215,170),(250,152),(300,140),(350,135),(400,133),(450,135),(500,140),(540,145),(565,150)],3.0)
# blue-seat north stand: roof front (seat back) and roof back lines
J['BF']=R([(600,165),(670,195),(720,225),(775,260),(820,300),(845,335)],dz=4.5)
J['BB']=R([(605,140),(690,182),(740,207),(795,245),(840,285),(860,320)],dz=4.5)
# near-right concrete stand with the dark roof (incl. the grey corner roof)
J['NF']=R([(850,325),(852,365),(855,400),(830,415),(785,430),(720,445),(670,457)],dz=5.0)
J['NB']=R([(910,330),(912,400),(880,450),(790,475),(690,495)],dz=5.0)
# south + near bowl roof: front edge is the grass edge; back edge the roof's outer line
J['SF']=R([(210,250),(240,300),(265,390),(300,405),(340,425),(415,455),(490,472),(565,480),(640,482),(668,482)],dz=5.0)
J['SB']=R([(147,265),(175,330),(230,400),(315,455),(390,490),(465,505),(540,517),(615,522),(690,525)],dz=5.0)
J['LW']=Z([(165,210),(205,205),(212,262),(170,268)],8.0)       # small white building, south-west
J['FAC']=Z([(690,555),(790,530),(880,495)],0.0)                  # near-right stand facade foot
for k in('W1','W2','BF','BB','NF','NB','SF','SB','LW','FAC'):print(k,[(round(a,1),round(d,1),round(z,1)) for a,d,z in J[k]])
json.dump(J,open('layoutB.json','w',newline=''))
