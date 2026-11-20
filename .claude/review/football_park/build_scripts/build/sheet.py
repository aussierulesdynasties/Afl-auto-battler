import sys,glob
from PIL import Image,ImageDraw
fs=sorted(glob.glob(sys.argv[1]));out=sys.argv[2];c=3;w,h=800,500
for k in range(0,len(fs),9):
    g=fs[k:k+9];im=Image.new('RGB',(c*w,((len(g)+c-1)//c)*h),(60,60,60))
    for i,f in enumerate(g):
        a=Image.open(f).convert('RGBA');bg=Image.new('RGBA',a.size,(120,150,190,255));bg.alpha_composite(a)
        im.paste(bg.convert('RGB').resize((w,h)),((i%c)*w,(i//c)*h));ImageDraw.Draw(im).text(((i%c)*w+8,(i//c)*h+6),__import__('os').path.basename(f),fill=(255,255,0))
    im.save(f'{out}_{k//9}.png')
