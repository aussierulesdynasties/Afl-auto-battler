from PIL import Image, ImageDraw; import numpy as np, json
from scipy import ndimage
Image.MAX_IMAGE_PIXELS=None
im=Image.open('data/accor/sat.png').convert('RGB'); a=np.asarray(im,np.float32)
sp=json.load(open('spec/accor.json')); poly=[p for k,p in sp['paint_poly'] if k=='paved'][0]
mk=Image.new('L',im.size,0); ImageDraw.Draw(mk).polygon([(3000+x*2,3000-y*2) for x,y in poly],fill=1); mk=np.asarray(mk)>0
w=(a.min(2)>225)&mk
lab,n=ndimage.label(w); out=[]
for i,sl in enumerate(ndimage.find_objects(lab)):
    h=sl[0].stop-sl[0].start; wd=sl[1].stop-sl[1].start; area=(lab[sl]==i+1).sum()
    if 8<=h<=20 and 8<=wd<=20 and area>50:
        cy=(sl[0].start+sl[0].stop)/2; cx=(sl[1].start+sl[1].stop)/2
        r=np.hypot((cx-3000)/2,(3000-cy)/2)
        if r>160: out.append([round((cx-3000)/2,1),round((3000-cy)/2,1),h/2,wd/2])
print(len(out)); [print(o) for o in out]
json.dump(out,open('data/accor/towers.json','w'))
d=im.crop((2000,2000,4000,4000)).copy(); D=ImageDraw.Draw(d)
for x,y,_,_ in out: px,py=3000+x*2-2000,3000-y*2-2000; D.ellipse((px-14,py-14,px+14,py+14),outline=(255,0,0),width=3)
d.resize((1400,1400)).save('out/accor/towers_det.jpg',quality=85)
