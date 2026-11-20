import json,numpy as np
from PIL import Image,ImageDraw,ImageFilter
M='C:/Users/DANTE/AppData/Local/Temp/claude/9f4017b9c485d8cb/fb8d066d-4ddf-4085-adc6-c6288b802d1c/scratchpad/moor/'
R=json.load(open('reg.json'));cx,cy=R['cm'][0]+R['t'][0],R['cm'][1]+R['t'][1]   # pmean in wb_3026 z19 pixels
td=Image.open(M+'td_full.png').convert('RGBA');N=td.size[0]
def place(bgfile,origin19,scale,out,crop=None):
    bg=Image.open(bgfile).convert('RGBA')
    # wb_3026 pixel -> global z19 pixel -> this image's pixel
    gx=473376*256+cx;gy=321937*256+cy;px=gx/scale-origin19[0]*256;py=gy/scale-origin19[1]*256
    t=td.resize((round(N/scale),round(N/scale)),Image.LANCZOS)
    a=np.asarray(t).copy();al=a[...,3]>10
    edge=np.asarray(Image.fromarray((al*255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES))>0
    half=a.copy();half[...,3]=np.where(al,150,0)
    ol=np.zeros_like(a);ol[edge]=(255,0,255,255)
    L=Image.new('RGBA',bg.size);L.alpha_composite(Image.fromarray(half),(round(px-t.size[0]/2),round(py-t.size[1]/2)))
    E_=Image.new('RGBA',bg.size);E_.alpha_composite(Image.fromarray(ol),(round(px-t.size[0]/2),round(py-t.size[1]/2)))
    o=Image.alpha_composite(bg,L);o2=Image.alpha_composite(bg,E_)
    W=Image.new('RGB',(bg.size[0]*2,bg.size[1]));W.paste(o.convert('RGB'),(0,0));W.paste(o2.convert('RGB'),(bg.size[0],0))
    if crop:W=W.crop(crop)
    W.save(out);print(out,W.size,px,py)
place('wb_3026_z19.png',(473376,321937),1,'ov_2014_07.png')
place('wb_10_z17.png',(118343,80484),4,'ov_2014_02_z17.png')
