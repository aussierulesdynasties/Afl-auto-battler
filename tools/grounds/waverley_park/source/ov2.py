import sys
from PIL import Image
ref=Image.open('ref.jpg').convert('RGBA').resize((2046,1152),Image.LANCZOS)
r=Image.open('out/render.png').convert('RGBA')
bg=ref.copy();bg.alpha_composite(r);bg.convert('RGB').save('out/model_on_photo.png')
ov=Image.blend(ref,bg,0.5);ov.convert('RGB').save('out/ov50.png')
side=Image.new('RGB',(2046,1152*2));side.paste(ref.convert('RGB'),(0,0));side.paste(bg.convert('RGB'),(0,1152));side.save('out/stack.png')
for n,box in (('l',(0,250,1023,1000)),('r',(1023,250,2046,1000)),('t',(400,0,1700,500))):
    ov.crop(box).convert('RGB').save(f'out/ov_{n}.png');ref.crop(box).convert('RGB').save(f'out/rf_{n}.png');bg.crop(box).convert('RGB').save(f'out/md_{n}.png')
