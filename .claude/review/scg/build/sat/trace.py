# per-degree traces from the satellite (world grid): grass edge, white-roof inner/outer edge; and the model's own edges
import numpy as np,cv2,json,math
def polar(im,inter=cv2.INTER_NEAREST):
    N=im.shape[0];H=170.0;A=np.arange(0,360,0.5);Rr=np.arange(50,175,0.25);aa,rr=np.meshgrid(np.radians(A),Rr)
    mx=((rr*np.cos(aa)+H)/(2*H)*N-0.5).astype(np.float32);my=((H-rr*np.sin(aa))/(2*H)*N-0.5).astype(np.float32)
    return cv2.remap(im,mx,my,inter),Rr
sat=cv2.imread('sat/sat_world.png');hsv=cv2.cvtColor(sat,cv2.COLOR_BGR2HSV)
grass=((hsv[...,0]>30)&(hsv[...,0]<90)&(hsv[...,1]>50)&(hsv[...,2]>40)).astype(np.uint8)
white=((hsv[...,2]>185)&(hsv[...,1]<45)).astype(np.uint8)
white=cv2.morphologyEx(white,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
gp,Rr=polar(grass*255);wp,_=polar(white*255)
out={'grass':[],'win':[],'wout':[]}
for i in range(720):
    g=gp[:,i]>0;k=0
    while k<len(g) and (g[k] or k<40):k+=1   # first non-grass beyond r 60
    out['grass'].append(float(Rr[k]) if k<len(g) else None)
    w=np.where(wp[:,i]>0)[0]
    if len(w)==0:out['win'].append(None);out['wout'].append(None);continue
    # the first contiguous white run beyond the grass
    w=w[w>k];
    if len(w)==0:out['win'].append(None);out['wout'].append(None);continue
    runs=np.split(w,np.where(np.diff(w)>8)[0]+1);r0=max(runs,key=len) if True else runs[0]
    r0=runs[0] if len(runs[0])>40 else max(runs,key=len)
    out['win'].append(float(Rr[r0[0]]));out['wout'].append(float(Rr[r0[-1]]))
json.dump(out,open('sat/trace.json','w'))
for d in range(0,360,10):
    i=d*2;print(d,out['grass'][i],out['win'][i],out['wout'][i])
