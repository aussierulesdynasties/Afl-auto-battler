# Bench-slat period on the flight: 2D FFT peak in 32x32 patches, photo vs render. usage: python r2/period.py RENDER
import sys,numpy as np
from PIL import Image
def g(p):return np.asarray(Image.open(p).convert('L'),float)
P=g('prev/photo_full.png');R=g(sys.argv[1])
def pk(I,cx,cy,n=32):
    a=I[cy-n//2:cy+n//2,cx-n//2:cx+n//2];a=a-a.mean();a*=np.outer(np.hanning(n),np.hanning(n))
    F=np.abs(np.fft.fftshift(np.fft.fft2(a)));c=n//2;F[c-2:c+3,c-2:c+3]=0
    y,x=np.unravel_index(F.argmax(),F.shape);fy,fx=(y-c)/n,(x-c)/n;f=np.hypot(fx,fy)
    return 1/f,np.degrees(np.arctan2(fy,fx))
for cx,cy in ((1085,975),(1110,945),(1135,930)):
    pp,pa=pk(P,cx,cy);rp,ra=pk(R,cx,cy);print(f"({cx},{cy}) photo {pp:.2f}px {pa:.0f}deg  render {rp:.2f}px {ra:.0f}deg")
