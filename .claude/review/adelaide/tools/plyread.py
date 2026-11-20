import numpy as np, re
def readply(fn, faces=False, cols=False):
    b=open(fn,'rb').read(); i=b.index(b'end_header')+11; hdr=b[:i].decode()
    nv=int(re.search(r'element vertex (\d+)',hdr).group(1)); nf=int(re.search(r'element face (\d+)',hdr).group(1))
    L=b[i:].decode().split('\n')
    A=np.array([l.split() for l in L[:nv]],float); V=A[:,:3]
    out=[V]
    if faces:
        F=[list(map(int,l.split()[1:])) for l in L[nv:nv+nf]]
        T=[]
        for f in F:
            for k in range(1,len(f)-1): T.append([f[0],f[k],f[k+1]])
        out.append(np.array(T))
    if cols: out.append(A[:,3:])
    return out if len(out)>1 else V
