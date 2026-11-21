import numpy as np, math
def setup(f):
    # re-derive yaw from VP_A for this f
    off=math.atan((400+9)/f); pit=math.atan((361-300)/f)
    yaw=math.atan2(-0.955,-0.296)-off
    fw=np.array([math.cos(pit)*math.cos(yaw),math.cos(pit)*math.sin(yaw),math.sin(pit)]); rt=np.cross(fw,[0,0,1]); rt/=np.linalg.norm(rt); up=np.cross(rt,fw)
    ray=lambda u,v: fw+rt*(u-400)/f+up*(300-v)/f
    def hit(u,v,h=0.0): d=ray(u,v); return d*((h-1.6)/d[2])
    def height(ub,vb,ut,vt,hb=0.0):
        B=hit(ub,vb,hb); d=ray(ut,vt); return 1.6+d[2]*np.linalg.norm(B[:2])/np.linalg.norm(d[:2])
    return fw,hit,height,yaw,pit
for f in (582,700,800,900,1000,1200):
    fw,hit,height,yaw,pit=setup(f)
    print(f,'bollard',round(height(471,455,471,425,0.15),2),'M post',round(height(327,440,312,302),2),'R post',round(height(457,452,437,180),2),'L',round(height(232,430,210,245),2))
