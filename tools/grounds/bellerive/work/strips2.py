# python work/strips.py b0 b1 r0 r1 out : polar strip, 2 m thin / 10 m bold grid, 1 deg ticks, labels after scaling (6 px per 0.5 deg row, 8 px per m)
import sys,cv2,numpy as np
U=np.load(sys.argv[6] if len(sys.argv)>6 else 'work/unwrap.npy');b0,b1,r0,r1=map(float,sys.argv[1:5])
i0,i1=int(b0*2),int(b1*2);j0,j1=int((r0-50)*4),int((r1-50)*4)
S=np.concatenate([U,U])[i0:i1,j0:j1];S=cv2.resize(S,(S.shape[1]*2,S.shape[0]*6),interpolation=cv2.INTER_CUBIC)
for r in np.arange(np.ceil(r0/2)*2,r1,2):
  x=int((r-r0)*8);S[:,x]=S[:,x]//2+(0,127,127) if r%10 else (0,255,255)
  if r%10==0:cv2.putText(S,str(int(r)),(x+2,12),0,0.45,(0,255,255),1)
for b in np.arange(np.ceil(b0),b1,1):
  y=int((b-b0)*12);S[y,:]=S[y,:]//2+(127,0,127) if b%5 else (255,0,255)
  if b%5==0:cv2.putText(S,str(int(b)%360),(2,y+14),0,0.45,(255,0,255),1)
cv2.imwrite(sys.argv[5],S)
