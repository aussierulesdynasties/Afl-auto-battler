# Texture-pass proof board: one row per surface type. Columns: real photo crop | before (old texture, close) |
# after at game-camera distance | after close. Bottom: grey-level stddev of every texture, before -> after.
# Usage: python board_tex.py CROPS_DIR BEFORE_RENDERS_DIR STDDEV_JSON   (writes proof/tex_board_1.jpg, _2.jpg)
import sys,json,os
from PIL import Image,ImageDraw,ImageFont
CR,RB,SD=sys.argv[1:4];CROWD=sys.argv[4] if len(sys.argv)>4 else ''
F=ImageFont.truetype('C:/Windows/Fonts/bahnschrift.ttf',22);FS=ImageFont.truetype('C:/Windows/Fonts/bahnschrift.ttf',17)
ROWS=[('Roof sheeting (deck)','roofdeck','roofdeck','gc_roofdeck','cl_roofdeck'),
      ('Roof underside (soffit)','soffit','soffit','gc_bowl','cl_soffit'),
      ('Seats (empty, no crowd)','seats','seats','gc_bowl','cl_seats'),
      ('Painted steel, fascia','steel','steel','gc_sign','cl_steel'),
      ('Light cladding (west podium)','facade','panel_facade','gc_panel_facade','cl_panel_facade'),
      ('Slate cladding (corner blocks)','slate','slate','gc_slate','cl_slate'),
      ('Louvres','louvre','louvre','gc_louvre','cl_louvre'),
      ('Paving','paving','paving','gc_paving','cl_paving'),
      ('Concrete','concrete','concrete','gc_concrete','cl_concrete'),
      ('Glazing','glass','glass','gc_glass','cl_glass'),
      ('Ground sign: MARVEL STADIUM','sign_cl','sign','gc_sign','cl_sign')]
CW,CH,LH=420,280,34;HEAD=['real photo (reference only)','before (old texture)','after: game camera','after: close']
def cell(p):
    im=Image.open(p).convert('RGB');s=max(CW/im.width,CH/im.height);im=im.resize((int(im.width*s+.5),int(im.height*s+.5)),Image.LANCZOS)
    x=(im.width-CW)//2;y=(im.height-CH)//2;return im.crop((x,y,x+CW,y+CH))
def board(rows,out,table=False):
    tabh=600 if table else 0;W=4*CW+5*10;H=40+len(rows)*(CH+LH+10)+tabh
    bd=Image.new('RGB',(W,H),(22,22,24));d=ImageDraw.Draw(bd)
    for c,h in enumerate(HEAD):d.text((10+c*(CW+10),10),h,font=F,fill=(235,235,235))
    for r,(lab,crop,bef,gc,cl) in enumerate(rows):
        y=40+r*(CH+LH+10);d.text((10,y+4),lab,font=F,fill=(255,214,90))
        cells=[os.path.join(CR,crop+'.jpg'),os.path.join(RB,'r_cl_%s.png'%bef),'r_%s.png'%gc,'r_%s.png'%cl]
        if crop=='sign_cl':cells[1]=os.path.join(CR,'sign_gc.jpg')
        for c,p in enumerate(cells):
            if os.path.exists(p):bd.paste(cell(p),(10+c*(CW+10),y+LH))
            else:d.text((20+c*(CW+10),y+LH+CH//2),'no before render',font=FS,fill=(150,150,150))
        if crop=='sign_cl':d.text((10+CW+10+6,y+LH+4),'2019 aerial (photo)',font=FS,fill=(255,255,255))
    if table:
        S=json.load(open(SD));y0=H-tabh+10;d.text((10,H-30),'Crowd: '+CROWD,font=F,fill=(255,214,90));d.text((10,y0),'Grey-level stddev (0-255) per texture: before -> after',font=F,fill=(255,214,90))
        for i,(n,b,a) in enumerate(S):
            x=10+(i//10)*(W//3);y=y0+40+(i%10)*48
            t='%-13s %s -> %.1f'%(n,'new' if b is None else '%.1f'%b,a)+('' if b is None or abs(a-b)>0.01 else '  (unchanged)')
            d.text((x,y),t,font=F,fill=(235,235,235))
    bd.save(out,quality=90)
board(ROWS[:6],'proof/tex_board_1.jpg');board(ROWS[6:],'proof/tex_board_2.jpg',True);print('ok')
