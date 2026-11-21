from PIL import Image
S=Image.open('map/sat_1400.png').convert('RGB'); k=S.size[0]/1400
cx,cy,w=-125,230,220
s=S.crop((int((cx-w/2+700)*k),int((700-cy-w/2)*k),int((cx+w/2+700)*k),int((700-cy+w/2)*k))).resize((1000,1000),Image.BICUBIC)
r=Image.open('nb/nb_ortho.png').convert('RGB').resize((1000,1000),Image.LANCZOS)
o=Image.new('RGB',(2000,1000)); o.paste(r,(0,0)); o.paste(s,(1000,0)); o.save('nb/pair.jpg',quality=90)
