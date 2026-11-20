# join audit cameras: python joins.py TAG  -> shotsJ<TAG>.json (out joins/<TAG>_<name>.png)
import json,math,sys
A0,B0=72.5,88.5
def ring(t,d,z):r=math.radians(t);return ((A0+d)*math.cos(r),(B0+d)*math.sin(r),z)
def shot(name,eye,tgt,f=900,W=1200,H=750):
    v=[tgt[i]-eye[i] for i in range(3)];h=math.hypot(v[0],v[1])
    return dict(p=[*eye,math.atan2(v[1],v[0]),math.atan2(v[2],h),0.0,f,W/2,H/2],W=W,H=H,out=f'joins/{sys.argv[1]}_{name}.png')
tag=sys.argv[1];S=[]
# inside views of seats + walkway (aisle lines across rows and sector changes)
for t in ([0,38,40,90,140,200,250,280,318] if tag=='B' else [0,38,40,90,140,200,250,300,318]):
    S.append(shot(f'in{t:03d}',ring(t,-22,9),ring(t,18,8)))
# outside/top views of roof ends and section edges
ends={'B':[35,45,135,148,236,244,257,306,322],'A':[35,45,135,148,317,318]}[tag]
for t in ends:
    S.append(shot(f'roof{t:03d}',ring(t,-15,45),ring(t,30,14)))
    S.append(shot(f'out{t:03d}',ring(t,75,22),ring(t,30,10)))
json.dump(dict(shots=S),open(f'shotsJ{tag}.json','w'));print(len(S))
