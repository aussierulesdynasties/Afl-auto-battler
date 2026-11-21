import sys,os,numpy as np
from PIL import Image
d=sys.argv[1]; fs=sorted(f for f in os.listdir(d) if f.endswith('.png'))
P=None; D=[]
for f in fs:
    A=np.asarray(Image.open(os.path.join(d,f)).convert('L').resize((320,180)),dtype=float)
    if P is not None: D.append(np.abs(A-P).mean())
    P=A
D=np.array(D); m=np.median(D)
print('frames',len(fs),'median diff %.2f max %.2f'%(m,D.max()))
print('outliers >2x median:',[(i+1,round(x,2)) for i,x in enumerate(D) if x>2*m])
