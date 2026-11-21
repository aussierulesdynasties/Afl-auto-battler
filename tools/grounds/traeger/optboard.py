# out/opt/{A,B,C}_{north,far}.png + the c07 crop -> out/opt/board_options.png (the director's A/B/C choice, one picture each)
import os
from PIL import Image,ImageDraw,ImageFont
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),'out','opt');F='C:/Windows/Fonts/segoeuib.ttf'
T={'A':'A  All boards as in the 2025 photo: TIO run + sponsor boards, names hand-painted',
   'B':'B  TIO run only; bare chain-link fence where the sponsor boards are',
   'C':'C  No boards: bare chain-link fence everywhere'}
W=1500;th=640;sc=0.5;w=int(W*sc);h=int(th*sc);hd=56
ref=Image.open(os.path.join(os.path.dirname(D),'c07_sponsors.png'));ref=ref.resize((2*w,int(ref.height*2*w/ref.width)))
out=Image.new('RGB',(2*w+30,hd+ref.height+20+3*(h+hd)+10),(24,24,26));d=ImageDraw.Draw(out)
d.text((10,14),'Reference: c07 (2025, empty day), boards read at full zoom',font=ImageFont.truetype(F,26),fill=(235,235,235))
out.paste(ref,(10,hd));y=hd+ref.height+20
for k in 'ABC':
    d.text((10,y+12),T[k],font=ImageFont.truetype(F,26),fill=(255,255,255));y+=hd
    for i,n in enumerate(('north','far')):
        out.paste(Image.open(os.path.join(D,'%s_%s.png'%(k,n))).convert('RGB').resize((w,h),Image.LANCZOS),(10+i*(w+10),y))
    y+=h
out.save(os.path.join(D,'board_options.png'));print(out.size)
