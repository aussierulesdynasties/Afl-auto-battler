import math,numpy as np
exec(open('nearsolve.py').read().split('# model')[0])
N=np.load('nearsolve.npy');ang,out,sm,sat=N
for x,yf in ((740,949),(760,954),(780,958),(800,962),(820,966)):
    best=(1e9,)
    for a in np.arange(155,185,0.05):
        t=math.radians(a)
        for r in np.arange(70,115,0.1):
            P=proj([(r*math.cos(t)+SH[0],r*math.sin(t)+SH[1],10.6)])[0]
            d=math.hypot(P[0]-x,P[1]-yf)
            if d<best[0]:best=(d,a,r)
    i=np.argmin(abs(ang-best[1]))
    print('photo x%d foot y%d -> deck-level wall foot at angle %.1f r %.1f (satellite edge %.1f, photo roof edge %.1f): set back %.1f m from roof edge'%(x,yf,best[1],best[2],sat[i],sm[i],sm[i]-best[2]))
