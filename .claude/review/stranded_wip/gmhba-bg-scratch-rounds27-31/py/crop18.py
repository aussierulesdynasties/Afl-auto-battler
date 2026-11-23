import sys
from PIL import Image
d=sys.argv[1]
a=Image.open(d+'/f_0091.png'); a.crop((900,380,1280,560)).resize((1140,540)).save(d+'/z_shed.png')
a.crop((0,0,1280,110)).resize((1280,220)).save(d+'/z_far.png')
b=Image.open(d+'/f_0061.png'); b.crop((520,470,800,570)).resize((1120,400)).save(d+'/z_lot.png')
b.crop((1000,180,1280,330)).resize((1120,600)).save(d+'/z_house.png')
