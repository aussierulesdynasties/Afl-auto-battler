# top-down overlay in the stadium frame: r_top.png (model straight down, same lean as the satellite) on sat_uv.png
# image x=(150-v)*4, y=(u+150)*4 (u south+, v west+), 0.25 m/px. Writes t_on.jpg (outlines), t_blend.jpg, t_model.jpg, t_sat.jpg, zooms
import sys,numpy as np
from PIL import Image,ImageDraw,ImageFilter
A=Image.open('sat_uv.png').convert('RGB');M=Image.open('r_top.png').convert('RGBA')
a=np.asarray(M)[...,3]>10
g=np.asarray(M.convert('L')).astype(float);ed=(np.abs(np.diff(g,axis=0,prepend=0))+np.abs(np.diff(g,axis=1,prepend=0)))>25
sil=a&~(np.asarray(Image.fromarray(a.astype(np.uint8)*255).filter(ImageFilter.MinFilter(5)))>0)
on=np.asarray(A).copy();on[ed&a]=(255,40,200);on[sil]=(0,255,255)
bl=Image.blend(A,Image.alpha_composite(A.convert('RGBA'),M).convert('RGB'),0.5)
def grid(im,step=10):
    d=ImageDraw.Draw(im)
    for k in range(-150,151,step):
        X=(150-k)*4;Y=(k+150)*4;col=(255,230,0) if k%50==0 else (120,110,0)
        d.line([(0,Y),(1200,Y)],fill=col);d.line([(X,0),(X,1200)],fill=col)
        if k%20==0:d.text((2,Y+1),'u%d'%k,fill=(255,255,255));d.text((X+2,2),'v%d'%k,fill=(255,255,255))
    return im
O=grid(Image.fromarray(on));O.save('t_on.jpg',quality=92);grid(bl).save('t_blend.jpg',quality=92);grid(A.copy()).save('t_sat.jpg',quality=92)
Mo=Image.new('RGB',M.size,(40,40,40));Mo.paste(M,(0,0),M);grid(Mo).save('t_model.jpg',quality=92)
for n,(x0,y0) in {'NW':(0,0),'NE':(600,0),'SW':(0,600),'SE':(600,600),'W':(0,300),'E':(600,300),'N':(300,0),'S':(300,600)}.items():
    for src,tag in((O,'on'),(A,'sat'),(Mo,'model')):
        im=src.crop((x0,y0,x0+600,y0+600)).resize((1200,1200),Image.LANCZOS)
        if tag!='on':grid_z=ImageDraw.Draw(im)
        im.save('t_%s_%s.jpg'%(tag,n),quality=90)
print('ok')
