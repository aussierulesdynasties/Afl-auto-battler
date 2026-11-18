from PIL import Image,ImageDraw
import random
random.seed(3)
def save(im,n):im.save('tex/'+n)
# seats: 256x256, 8 rows, aisle on the left edge
im=Image.new('RGB',(256,256),(226,58,42));d=ImageDraw.Draw(im)
for r in range(8):
    y=r*32;d.rectangle([0,y+20,255,y+31],fill=(150,110,104))
    for x in range(0,256,8):d.rectangle([x+1,y+2,x+6,y+19],fill=(242,72,50))
d.rectangle([0,0,14,255],fill=(176,170,166));save(im,'seats.png')
# podium facade: vertical multicolour fins
cols=[(214,58,48),(236,128,40),(240,190,60),(40,70,150),(110,60,140),(230,230,230),(60,120,190)]
im=Image.new('RGB',(512,128),(60,60,70));d=ImageDraw.Draw(im)
for x in range(0,512,6):d.rectangle([x,0,x+4,127],fill=random.choice(cols))
save(im,'stripes.png')
# lamp head face
im=Image.new('RGB',(128,96),(248,248,248));d=ImageDraw.Draw(im)
for i in range(8):
    for j in range(6):d.rectangle([4+i*15,4+j*15,15+i*15,15+j*15],fill=(214,218,226))
save(im,'lamps.png')
# scoreboard back with white legs handled by geometry; screen front
im=Image.new('RGB',(256,96),(25,30,45));save(im,'screen.png')
# LED fascia band
im=Image.new('RGB',(512,32),(40,48,80));d=ImageDraw.Draw(im)
for x in range(0,512,64):d.rectangle([x+6,10,x+50,22],fill=(80,140,220))
save(im,'led.png')
