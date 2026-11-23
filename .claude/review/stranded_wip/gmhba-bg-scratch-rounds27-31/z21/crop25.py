import sys
from PIL import Image
im=Image.open('st30_2.png'); im.crop((600,0,1280,180)).resize((1360,360)).save('c30_cbd.png')
im.crop((0,0,640,90)).resize((1280,180)).save('c30_hor.png')
