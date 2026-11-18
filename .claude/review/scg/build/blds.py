# Heritage stands as clean rectangular buildings, read off the straightened plans g/rp_mem.png and g/rp_lad.png
# (u along the boundary, w away from the field, metres) and the field-side photo refs5/SCG-ladies-members-stands.jpg.
# (frame, u0,u1, w0,w1, eave z, ridge rise, roof kind, front elevation material)
import math,numpy as _np
FR={'M':((-68.5,45.3),35.0),'L':((-86.7,5.8),65.0)}
def fr_xy(f,u,w):
    (ox,oy),a=FR[f];a=math.radians(a);U=(math.cos(a),math.sin(a));Wd=(-U[1],U[0])
    return (ox+u*U[0]+w*Wd[0],oy+u*U[1]+w*Wd[1])
BLD=[
 # Ladies' Stand: one big hipped roof over the two-tier stand (cupola on the ridge), lower ranges behind it either side
 # of the domed round tower
 ('L1','L',4,52,10,29,13.5,5.0,'hip_u'),
 ('L2','L',3,19,28,37,12.0,3.0,'gable_u'),
 ('L3','L',30,42,28,34,12.0,3.0,'gable_u'),
 # Members Pavilion: left range (gable end against the Ladies'), central block whose pediment faces the field under the
 # clock tower, right range with small field gables, brick end gable, rear wings
 ('M1','M',-4,15,10,29,13.0,4.5,'gable_u'),
 ('M2','M',14,24.5,10,37,14.0,4.0,'gable_w'),
 ('M3','M',24,48,10,28,13.0,4.0,'gable_u'),
 ('M4','M',45,53,10,26,13.0,4.0,'gable_w'),
 ('M5','M',-5,15,36,44,12.5,4.0,'gable_u'),   # back range; the light court below it (u 0-6, w 29-36) is open
 ('M5b','M',6,15,28,36.5,12.5,3.5,'gable_w'),
 ('M5c','M',-5,0,28,36.5,12.0,2.5,'gable_w'),
 ('M6','M',15,34,28,45.5,12.5,4.0,'gable_w'),
 ('M7','M',33,48.5,27,37,11.0,3.0,'gable_u'),
 ('M8','M',-10,-4,24,40,11.0,3.0,'gable_w'),
]
GABLETS=[('M1',1.5),('M1',10.5),('M3',28.0),('M3',40.0)]   # small field gables with finials (field photo)
