import sys
from PIL import Image
ph=Image.open('refs/ref.jpg').convert('RGBA');m=Image.open('out/render_model.png').convert('RGBA');g=Image.open('out/render_ground.png').convert('RGBA')
mg=Image.new('RGBA',ph.size,(30,30,30,255));mg.alpha_composite(g)
ov=ph.copy();a=m.split()[3].point(lambda v:int(v*0.6));m2=m.copy();m2.putalpha(a);ov.alpha_composite(m2)
ov.save('out/overlay.png')
W,H=ph.size;b=Image.new('RGB',(W*3+40,H),(20,20,20))
for i,im in enumerate([ph,mg,ov]):b.paste(im.convert('RGB'),(i*(W+20),0))
b.save(sys.argv[1] if len(sys.argv)>1 else 'out/board.png')
