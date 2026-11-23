import sys
from PIL import Image
d=sys.argv[1]; o=sys.argv[2]
a=Image.open(d+'/f_0121.png')
a.crop((900,520,1280,720)).resize((1140,600)).save(o+'/z_houses.png')
a.crop((620,60,1280,160)).resize((1320,200)).save(o+'/z_cbd.png')
a.crop((0,0,640,90)).resize((1280,180)).save(o+'/z_hor.png')
a.crop((700,380,1000,560)).resize((900,540)).save(o+'/z_road.png')
b=Image.open(d+'/f_0091.png'); b.crop((0,0,700,130)).resize((1400,260)).save(o+'/z_bay.png')
b.crop((0,60,640,250)).resize((1280,380)).save(o+'/z_cbd2.png')
