from PIL import Image
O='out/peoplefirst/fence/'
S=Image.new('RGB',(1920,540))
for i,f in enumerate(['fence_270','fence_315']): S.paste(Image.open(O+f+'.png').convert('RGB'),(960*i,0))
S.save(O+'zoom_56.jpg',quality=92)
