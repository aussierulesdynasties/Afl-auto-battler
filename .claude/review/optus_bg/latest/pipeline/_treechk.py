import json; from PIL import Image, ImageDraw
im=Image.open('data/optus/sat_hi_plaza.png').convert('RGB'); d=ImageDraw.Draw(im)
for x,y,_k in json.load(open('data/optus/prep/trees.json')):
    if 80<=x<=260 and -50<=y<=135:
        c,r=(x-80)/0.125,(135-y)/0.125; d.ellipse([c-12,r-12,c+12,r+12],outline=(255,0,255),width=3)
im.save('_trees.jpg',quality=85)
