# Crop boards: one PNG per part, photo | render | 50% overlay side by side at full resolution, labelled.
import sys,os
from PIL import Image,ImageDraw,ImageFont
def board(photo,render,parts,outdir,tag):
    ph=Image.open(photo).convert('RGB');rd=Image.open(render).convert('RGBA').resize(ph.size,Image.LANCZOS)
    rw=Image.new('RGB',ph.size,(255,255,255));rw.paste(rd,(0,0),rd);ov=Image.blend(ph,rw,0.5)
    try:fn=ImageFont.truetype('arial.ttf',26)
    except Exception:fn=ImageFont.load_default()
    os.makedirs(outdir,exist_ok=True);outs=[]
    for name,b in parts.items():
        ims=[i.crop(b) for i in(ph,rw,ov)];w,h=ims[0].size
        S=Image.new('RGB',(w*3+20,h+40),(20,20,20));d=ImageDraw.Draw(S)
        for k,(i,l) in enumerate(zip(ims,('photo','render','50% overlay'))):S.paste(i,(k*(w+10),40));d.text((k*(w+10)+6,6),f'{tag} {name}: {l}',fill=(255,255,255),font=fn)
        fp=os.path.join(outdir,f'{tag}_{name}.png');S.save(fp);outs.append(fp)
    return outs
GOR=dict(roof_gables=(900,1000,2600,1260),clock_gable=(1700,1050,2120,1230),posts_deck=(950,1180,2600,1520),
         wall_pilasters_stairs=(950,1460,2600,1700),entrance=(1650,1440,2150,1700),se_end=(800,1000,1250,1700))
AER=dict(ryde_stand=(2380,700,3050,1050),se_open_stand=(3500,850,4250,1550),gorringe=(4050,1550,4650,2350),
         lewis_stand=(3650,2450,4400,3250),letitia_stand=(1050,2250,1700,2950),north_terrace=(1700,2600,4000,3050),
         sheds_scoreboard=(1250,780,2000,1450),whole=(0,0,5000,4000))
if __name__=='__main__':
    print(board('web/hr_gor.jpg','r_full_gor.png',GOR,'boards','gorringe'))
    print(board('ref_full.png','r_full_aerial.png',AER,'boards','aerial'))
