# Texture-pass proof board (Optus). Rows = surfaces; columns: real photo crop (reference only) | before (old texture,
# close) | after at game distance | after close. Last board ends with every texture's grey-level stddev before -> after.
# Usage: python board_tex.py CROPS_DIR BEFORE_DIR AFTER_DIR OUTDIR   (run from .claude/review/optus)
import sys,os,glob
import numpy as np
from PIL import Image,ImageDraw,ImageFont
CR,BD,AD,OD=sys.argv[1:5]
F=ImageFont.truetype('C:/Windows/Fonts/bahnschrift.ttf',22);FS=ImageFont.truetype('C:/Windows/Fonts/bahnschrift.ttf',17)
ROWS=[('Roof membrane','roof'),('Roof underside','under'),('Seats (empty, no crowd)','seats'),('Bronze screen','bronze'),
      ('Glass band','glass'),('Podium wall','podwall'),('Terrace','terrace'),('Plaza paving (street apron)','plaza'),
      ('Grand stair','stair'),('Sign A: OPTUS STADIUM + yes','sign_a'),('Sign B: OPTUS STADIUM (text only, logo not visible in o2)','sign_b')]
CW,CH,LH=420,280,34;HEAD=['real photo (reference only)','before (old texture)','after: game distance','after: close']
def cell(p):
    im=Image.open(p).convert('RGB');s=max(CW/im.width,CH/im.height);im=im.resize((int(im.width*s+.5),int(im.height*s+.5)),Image.LANCZOS)
    x=(im.width-CW)//2;y=(im.height-CH)//2;return im.crop((x,y,x+CW,y+CH))
g=lambda p:float(np.asarray(Image.open(p).convert('L'),float).std())
def board(rows,out,table=False):
    tabh=620 if table else 0;W=4*CW+5*10;H=40+len(rows)*(CH+LH+10)+tabh
    bd=Image.new('RGB',(W,H),(22,22,24));d=ImageDraw.Draw(bd)
    for c,h in enumerate(HEAD):d.text((10+c*(CW+10),10),h,font=F,fill=(235,235,235))
    for r,(lab,k) in enumerate(rows):
        y=40+r*(CH+LH+10);d.text((10,y+4),lab,font=F,fill=(255,214,90))
        for c,p in enumerate((os.path.join(CR,k+'.jpg'),os.path.join(BD,'cl_%s.png'%k),os.path.join(AD,'gc_%s.png'%k),os.path.join(AD,'cl_%s.png'%k))):
            bd.paste(cell(p),(10+c*(CW+10),y+LH))
        if k=='sign_b':d.text((10+6,y+LH+4),'o2 aerial',font=FS,fill=(255,255,255))
        if k.startswith('sign'):d.text((10+CW+10+6,y+LH+4),'no sign before',font=FS,fill=(255,255,255))
    if table:
        y0=H-tabh+10;d.text((10,y0),'Grey-level stddev (0-255) per texture: before -> after',font=F,fill=(255,214,90))
        fs=sorted(glob.glob('tex/*.png'))
        for i,f in enumerate(fs):
            n=os.path.basename(f)[:-4];b='tex_base/'+n+'.png';a=g(f);bv=g(b) if os.path.exists(b) else None
            t='%-10s %s -> %.1f'%(n,'new' if bv is None else '%.1f'%bv,a)+('' if bv is None or abs(a-bv)>0.05 else ' (kept)')
            d.text((10+(i//10)*(W//3),y0+40+(i%10)*46),t,font=F,fill=(235,235,235))
        d.text((10,H-36),'Crowd: none found. The Optus build has no crowd cards, crowd meshes or people billboards, and the seat map had no painted crowd.',font=FS,fill=(255,214,90))
    bd.save(out,quality=90)
board(ROWS[:6],os.path.join(OD,'tex_board_1.jpg'));board(ROWS[6:],os.path.join(OD,'tex_board_2.jpg'),True);print('ok')
