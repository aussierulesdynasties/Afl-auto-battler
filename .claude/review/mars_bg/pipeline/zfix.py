from PIL import Image
O='out/peoplefirst/fence/'
for i,f in enumerate(['fence_225','fence_270']):
    im=Image.open(O+f+'.png').convert('RGB'); W,H=im.size; print(W,H)
    im.crop((W//2-480,H-540,W//2+480,H)).save(f'chk_f{i}.png')
a=Image.open('chk_f0.png'); a.save(O+'zoom_56.jpg',quality=92)
