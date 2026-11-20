import math,numpy as np,json
exec(open('nearsolve.py').read().split('# model')[0])
G=json.load(open('geo_n.json'));RG=G['RG']
def wallang(x,dr=25):
    best=None
    for a in np.arange(120,250,0.02):
        t=math.radians(a);r=lerp(RG,a)+dr;q=proj([(r*math.cos(t),r*math.sin(t),15.0)])[0]
        if best is None or abs(q[0]-x)<best[0]:best=(abs(q[0]-x),a)
    return best[1]
def ywall(a,z,dr=25):
    t=math.radians(a);r=lerp(RG,a)+dr;return proj([(r*math.cos(t),r*math.sin(t),z)])[0][1]
if __name__=='__main__':
    for x in (760,780,800,820,840,880,920):
        a=wallang(x);print(x,'angle %.1f'%a,{z:round(ywall(a,z),1) for z in (10.6,12,14,16,18,20,21)})
