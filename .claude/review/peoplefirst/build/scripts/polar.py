import cv2,numpy as np,json
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
S=json.load(open('sat.json'));m=S['mpp']
mk=cv2.imread('roof_mask.png',0)>0
N=1440;rs=np.arange(40,160,0.1)
out=[]
for i in range(N):
    a=2*np.pi*i/N;x=rs*np.cos(a);y=rs*np.sin(a)
    u=(S['px']+x/m).astype(int);v=(S['py']-y/m).astype(int);on=mk[v,u]
    if on.sum()<20:out.append((np.nan,np.nan,0));continue
    idx=np.where(on)[0];out.append((rs[idx[0]],rs[idx[-1]],on.sum()*0.1))
P=np.array(out);np.save('polar.npy',P)
ang=np.arange(N)/N*360
plt.figure(figsize=(16,6));plt.plot(ang,P[:,0],'.',ms=2,label='in');plt.plot(ang,P[:,1],'.',ms=2,label='out');plt.plot(ang,P[:,2],'.',ms=2,label='width')
plt.xticks(range(0,361,15));plt.grid();plt.legend();plt.savefig('polar.png',dpi=70)
