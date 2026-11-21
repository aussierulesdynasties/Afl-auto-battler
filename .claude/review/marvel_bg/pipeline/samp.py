import sys, numpy as np
from PIL import Image
a=np.asarray(Image.open(sys.argv[1]).convert('RGB'),float); b=np.asarray(Image.open(sys.argv[2]).convert('RGB'),float)
H=a.shape[0]; half=float(sys.argv[3])
for nm,x,y in [('E_block',290,0),('E_block2',250,-150),('NE_block',100,250),('W_block',-300,150),('S_block',150,-300)]:
    i=int((half-y)/(2*half)*H); j=int((x+half)/(2*half)*H); r=15
    pa=a[i-r:i+r,j-r:j+r].reshape(-1,3); pb=b[i-r:i+r,j-r:j+r].reshape(-1,3)
    print(nm,'sat',pa.mean(0).round(),'grey sd',round(pa.mean(1).std(),1),'| ours',pb.mean(0).round())
