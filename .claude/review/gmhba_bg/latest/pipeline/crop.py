from PIL import Image
a=Image.open('out/mcg/check_prebake/base_000.png').crop((150,380,650,720)); b=Image.open('out/mcg/check/base_000.png').crop((150,380,650,720))
s=Image.new('RGB',(1000,340)); s.paste(a,(0,0)); s.paste(b,(500,0)); s.save('out/mcg/crop_cmp.png')
