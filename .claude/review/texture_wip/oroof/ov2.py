import json,math,numpy as np
from PIL import Image,ImageDraw,ImageFilter
S=np.asarray(Image.open('../obuild/sat/sat_025.png').convert('RGB')).astype(int)
W=(S.min(2)>175)&(S.max(2)-S.min(2)<45);M=np.asarray(Image.open('top_mask_lean.png'))>128
J=json.load(open('../obuild/geom.json'));oc=J['oc'];X0,Y1,R=-260,230,0.25
def at(A,a,r):
    u,v=int(round((oc[0]+math.cos(a)*r-X0)/R)),int(round((Y1-oc[1]-math.sin(a)*r)/R));return A[v,u]
def medge(a):
    rs=np.arange(60,200,R);w=np.array([at(M,a,r) for r in rs]);i=np.where(w)[0];return rs[i[0]],rs[i[-1]]
def run(a,r,step):  # white for 2 m starting at r going by step
    return all(at(W,a,r+step*k*R) for k in range(8))
rows=[]
for d in range(0,360,2):
    a=math.radians(d);mi,mo=medge(a)
    si=next((r for r in np.arange(mi-8,mi+8,R) if run(a,r,1)),None)
    so=next((r for r in np.arange(mo+8,mo-8,-R) if run(a,r,-1)),None)
    rows.append((d,si,so,mi,mo))
json.dump([[float(x) if x is not None else None for x in r] for r in rows],open('ov2_rows.json','w'))
for k,n in((1,'inner'),(2,'outer')):
    d=np.array([r[k+2]-r[k] for r in rows if r[k] is not None]);miss=sum(r[k] is None for r in rows)
    print('%s n=%d miss=%d median %+.2f mean|err| %.2f p90 %.2f max %.2f  <=1m %d <=2m %d'%(n,len(d),miss,np.median(d),np.abs(d).mean(),np.percentile(np.abs(d),90),np.abs(d).max(),(abs(d)<=1).sum(),(abs(d)<=2).sum()))
    print(' worst',sorted(((round(r[k+2]-r[k],1),r[0]) for r in rows if r[k] is not None),key=lambda t:-abs(t[0]))[:10],'miss at',[r[0] for r in rows if r[k] is None])
dep=np.array([(r[2]-r[1],r[4]-r[3]) for r in rows if r[1] is not None and r[2] is not None])
print('depth sat median %.1f (%.1f-%.1f)  model %.1f (%.1f-%.1f)'%(np.median(dep[:,0]),dep[:,0].min(),dep[:,0].max(),np.median(dep[:,1]),dep[:,1].min(),dep[:,1].max()))
# overlay: sat + model outline red + sat-detected edge points cyan
A=np.asarray(Image.open('../obuild/sat/sat_025.png').convert('RGB')).copy()
E=np.asarray(Image.fromarray((M*255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES))>0;A[E]=(255,0,40)
im=Image.fromarray(A);dr=ImageDraw.Draw(im)
for r in rows:
    a=math.radians(r[0])
    for s in(r[1],r[2]):
        if s is None:continue
        u,v=(oc[0]+math.cos(a)*s-X0)/R,(Y1-oc[1]-math.sin(a)*s)/R;dr.ellipse((u-3,v-3,u+3,v+3),outline=(0,230,255),width=2)
for x in range(-250,241,50):
    px=(x-X0)/R;dr.line([(px,0),(px,1840)],fill=(255,200,0));dr.text((px+3,3),str(x)+' m',fill=(255,255,0))
for y in range(-200,231,50):
    py=(Y1-y)/R;dr.line([(0,py),(2000,py)],fill=(255,200,0));dr.text((3,py+3),str(y)+' m',fill=(255,255,0))
im.crop((300,250,1750,1600)).save('overlay.png')
