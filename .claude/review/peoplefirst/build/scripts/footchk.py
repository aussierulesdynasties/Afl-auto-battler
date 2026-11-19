import math,numpy as np
exec(open('nearsolve.py').read().split('# model')[0])
N=np.load('nearsolve.npy');ang,out,sm,sat=N
for a in (163,165.4,167.6,169.8,172,176,180):
    i=np.argmin(abs(ang-a));t=math.radians(a)
    row=[a,sat[i],sm[i]]
    for r in (sat[i],sm[i]):
        for z in (10.6,):
            P=proj([(r*math.cos(t)+SH[0],r*math.sin(t)+SH[1],z)]);row+=[P[0,0],P[0,1]]
    print('a %.1f sat r %.1f photo r %.1f | deck-foot at sat r: x%.0f y%.0f | at photo r: x%.0f y%.0f'%tuple(row))
