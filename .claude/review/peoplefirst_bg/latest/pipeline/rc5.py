exec(open('rc.py').read().split('for px')[0])
import math
for fr,pts in [(1,[(800,420),(885,385),(850,395),(805,430),(430,350)])]:
    a=math.radians(90+(fr-1)*1.5); cam=(520*math.cos(a),520*math.sin(a),190)
    for px,py in pts: print(fr,px,py,shoot(cam,(0,0,10),60,1280,720,px,py))
