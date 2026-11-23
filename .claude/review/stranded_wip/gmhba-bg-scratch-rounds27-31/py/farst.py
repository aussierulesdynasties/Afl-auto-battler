import numpy as np,sys
f=np.load(sys.argv[1]); m=f.shape[0]; print(f.shape,f.min(),f.max())
for th in (-1,0,0.5,1,2): print(th,(f<=th).mean())
c=m//2; s=f[c:c+40:4, c-20:c+20:4]; print(np.round(s).astype(int))
