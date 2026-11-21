exec(open('rc.py').read().split('for px')[0])
import math
for fr,pts in [(151,[(700,515),(700,545),(765,545),(570,520),(875,488),(855,305)]),(121,[(430,512),(490,540),(285,410),(380,462),(960,390),(1000,455),(400,425)]),(181,[(360,485),(385,485),(385,520),(570,522),(1000,375)]),(211,[(960,510),(270,385),(260,408),(335,450),(175,225)])]:
    a=math.radians(90+(fr-1)*1.5); cam=(520*math.cos(a),520*math.sin(a),190)
    for px,py in pts: print(fr,px,py,shoot(cam,(0,0,10),60,1280,720,px,py))
import json
B=[o for o in bpy.data.objects if 'bridge' in o.name]
for o in B: print('BR', o.name, [round(v,1) for v in o.dimensions], len(o.data.polygons))
