exec(open('parts.py').read().split('# ---------- end arches')[0])
ANp=[(323,380),(337,330),(357,290),(383,253),(417,220),(450,210),(483,212),(517,223),(533,233)]
ASp=[(1473,377),(1467,350),(1457,310),(1440,263),(1413,223),(1367,198),(1303,213)]
C3=np.array(P[:3])
def onplane(u,v,a,b):
    # vertical plane through plan points a,b (local) -> world
    A=W(*a,0);B=W(*b,0);d=B-A;n=np.array([-d[1],d[0],0]);w=ray(P,u,v);t=((A-C3)@n)/(w@n);X=C3+t*w
    return np.round([(X[:2]-A[:2])@d[:2]/np.linalg.norm(d[:2]),X[2]],1)
for nm,a,b,px in (('N',NIL,FIL,ANp),('S',NIR,FIR,ASp)):
    print(nm,'span',np.linalg.norm(b-a).round(1),[tuple(onplane(u,v,a,b)) for u,v in px])
