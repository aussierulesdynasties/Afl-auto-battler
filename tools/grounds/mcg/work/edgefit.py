# python work/edgefit.py idrender.png : per bearing, model roof-inner / outer edges vs strongest satellite edge nearby (metres)
import sys,cv2,numpy as np,hashlib
S=cv2.cvtColor(cv2.imread('sat/esri_025.png'),cv2.COLOR_BGR2GRAY).astype(float);S=cv2.GaussianBlur(S,(5,5),1.2)
r=cv2.imread(sys.argv[1],cv2.IMREAD_UNCHANGED)
def idc(n):h=hashlib.md5(n.encode()).digest();return np.array([h[2],h[1],h[0]])
roofm=[idc(n) for n in ('roof_white','roof_grey','roof_teal','roof_clear_w','roof_fascia','fascia')]
rs=np.arange(60,200,0.25)
def samp(img,b,interp=cv2.INTER_LINEAR):
    B=np.radians(b);X=((rs*np.sin(B)+260)*4).astype(np.float32);Y=((260-rs*np.cos(B))*4).astype(np.float32)
    return cv2.remap(img,X[None],Y[None],interp)[0]
rows=[]
for b in np.arange(0,360,2.0):
    c=samp(r,b,cv2.INTER_NEAREST);al=c[:,3]>128;col=c[:,:3].astype(int)
    isroof=np.zeros(len(rs),bool)
    for m in roofm:isroof|=np.abs(col-m).sum(1)<12
    if not al.any():continue
    i_out=np.where(al)[0].max();ir=np.where(isroof)[0]
    s=samp(S,b);g=np.gradient(s)
    def best(i,w,sign):
        lo,hi=max(i-int(w*4),1),min(i+int(w*4),len(rs)-2);gg=g[lo:hi]*sign if sign else np.abs(g[lo:hi]);j=lo+int(np.argmax(gg));return rs[j],gg.max()
    so,go=best(i_out,8,0)
    if len(ir):
        i_in=ir.min();si,gi=best(i_in,8,-1)  # going outward: dark seats/shadow -> bright roof = +grad; we look for +grad: sign -1? see below
        si2,gi2=best(i_in,8,1);si,gi=(si2,gi2)
        rows.append((b,rs[i_out],so,so-rs[i_out],rs[i_in],si,si-rs[i_in]))
    else: rows.append((b,rs[i_out],so,so-rs[i_out],np.nan,np.nan,np.nan))
print(' brg  out_m out_s  d_out | rin_m rin_s  d_in')
for t in rows:print('%5.0f %6.1f %6.1f %5.1f | %6.1f %6.1f %5.1f'%t)
