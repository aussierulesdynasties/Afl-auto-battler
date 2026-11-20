import sys;from cam import *
from PIL import Image,ImageDraw
im=Image.open(sys.argv[1]).convert('RGB');d=ImageDraw.Draw(im)
for k,v in G.items():
    if k=='masts':continue
    Y=proj([(x,y,0) for x,y in v]);d.line([tuple(a) for a in Y],fill=(255,255,0) if k=='pitch' else (0,255,255) if k=='stadium' else (255,0,255),width=2)
im.save(sys.argv[2])
