# hand-made chain-link tile: 256 px = 1 m, diamonds 60 mm, galvanised wire, transparent gaps
from PIL import Image, ImageDraw
import sys
N=256; im=Image.new('RGBA',(N,N),(0,0,0,0)); d=ImageDraw.Draw(im); s=N//16
for i in range(-16,32):
    d.line([(i*s,0),(i*s+N,N)],fill=(150,154,156,255),width=2)
    d.line([(i*s,N),(i*s+N,0)],fill=(128,132,134,255),width=2)
im.save(sys.argv[1])
