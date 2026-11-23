import json,math,numpy as np
s=json.load(open('out/accor/job_video.json'))
def find(x):
    if isinstance(x,dict):
        if 'video' in x: return x['video']
        for v in x.values():
            r=find(v)
            if r: return r
    if isinstance(x,list):
        for v in x:
            r=find(v)
            if r: return r
o=find(s); print({k:o[k] for k in o if k!='x'})
L=np.array(o['look'],float); n=o.get('frames',96); fh=math.radians(o.get('fov_h',50)); res=o.get('res',[1280,720])
for name,P in (('station',(561,59,15)),('dome',(434,148,20)),('arena',(-134,304,20))):
  vis=[]
  for i in range(n):
    a=math.radians(o.get('start_deg',0))+2*math.pi*i/n
    C=np.array([L[0]+o['r']*math.cos(a),L[1]+o['r']*math.sin(a),o['z']])
    f=L-C; f/=np.linalg.norm(f); r=np.cross(f,[0,0,1]); r/=np.linalg.norm(r); u=np.cross(r,f)
    d=np.array(P)-C; z=d@f
    if z<=0: continue
    x=(d@r)/z/math.tan(fh/2); y=(d@u)/z/math.tan(fh/2)*res[0]/res[1]
    if abs(x)<1 and abs(y)<1: vis.append(i)
  print(name,len(vis),'of',n,vis[:5],vis[-3:])
for i in (30,60,90):
    a=math.radians(90)+2*math.pi*i/n
    C=np.array([L[0]+o['r']*math.cos(a),L[1]+o['r']*math.sin(a),o['z']])
    f=L-C; f/=np.linalg.norm(f); r=np.cross(f,[0,0,1]); r/=np.linalg.norm(r); u=np.cross(r,f)
    d=np.array((561,59,15))-C; z=d@f; x=(d@r)/z/math.tan(fh/2); y=(d@u)/z/math.tan(fh/2)*16/9
    print(i,'px',round(640+640*x),round(360-360*y),'dist',round(z))
