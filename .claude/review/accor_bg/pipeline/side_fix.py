from PIL import Image; import shutil
O='out/peoplefirst/photo/'
shutil.copy(O+'street3.png',O+'street.png')
s=Image.open(O+'p4_side.jpg'); n=Image.open(O+'p4.png').convert('RGB')
w,h=s.size; n=n.resize((w//2,h)); s.paste(n,(w//2,0)); s.save(O+'p4_side.jpg',quality=92)
im=Image.open(O+'street.png').convert('RGB'); W,H=im.size
for i,(a,b) in enumerate([(0,0),(W//2,0),(0,H//2),(W//2,H//2)]): im.crop((a,b,a+W//2,b+H//2)).save(f'chk_st{i}.png')
z=Image.open('out/peoplefirst/fence/zoom_56.jpg'); print(z.size, s.size, im.size)
