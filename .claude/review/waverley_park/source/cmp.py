import sys
from PIL import Image
P=Image.open('ref.jpg').convert('RGB');M=Image.open('out/model_on_photo.png').convert('RGB')
R={'mem':(260,40,660,180),'nf':(250,380,800,576),'lf':(0,200,330,520),'rf':(760,120,1023,440),'farR':(620,40,1000,200)}
for n,(x0,y0,x1,y1) in R.items():
    k=950/(x1-x0);w,h=950,int((y1-y0)*k)
    a=P.crop((x0,y0,x1,y1)).resize((w,h),Image.LANCZOS);b=M.crop((2*x0,2*y0,2*x1,2*y1)).resize((w,h),Image.LANCZOS)
    o=Image.new('RGB',(w,2*h+6),(255,255,255));o.paste(a,(0,0));o.paste(b,(0,h+6));o.save('out/cmp_'+n+'.png')
