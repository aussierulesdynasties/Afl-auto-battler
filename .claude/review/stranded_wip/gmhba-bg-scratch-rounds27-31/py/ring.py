import sys,glob
from PIL import Image
fs=sorted(glob.glob(sys.argv[1]+'/f_*.png')); w,h=640,360
S=Image.new('RGB',(w*2,h*((len(fs)+1)//2)),'black')
for i,f in enumerate(fs): S.paste(Image.open(f).convert('RGB').resize((w,h)),((i%2)*w,(i//2)*h))
S.save(sys.argv[2],quality=90); print(len(fs))
