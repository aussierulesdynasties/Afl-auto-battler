# python bz.py RENDER PHOTO W H x0 y0 x1 y1 OUT : photo crop (border fractions) above/beside the border render, plus colour diffs
import sys
from PIL import Image
r=Image.open(sys.argv[1]).convert('RGBA');ph=Image.open(sys.argv[2]).convert('RGB')
W,H=int(sys.argv[3]),int(sys.argv[4]);f=[float(v) for v in sys.argv[5:9]]
pc=ph.crop((round(f[0]*W),round(f[1]*H),round(f[2]*W),round(f[3]*H))).resize(r.size,Image.LANCZOS)
bg=Image.new('RGBA',r.size,(58,60,66,255));bg.alpha_composite(r);w,h=r.size
side=w<h
bd=Image.new('RGB',(w*2,h) if side else (w,h*2));bd.paste(pc,(0,0));bd.paste(bg.convert('RGB'),(w,0) if side else (0,h))
bd.save(sys.argv[9]);bd.resize((bd.width//2,bd.height//2)).save(sys.argv[9].replace('.png','_s.png'))
