from PIL import Image; import glob,os
os.makedirs('deliver',exist_ok=True)
f=sorted(glob.glob('video/orbit_frames/*.png')); sel=f[::30]
for i,p in enumerate(sel): Image.open(p).convert('RGB').save('deliver/orbit_f%03d.jpg'%(i*30),quality=92)
W,H=640,360; S=Image.new('RGB',(W*4,H*2))
for i,p in enumerate(sel): S.paste(Image.open(p).convert('RGB').resize((W,H)),((i%4)*W,(i//4)*H))
S.save('deliver/ring_sheet.jpg',quality=90); print(len(sel))
