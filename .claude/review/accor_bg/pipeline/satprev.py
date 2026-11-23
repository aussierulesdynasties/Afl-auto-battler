from PIL import Image
Image.MAX_IMAGE_PIXELS=None
im=Image.open('data/accor/sat.png'); im.resize((1500,1500)).save('out/accor/sat_full.jpg',quality=85)
c=im.crop((2000,2000,4000,4000)).resize((1400,1400)); c.save('out/accor/sat_1km.jpg',quality=85)
