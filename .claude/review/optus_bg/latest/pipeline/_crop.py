from PIL import Image; import glob
fs=sorted(glob.glob('orbit_frames/f_*.png'))
for i in range(0,len(fs),30):
    Image.open(fs[i]).convert('RGB').save('z_%d.jpg'%(i+1),quality=90)
print(len(fs))
