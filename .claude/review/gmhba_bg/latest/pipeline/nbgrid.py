from PIL import Image, ImageDraw
S=Image.open('map/sat_1400.png').convert('RGB'); W=S.size[0]; k=W/1400
X0,X1,Y0,Y1=-210,-40,120,340; sc=8
c=S.crop((int((X0+700)*k),int((700-Y1)*k),int((X1+700)*k),int((700-Y0)*k))).resize(((X1-X0)*sc,(Y1-Y0)*sc),Image.BICUBIC); d=ImageDraw.Draw(c)
for x in range(X0,X1+1,10): d.line([((x-X0)*sc,0),((x-X0)*sc,c.size[1])],fill=(255,255,0) if x%50==0 else (120,120,0)); d.text(((x-X0)*sc+2,2),str(x),fill=(255,255,0))
for y in range(Y0,Y1+1,10): d.line([(0,(Y1-y)*sc),(c.size[0],(Y1-y)*sc)],fill=(255,255,0) if y%50==0 else (120,120,0)); d.text((2,(Y1-y)*sc+2),str(y),fill=(255,255,0))
c.save('nb/grid.png'); print(S.size, c.size)
