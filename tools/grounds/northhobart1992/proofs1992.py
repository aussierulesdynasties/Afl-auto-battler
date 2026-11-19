# Proof boards for the 1992 rework (run after chain2.sh). Photo panels come from the committed boards in
# .claude/review/northhobart/boards (the 1992 aerial crop and the Gorringe photo crops), so no web file is needed.
# Each board: photo | new render | 50% overlay, same crop box, labelled.
import os
from PIL import Image,ImageDraw,ImageFont
from boards import GOR,AER
OLD='../../../.claude/review/northhobart/boards';NEW='../../../.claude/review/north_hobart'
try:FN=ImageFont.truetype('arial.ttf',26)
except Exception:FN=ImageFont.load_default()
def photo_panel(tag,name):
    b=GOR[name] if tag=='gorringe' else AER[name];w,h=b[2]-b[0],b[3]-b[1]
    return Image.open(f'{OLD}/{tag}_{name}.png').convert('RGB').crop((0,40,w,40+h))
def board(tag,name,render,out):
    b=GOR[name] if tag=='gorringe' else AER[name];ph=photo_panel(tag,name)
    rd=render.crop(b);rw=Image.new('RGB',rd.size,(255,255,255));rw.paste(rd,(0,0),rd);ov=Image.blend(ph,rw,0.5)
    w,h=ph.size;S=Image.new('RGB',(w*3+20,h+40),(20,20,20));d=ImageDraw.Draw(S)
    for k,(i,l) in enumerate(zip((ph,rw,ov),('photo','1992 model','50% overlay'))):S.paste(i,(k*(w+10),40));d.text((k*(w+10)+6,6),f'{tag} {name}: {l}',fill=(255,255,255),font=FN)
    S.save(out);return out
if __name__=='__main__':
    os.makedirs(f'{NEW}/boards',exist_ok=True)
    # the 1992 aerial (5000x4000 crop) recovered from the whole-aerial board, for topdown.py
    Image.open(f'{OLD}/aerial_whole.png').convert('RGB').crop((0,40,5000,4040)).save('ref_full_1992.png')
    ga=Image.open(f'{NEW}/renders/r_full_gor.png').convert('RGBA');aa=Image.open(f'{NEW}/renders/r_full_aerial.png').convert('RGBA')
    for n in GOR:print(board('gorringe',n,ga,f'{NEW}/boards/gorringe_{n}.png'))
    for n in AER:
        if n!='whole':print(board('aerial',n,aa,f'{NEW}/boards/aerial_{n}.png'))
