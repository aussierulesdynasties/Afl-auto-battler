import json,math,numpy as np,sys
src=open('build3.py',encoding='utf-8').read()
start=src.index("C=O['colors']");end=src.index("_bp=np.array")
O=json.load(open('build.json'))
exec(src[start:end])
for deg in range(-180,180,15):
    a=math.radians(deg);print(deg,'stand' if in_stand(a) else 'bank',round(d_out(a),1),tuple(round(v) for v in pt(a,0)[:2]))
