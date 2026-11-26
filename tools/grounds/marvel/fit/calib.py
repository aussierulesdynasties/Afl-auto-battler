import json,numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage,optimize
im=np.asarray(Image.open('/tmp/claude-0/ref/geA/ge_top.png').convert('RGB'),float)
H,W=im.shape[:2]
r,g,b=im[...,0],im[...,1],im[...,2]
wat=(b>r+12)&(im.mean(2)<120)
wat[:60]=False  # the UI banner
wat=ndimage.binary_opening(wat,iterations=2);lab,n=ndimage.label(wat);sz=ndimage.sum(wat,lab,range(1,n+1));wat=lab==(1+np.argmax(sz))
wat=ndimage.binary_fill_holes(ndimage.binary_closing(wat,iterations=3))
Image.fromarray((wat*255).astype(np.uint8)).save('ge_water.png')
edge=wat^ndimage.binary_erosion(wat);edge[:62]=False;edge[:, :3]=False;edge[-3:]=False
dt=ndimage.distance_transform_edt(~edge)
O=json.load(open('osm_w.json'))
# OSM water mask edge points (water minus piers), sampled every 0.5 m along polygons, then kept only where on water boundary
from shapely.geometry import Polygon
from shapely.ops import unary_union
wp=unary_union([Polygon(p).buffer(0) for p in O['water']]);pp=unary_union([Polygon(p).buffer(0) for _,_,p in O['pier'] if len(p)>=3])
land_water=wp.difference(pp)
def pts(g):
    out=[]
    geoms=getattr(g,'geoms',[g])
    for G in geoms:
        for ring in [G.exterior]+list(G.interiors):
            L=ring.length;k=int(L/0.5)
            out+= [ring.interpolate(i*0.5).coords[0] for i in range(k)]
    return np.array(out)
P=pts(land_water)
P=P[(np.abs(P[:,0])<420)&(np.abs(P[:,1])<260)]
def proj(par,E,N):
    mpp,th,tx,ty=par;c,s=np.cos(th),np.sin(th)
    x=(c*E-s*N)/mpp;y=-(s*E+c*N)/mpp
    return W/2+tx+x,H/2+ty+y
def cost(par,ret=False):
    x,y=proj(par,P[:,0],P[:,1]);m=(x>3)&(x<W-3)&(y>62)&(y<H-3)
    d=ndimage.map_coordinates(dt,[y[m],x[m]],order=1)
    return d if ret else np.mean(np.minimum(d,25))
best=None
for mpp in np.linspace(0.45,0.6,16):
    for th in np.radians([-2,0,2]):
        res=optimize.minimize(cost,[mpp,th,0,0],method='Nelder-Mead',options=dict(xatol=1e-4,fatol=1e-4,maxiter=3000))
        if best is None or res.fun<best.fun:best=res
par=best.x;d=cost(par,True)
print('mpp %.4f rot %.2f deg shift %.1f,%.1f px; edge points %d; dist px mean %.2f median %.2f p90 %.2f'%(par[0],np.degrees(par[1]),par[2],par[3],len(d),d.mean(),np.median(d),np.percentile(d,90)))
print('in metres: median %.2f p90 %.2f'%(np.median(d)*par[0],np.percentile(d,90)*par[0]))
json.dump(dict(mpp=par[0],th=par[1],tx=par[2],ty=par[3]),open('calib_top.json','w'))
v=Image.fromarray(im.astype(np.uint8));D=ImageDraw.Draw(v)
x,y=proj(par,P[:,0],P[:,1])
for a,bb in zip(x,y):D.point((a,bb),fill=(255,0,0))
v.save('calib_check.png')
