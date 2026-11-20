import sys;from PIL import Image
ph=Image.open('photo.png').convert('RGBA');rd=Image.open(sys.argv[1]).convert('RGBA')
ov=ph.copy();a=rd.split()[3].point(lambda v:int(v*0.55));ov.paste(rd,(0,0),a)
ov.convert('RGB').save(sys.argv[2])
if len(sys.argv)>3:
    W=1920//2;H=1280//2;B=Image.new('RGB',(W*3+20,H),(20,20,20))
    bg=Image.new('RGBA',rd.size,(40,40,46,255));bg.alpha_composite(rd)
    for i,im in enumerate([ph,bg,ov]):B.paste(im.convert('RGB').resize((W,H),Image.LANCZOS),(i*(W+10),0))
    B.save(sys.argv[3])
