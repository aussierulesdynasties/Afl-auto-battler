# true z-buffer face-ID raster (replaces painter's order): ID[y,x] = nearest face index or -1
import numpy as np
def zbuffer(uv,depth,faces,W,H,skip=None):
    ID=np.full((H,W),-1,np.int64);Z=np.full((H,W),np.inf)
    for fi,idx in enumerate(faces):
        if skip is not None and skip[fi]:continue
        for k in range(1,len(idx)-1):
            t=(idx[0],idx[k],idx[k+1]);dz=depth[list(t)]
            if (dz<=0.5).any():continue
            P=uv[list(t)];x0=max(int(np.floor(P[:,0].min())),0);x1=min(int(np.ceil(P[:,0].max())),W-1)
            y0=max(int(np.floor(P[:,1].min())),0);y1=min(int(np.ceil(P[:,1].max())),H-1)
            if x1<x0 or y1<y0:continue
            xs,ys=np.meshgrid(np.arange(x0,x1+1)+0.5,np.arange(y0,y1+1)+0.5)
            (ax,ay),(bx,by),(cx,cy)=P;den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
            if abs(den)<1e-9:continue
            l0=((by-cy)*(xs-cx)+(cx-bx)*(ys-cy))/den;l1=((cy-ay)*(xs-cx)+(ax-cx)*(ys-cy))/den;l2=1-l0-l1
            ins=(l0>=-1e-6)&(l1>=-1e-6)&(l2>=-1e-6)
            if not ins.any():continue
            iz=l0/dz[0]+l1/dz[1]+l2/dz[2];z=np.where(ins,1/np.maximum(iz,1e-9),np.inf)
            sub=Z[y0:y1+1,x0:x1+1];better=z<sub-0.02
            sub[better]=z[better];ID[y0:y1+1,x0:x1+1][better]=fi
    return ID
