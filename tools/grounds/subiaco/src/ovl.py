import sys,numpy as np
from PIL import Image,ImageFilter
ph,rn,out=sys.argv[1:4]
P=Image.open(ph).convert('RGB');R=Image.open(rn).convert('RGBA').resize(P.size)
a=np.array(R)[:,:,3]>0;g=np.array(R.convert('L'))
e=np.array(Image.fromarray(g).filter(ImageFilter.FIND_EDGES))>25
A=np.array(P).astype(float)
A[a]=A[a]*0.55+np.array(R)[:,:,:3][a]*0.45
A[e]=[255,0,255]
Image.fromarray(A.astype(np.uint8)).save(out)
