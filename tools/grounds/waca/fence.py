import numpy as np
# real boundary traced on the 2015 satellite (metres)
PTS=[(108,0),(107,25),(101,48),(80,62),(50,67),(0,72),(-50,61.7),(-70,52),(-82,40),(-89,25),(-90.5,0),(-86,-25),(-75,-38),(-50,-59.5),(0,-69.2),(50,-62),(75,-49),(90,-33),(104,-15)]
def dense(n=400):
    P=np.array(PTS+[PTS[0]],float);c=P.mean(0)
    # periodic Catmull-Rom
    Q=np.array(PTS,float);N=len(Q);out=[]
    for i in range(N):
        p0,p1,p2,p3=Q[i-1],Q[i],Q[(i+1)%N],Q[(i+2)%N]
        for t in np.linspace(0,1,n//N,endpoint=False):
            out.append(0.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t**3))
    return np.array(out)
