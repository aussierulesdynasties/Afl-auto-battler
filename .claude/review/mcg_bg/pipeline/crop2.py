from PIL import Image
rows=[]
for n,box in [('base_000',(300,520,1280,720)),('base_003',(0,520,980,720))]:
    a=Image.open('out/mcg/check_prebake/%s.png'%n).crop(box); b=Image.open('out/mcg/check/%s.png'%n).crop(box); rows.append((a,b))
s=Image.new('RGB',(1960,400))
for k,(a,b) in enumerate(rows): s.paste(a,(0,200*k)); s.paste(b,(980,200*k))
s.save('out/mcg/crop_ground.png')
