# Heritage stands as clean buildings. Plan read off the Esri z20 satellite straightened into each frame (sat/rect.py ->
# sat/rL.png, sat/rM.png) and the OSM outlines 195513198 (Ladies') / 195513202 (Members'): u along the boundary, w away
# from the field, metres; w=0 is the roof's field edge. Heights and looks from the field photo refs5/SCG-ladies-members-stands.jpg.
# (name, frame, u0,u1, w0,w1, eave z, ridge rise, roof kind)
import math,numpy as _np
FR={'M':((-68.5,45.3),35.0),'L':((-86.7,5.8),65.0)}
def fr_xy(f,u,w):
    (ox,oy),a=FR[f];a=math.radians(a);U=(math.cos(a),math.sin(a));Wd=(-U[1],U[0])
    return (ox+u*U[0]+w*Wd[0],oy+u*U[1]+w*Wd[1])
BLD=[
 # Ladies' Stand: one big hipped roof over the two-tier stand (cupola mid-ridge); two small gables on the back slope,
 # the round tower behind it, a low range at the north back corner
 ('L1','L',-3,42,0,18.5,13.5,5.0,'hip_u'),
 ('L4','L',5,12,12.5,21,12.0,3.0,'gable_w'),
 ('L5','L',25,30.5,13.5,22,12.0,3.0,'gable_w'),
 ('L3','L',31,41,18,25,11.0,3.0,'gable_u'),
 # Members Pavilion: left range, central block (pediment to the field, clock tower), right range, north end, back ranges
 # eaves back-projected from the field photo (heritage camera): left 10.5, central block 11.5, right 10.6, wing 10.65/13.75
 ('M1','M',-4,8,0,19,12.1,3.5,'hip_u'),
 ('M2','M',8,30.5,0,18,12.25,3.5,'hip_u'),   # front range: ridge parallel to the field (photo: level ridge line between the turrets)
 ('M3','M',30.5,43.5,0,18,11.5,4.0,'hip_u'),
 ('M4','M',43,47.5,0,16,10.65,3.1,'gable_w'),
 ('M5','M',-5,15,26,34,12.5,4.0,'gable_u'),
 ('M5b','M',6,15,18,26.5,11.5,3.0,'hip_u'),
 ('M5c','M',-5,0,18,26.5,12.0,2.5,'gable_w'),
 ('M6','M',15,33,18,35,11.5,4.0,'hip_u'),
 ('M7','M',33,46,17,28,11.0,3.0,'gable_u'),
]
GABLETS=[]   # field photo: no small gables on the Members' front slope
TURRETS=[('M1',1.2,2.5),('M2',11.7),('M2',26.6),('M3',37.8)]   # (block, u[, w]); left one lower, near the eave (photo x 580)   # crested roof ventilators (field photo u 11.7, 26.6, 37.8; top ~15.4)
ARCH=('M2',16.2,22.6,13.4)   # arched fanlight pediment on the central block's cornice: u range, crown height
ROT=('L',19.5,18.8,10.4)      # round tower: centre u,w and radius from the OSM curve (fit to 9 nodes, +-0.6 m)
CUP=('L',19.5,9.25)           # Ladies' cupola on the middle of the ridge (photo: 0.53 along the stand)
CLK=('M',18.85,8.0)           # Members' clock tower on the central block (photo: 0.42 along the pavilion)
