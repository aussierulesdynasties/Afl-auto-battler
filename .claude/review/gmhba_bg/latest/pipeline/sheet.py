import sys,os
from PIL import Image
d,out,step=sys.argv[1],sys.argv[2],int(sys.argv[3])
fs=sorted(f for f in os.listdir(d) if f.endswith('.png'))[::step]
im=Image.open(os.path.join(d,fs[0])); w,h=im.size; s=480/w; tw,th=480,int(h*s)
cols=4; rows=(len(fs)+cols-1)//cols
S=Image.new('RGB',(cols*tw,rows*th))
for i,f in enumerate(fs): S.paste(Image.open(os.path.join(d,f)).convert('RGB').resize((tw,th)),((i%cols)*tw,(i//cols)*th))
S.save(out); print(len(fs),S.size)
