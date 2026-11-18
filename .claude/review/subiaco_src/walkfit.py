exec(open('wsolve.py').read().split("for x,y,h in JB")[0])
LN=json.load(open('nslines.json'))
def dline(a,k):
    (px,py),(ux,uy)=LN[k];t=math.radians(a);ex,ey=math.cos(t),math.sin(t);px-=C0[0];py-=C0[1]
    return (px*uy-py*ux)/(ex*uy-ey*ux)-rf(a)
rkm=lambda a:(bfz(a)-2.4)/(bfd(a)-0.8)
Z1C=1.2+(dline(95,'d1f')-fo(95)-0.9)*rkm(95);print('Z1C',round(Z1C,2))
from PIL import Image
L=np.asarray(Image.open('refs/c/17.jpg').convert('L')).astype(float)
p0=np.array([697.,182.]);p1=np.array([865.,320.]);u=(p1-p0)/np.linalg.norm(p1-p0);n=np.array([u[1],-u[0]])
def s(p):
    x,y=p;x0,y0=int(x),int(y);fx,fy=x-x0,y-y0
    return L[y0,x0]*(1-fx)*(1-fy)+L[y0,x0+1]*fx*(1-fy)+L[y0+1,x0]*(1-fx)*fy+L[y0+1,x0+1]*fx*fy
F,B=[],[]
for t in range(0,205,5):
    q=p0+u*t;O=np.arange(-50,5,0.5);v=np.array([s(q+n*o) for o in O]);br=v>150
    # roof start: first o where the next 10 px are all bright
    i=next((k for k in range(len(O)-20) if br[k:k+20].all() and O[k]>-36),None)
    if i is None:continue
    j=i-1
    while j>0 and not br[j]:j-=1          # end of walkway
    k=j
    while k>0 and br[k]:k-=1              # start of walkway
    if not(4<=(O[j]-O[k])<=12):continue
    F.append(onz(q+n*(O[k]+0.5),Z1C));B.append(onz(q+n*(O[j]+0.5),Z1C))
    a,d=toPolar(F[-1]);a2,d2=toPolar(B[-1])
    print(t,'walk o %.1f..%.1f  roof %.1f'%(O[k],O[j],O[i]),' a %.1f d1f %.2f (line %.2f)  d1b %.2f (line %.2f)'%(a,d,dline(a,'d1f'),d2,dline(a2,'d1b')))
u2=np.array(LN['dRF'][1]);nr=np.array([-u2[1],u2[0]])
for k,Pp in (('d1f',F),('d1b',B)):
    off=np.mean([p[:2]@nr for p in Pp]);res=[p[:2]@nr-off for p in Pp];print(k,'rms %.2f'%np.sqrt(np.mean(np.square(res))));LN[k]=((nr*off).tolist(),u2.tolist())
json.dump(LN,open('nslines2.json','w'))
