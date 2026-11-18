import json,numpy as np,sys
from camlib import proj
from PIL import Image
cam=json.load(open('camB.json'))['p'];Z=json.load(open('zonedump.json'))
def lum(f):
    I=np.asarray(Image.open(f).convert('RGB')).astype(float);return I.mean(2)
ph,rn=lum('refs/c/17.jpg'),lum('renB2_k.png')
def peaks(L,rows,thr):
    A=np.array([r[0] for r in rows]);X=np.array([r[1:] for r in rows])
    q=proj(cam,X,500,300)
    v=np.array([L[int(round(y)),int(round(x))] for x,y in q[:,:2]])
    base=np.convolve(v,np.ones(41)/41,'same');ex=v-base;out=[]
    for i in range(3,len(A)-3):
        if ex[i]>thr and ex[i]==ex[i-3:i+4].max():out.append(round(float(A[i]),1))
    return out
for k,rows in Z.items():
    print(k,'P',peaks(ph,rows,22));print(k,'R',peaks(rn,rows,10))
