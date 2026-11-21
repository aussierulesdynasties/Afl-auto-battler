# z luminance profile of the photo elevation (work/pp<b>.png: x = bearing at 20 px/deg from b, y = z 45..0 at 8 px/m)
import sys,numpy as np
from PIL import Image
for spec in sys.argv[1:]:
    b0,b1=map(float,spec.split(':'));base=int(b0//60*60)
    a=np.asarray(Image.open(f'work/pp{base}.png').convert('RGB'),float)[:360]
    x0,x1=int((b0-base)*20),int((b1-base)*20);s=a[:,x0:x1].mean(1);L=s.mean(1)
    print(spec, 'z: L (r,g,b) every 0.5 m, 0..26')
    for z in np.arange(0,26,0.5):
        y=int((45-z)*8);v=s[y-2:y+2].mean(0);print(f'  {z:4.1f} {v.mean():5.0f} {v.astype(int)}')
