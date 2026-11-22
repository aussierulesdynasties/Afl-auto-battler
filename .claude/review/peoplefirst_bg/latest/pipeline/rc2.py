exec(open('rc.py').read().split('for px')[0])
import math
a=math.radians(90); cam=(520*math.cos(a),520*math.sin(a),190)
for nm,px,py in [('slab',380,322),('slab2',575,345),('stand',890,365),('cross',1040,440),('L',600,560),('shed',1220,510),('park',900,520),('wedge',860,330)]:
    print(nm,shoot(cam,(0,0,10),60,1280,720,px,py))
