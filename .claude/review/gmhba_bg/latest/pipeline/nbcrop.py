from PIL import Image
S=Image.open('map/sat_600.png').convert('RGB'); W=S.size[0]; k=W/600
cx,cy=-133.53,231.8; x0=(cx-70+300)*k; y0=(300-(cy+70))*k
c=S.crop((int(x0),int(y0),int(x0+140*k),int(y0+140*k))).resize((1400,1400),Image.LANCZOS); c.save('nb/sat_nb.png'); print(S.size)
