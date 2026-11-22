exec(open('rc.py').read().split('for px')[0])
import math
for fr,pts in [(91,[(560,470),(690,485),(650,505),(775,527),(960,350),(400,510),(350,488)]),(61,[(790,460),(860,432),(985,440),(665,540),(240,360)]),(31,[(870,395),(940,370),(280,470)])]:
    a=math.radians(90+(fr-1)*1.5); cam=(520*math.cos(a),520*math.sin(a),190)
    for px,py in pts: print(fr,px,py,shoot(cam,(0,0,10),60,1280,720,px,py))
