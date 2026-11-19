# python work/geortho.py view z out : GE top-down view resampled to the Esri frame (0.25 m/px, 1600 px, origin at 800,800) on the plane z
import sys,json,cv2,numpy as np;sys.path.insert(0,'work');import tri as T
v,z,out=sys.argv[1],float(sys.argv[2]),sys.argv[3];c=T.camv(v);im=cv2.imread(f'ge/{v}.png')
xs=-200+(np.arange(1600)+0.5)*0.25;X,Y=np.meshgrid(xs,xs[::-1])
d=np.stack([X-c['C'][0],Y-c['C'][1],np.full_like(X,z-c['C'][2])],-1);zz=d@c['fwd']
u=c['W']/2+c['f']*(d@c['right'])/zz;w=c['H']/2-c['f']*(d@c['up'])/zz
cv2.imwrite(out,cv2.remap(im,u.astype(np.float32),w.astype(np.float32),cv2.INTER_LINEAR))
