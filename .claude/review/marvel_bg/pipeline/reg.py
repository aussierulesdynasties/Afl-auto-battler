import sys,numpy as np
from PIL import Image
T=np.asarray(Image.open(sys.argv[1]).convert('L'),np.float32);S=np.asarray(Image.open(sys.argv[2]).convert('L').resize(T.shape[::-1]),np.float32)
mpp=float(sys.argv[3])
def E(a):gy,gx=np.gradient(a);return np.hypot(gx,gy)
T,S=E(T),E(S);n=T.shape[0];k=n//4
for j in range(4):
  row=[]
  for i in range(4):
    a=T[j*k:(j+1)*k,i*k:(i+1)*k];b=S[j*k:(j+1)*k,i*k:(i+1)*k]
    a=a-a.mean();b=b-b.mean();F=np.fft.fft2(a)*np.conj(np.fft.fft2(b));F/=np.abs(F)+1e-6
    c=np.real(np.fft.ifft2(F));y,x=np.unravel_index(c.argmax(),c.shape)
    y=y-k if y>k//2 else y;x=x-k if x>k//2 else x
    row.append('(%+.1f,%+.1f) pk%.2f'%(x*mpp,-y*mpp,c.max()))
  print(' '.join(row))
