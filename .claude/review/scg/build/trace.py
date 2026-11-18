exec(open('meas.py').read())
from PIL import Image,ImageDraw
from scipy import ndimage as nd
hsv=np.array(Image.open('refs/scg.jpg').convert('HSV')).astype(int)
white=(hsv[...,1]<50)&(hsv[...,2]>160);white=nd.binary_opening(white,iterations=1)
c0=pr([(*PC,0)])[0];print('centre px',c0)
ROOFS=['195513203','195513197','195513200','659304331','659304332']
RP={k:polar(G[k]) for k in ROOFS}
GP=polar(G['4000006'])
def rmin_any(a):
    i=int(round((a%(2*math.pi))/(2*math.pi)*720))%720;v=[RP[k][i] for k in ROOFS if not np.isnan(RP[k][i][0])]
    return (min(x[0] for x in v),max(x[1] for x in v)) if v else (np.nan,np.nan)
def solve_z(u,v,which):
    best=None
    for z in np.arange(0,70,0.25):
        X=at_z(u,v,z);a=theta(X);lo,hi=rmin_any(a)
        if np.isnan(lo):continue
        e=rr(X)-(lo if which==0 else hi)
        if best is None or abs(e)<abs(best[0]):best=(e,z,a,rr(X))
    return best
out=[];im=Image.open('refs/scg.jpg').convert('RGB');d=ImageDraw.Draw(im)
for ad in np.arange(0,360,0.5):
    a=math.radians(ad);run=[];r=60
    while True:
        x=int(c0[0]+math.cos(a)*r);y=int(c0[1]+math.sin(a)*r)
        if not(0<=x<1200 and 0<=y<675):break
        run.append((white[y,x],x,y));r+=1
    ws=[i for i,(w,_,_) in enumerate(run) if w]
    if not ws:continue
    i0=ws[0];i1=i0
    while i1+1<len(run) and (run[i1+1][0] or any(run[j][0] for j in range(i1+2,min(i1+6,len(run))))):i1+=1
    f=run[i0][1:];o=run[i1][1:]
    bf=solve_z(*f,0);bo=solve_z(*o,1)
    out.append((ad,f,o,bf,bo));d.ellipse([f[0]-2,f[1]-2,f[0]+2,f[1]+2],fill=(255,0,0));d.ellipse([o[0]-2,o[1]-2,o[0]+2,o[1]+2],fill=(0,0,255))
    if 0:print(ad,f,o,'front z %.1f err %.1f th %d r %.0f'%(bf[1],bf[0],math.degrees(bf[2]),bf[3]),'| outer z %.1f err %.1f th %d r %.0f'%(bo[1],bo[0],math.degrees(bo[2]),bo[3]))
im.save('g/trace.png')
import pickle
rec=[]
for ad,f,o,bf,bo in out:
    if bf:rec.append(('f',math.degrees(bf[2]),bf[1],bf[0],bf[3]))
    if bo:rec.append(('o',math.degrees(bo[2]),bo[1],bo[0],bo[3]))
json.dump(rec,open('trace.json','w'))
RNG={'195513203':(42,107),'195513197':(-32,22),'195513200':(-100,-30),'659304331':(-138,-100),'659304332':(169,224)}
for k,(a0,a1) in RNG.items():
    for w in 'fo':
        pts=sorted([(t if t>a0-5 or a1<180 else t+360,z) for s,t,z,e,r in rec if s==w and abs(e)<0.6 and a0<=(t if t>0 or a1<180 else t+360)<=a1])
        if not pts:print(k,w,'none');continue
        A=np.array(pts);bins=np.arange(a0,a1+1,5);row=[]
        for b in bins:
            m=(A[:,0]>=b-2.5)&(A[:,0]<b+2.5)
            row.append('%d:%s'%(b,'%.1f'%np.median(A[m,1]) if m.sum() else '-'))
        print(k,w,' '.join(row))
json.dump([(float(ad),list(map(int,f)),list(map(int,o))) for ad,f,o,bf,bo in out],open('tracepx.json','w'))
