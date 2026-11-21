from PIL import Image,ImageDraw
import os
N=['steel','post','frame','lamps','sign_tio','sign_white','screen','rail','shed_wall','roof_white','brick','tree','trunk','dirt','grass']
B=Image.new('RGB',(5*320,3*340),(40,40,40));d=ImageDraw.Draw(B)
for i,n in enumerate(N):
    im=Image.open(os.path.join('tex3',n+'.png'))
    if im.mode=='RGBA':bg=Image.new('RGBA',im.size,(60,110,50,255));bg.alpha_composite(im);im=bg
    im=im.convert('RGB');im.thumbnail((300,300));x,y=(i%5)*320+10,(i//5)*340+10
    B.paste(im,(x,y));d.text((x,y+305),n,fill=(255,255,255))
B.save('out/texsite_board.png')
