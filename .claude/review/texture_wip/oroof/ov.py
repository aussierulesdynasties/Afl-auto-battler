import json,math,numpy as np
from PIL import Image,ImageDraw,ImageFilter
B='../obuild/';S=np.asarray(Image.open(B+'sat/sat_025.png').convert('RGB')).astype(int)
M=np.asarray(Image.open('top_mask_lean.png').convert('L'))>128
J=json.load(open(B+'geom.json'));oc=J['oc'];X0,Y1,R=-260,230,0.25
W=(S.min(2)>185)&(S.max(2)-S.min(2)<40)
def edges(A,a):
    c,s=math.cos(math.radians(a)),math.sin(math.radians(a));inn=out=None;r=60.0;gap=0
    while r<200:
        u,v=int(round((oc[0]+c*r-X0)/R)),int(round((Y1-oc[1]-s*r)/R))
        w=A[v,u] if 0<=v<A.shape[0] and 0<=u<A.shape[1] else False
        if w:
            if inn is None:inn=r
            out=r;gap=0
        elif inn is not None:
            gap+=R
            if gap>4:break
        r+=R
    return inn,out
rows=[]
for a in range(0,360,2):
    si,so=edges(W,a);mi,mo=edges(M,a);rows.append((a,si,so,mi,mo))
def st(k):
    d=np.array([r[k+2]-r[k] for r in rows if r[k] and r[k+2]]);return len(d),np.median(d),np.abs(d).mean(),np.percentile(np.abs(d),90),np.abs(d).max()
print('outer n %d med %.2f mean|d| %.2f p90 %.2f max %.2f'%st(2))
print('inner n %d med %.2f mean|d| %.2f p90 %.2f max %.2f'%st(1))
dep=[(r[2]-r[1],r[4]-r[3]) for r in rows if all(r[1:])];dep=np.array(dep)
print('depth sat med %.1f model med %.1f  sat range %.1f-%.1f model %.1f-%.1f'%(np.median(dep[:,0]),np.median(dep[:,1]),dep[:,0].min(),dep[:,0].max(),dep[:,1].min(),dep[:,1].max()))
bad=[r for r in rows if r[2] and r[4] and abs(r[4]-r[2])>1.5 or r[1] and r[3] and abs(r[3]-r[1])>1.5]
print('angles >1.5m:',[(r[0],round((r[3] or 0)-(r[1] or 0),1),round((r[4] or 0)-(r[2] or 0),1)) for r in bad])
json.dump(rows,open('ov_rows.json','w'))
im=Image.fromarray(S.astype(np.uint8));e=Image.fromarray((M*255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES)
E=np.asarray(e)>0;A=np.asarray(im).copy();A[E]=(255,0,40);im=Image.fromarray(A)
im.crop((300,250,1750,1600)).save('overlay.png')
