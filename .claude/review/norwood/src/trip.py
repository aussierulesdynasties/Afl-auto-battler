import sys
from PIL import Image
ph=Image.open(sys.argv[1]).convert('RGB');r=Image.open(sys.argv[2]).convert('RGBA').resize(ph.size)
bg=ph.copy();comp=Image.alpha_composite(Image.new('RGBA',ph.size,(30,30,30,255)),r).convert('RGB')
ov=Image.blend(ph,Image.alpha_composite(ph.convert('RGBA'),r).convert('RGB'),0.5)
W,H=ph.size;T=Image.new('RGB',(W*3,H));T.paste(ph,(0,0));T.paste(comp,(W,0));T.paste(ov,(2*W,0));T.save(sys.argv[3])
ov.save(sys.argv[3].replace('.png','_ov.png'))
