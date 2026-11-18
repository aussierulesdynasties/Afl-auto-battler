import bpy,numpy as np
from scipy.spatial import ConvexHull
from matplotlib.path import Path
H={}
for n in ('huggins_stand','ian_drake_pavilion','club_sawtooth','club_whiteblock','grandstand','scoreboard'):
    o=bpy.data.objects[n];v=np.array([(o.matrix_world@x.co)[:] for x in o.data.vertices]);h=ConvexHull(v[:,:2]);H[n]=Path(v[h.vertices,:2])
for n in ('crest_posts','billboards','crest_wire'):
    o=bpy.data.objects[n];v=np.array([(o.matrix_world@x.co)[:] for x in o.data.vertices])
    for k,p in H.items():
        m=p.contains_points(v[:,:2])
        if m.any():print(n,'inside',k,m.sum(),np.round(v[m][:3],1).tolist())
