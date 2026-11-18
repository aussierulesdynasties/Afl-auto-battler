import json,sys
from PIL import Image,ImageDraw
L=json.load(open(sys.argv[1]));out=sys.argv[2];cols=int(sys.argv[3]) if len(sys.argv)>3 else 3
ims=[(x['out'].split('/')[-1],Image.open(x['out']).convert('RGB')) for x in L]
w=640;h=int(ims[0][1].height*w/ims[0][1].width);rows=(len(ims)+cols-1)//cols
S=Image.new('RGB',(cols*w,rows*(h+20)),(20,20,20));d=ImageDraw.Draw(S)
for i,(n,im) in enumerate(ims):
    x=(i%cols)*w;y=(i//cols)*(h+20);S.paste(im.resize((w,h)),(x,y+20));d.text((x+4,y+4),n,fill=(255,255,0))
S.save(out);print(S.size)
