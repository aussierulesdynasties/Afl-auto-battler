from PIL import Image
D='C:/Users/DANTE/AppData/Local/Temp/claude/b11ecf2cca45cfb5/002c0964-89cd-46e5-bf30-bd32e1451dbd/scratchpad/wh/'
ph=Image.open(D+'bb1984.jpg').convert('RGB');rd=Image.open(D+'rend.png').convert('RGB').resize(ph.size)
bl=Image.blend(ph,rd,0.5);W,H=ph.size;o=Image.new('RGB',(W*3,H));o.paste(ph,(0,0));o.paste(rd,(W,0));o.paste(bl,(2*W,0));o.save(D+'cmp1.png')
bl.resize((W*2,H*2),Image.LANCZOS).save(D+'ov_big.png')
