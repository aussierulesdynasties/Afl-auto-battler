# python work/parts.py outdir : one board per part, photo | render | 50% blend, cropped from the ov3 boards (panels 960x486)
import sys,os
from PIL import Image,ImageDraw
out=sys.argv[1];os.makedirs(out,exist_ok=True)
P={'north_entrance_canopy':('f000',(300,150,700,330)),'north_flank_blocks':('f000',(0,130,960,330)),
 'ne_olympic_screen':('f045',(500,0,960,300)),'east_facades':('f090',(0,100,960,330)),'se_ponsford':('f135',(0,100,960,330)),
 'south_gss':('f180',(80,100,880,330)),'sw_screen':('f225',(0,0,480,300)),'west_mcc':('f270',(0,100,960,330)),
 'nw_warne':('f315',(0,100,960,330)),'roof_trusses_north':('n_n',(0,0,960,486)),'light_towers':('o000',(0,0,960,486)),
 'plaza_outer_fence':('n_c',(0,0,960,486))}
for name,(v,(x0,y0,x1,y1)) in P.items():
    b=Image.open(f'work/ov3_{v}.png').convert('RGB');H=486;W=x1-x0
    bd=Image.new('RGB',(3*W+20,y1-y0+30),(20,20,20));d=ImageDraw.Draw(bd)
    for k,lab in enumerate(('photo','render','blend')):
        oy=(0,H,2*H-1)[k];bd.paste(b.crop((x0,y0+oy,x1,y1+oy)),(k*(W+10),30))
        d.text((k*(W+10)+4,8),f'{name}  {v}  {lab}',fill=(255,255,0))
    bd.save(f'{out}/part_{name}.png')
print('ok',len(P))
