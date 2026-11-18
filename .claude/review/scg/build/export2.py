# multi-photo projection: every face takes the photo that sees it most squarely with the most pixels; ID-buffer occlusion per photo
exec(open('geo.py').read())
import cv2
exec(open('zbuf.py').read())
from PIL import Image,ImageDraw
CAMS=[('cam.json','refs/scg.jpg'),('cam16.json','refs4/016.jpg'),('cam63.json','refs3/063.jpg')]
Va=np.array(V,float);SC=2;best=[None]*len(F);score=np.zeros(len(F))
for ci,(cj,ip) in enumerate(CAMS):
    q=json.load(open(cj))['p'];Cc=np.array(q[:3]);Mc=R(*q[3:6]);f_,cx_,cy_=q[6],q[7],q[8]
    ph=cv2.imread(ip);Hh,Ww=ph.shape[:2]
    CM={1:'col16.npy',2:'col63.npy'}                     # grade each extra photo to the reference photo's colours
    if ci in CM:M_=np.load(CM[ci]);ph=np.clip(np.c_[ph.reshape(-1,3).astype(float),np.ones(Hh*Ww)]@M_,0,255).reshape(ph.shape).astype(np.uint8)
    d=(Va-Cc)@Mc.T;front=d[:,2]>1;uv=np.stack([cx_+f_*d[:,0]/np.maximum(d[:,2],1e-3),cy_-f_*d[:,1]/np.maximum(d[:,2],1e-3)],1)
    ID=zbuffer(uv*SC,d[:,2],[idx for idx,m in F],Ww*SC,Hh*SC,skip=[False]*len(F));cnt=np.bincount(ID[ID>=0].ravel(),minlength=len(F))
    tm=np.isin(ID,[i for i,(idx,m) in enumerate(F) if m in('tower','lamp','headback')]).astype(np.uint8)*255
    tm=tm.reshape(Hh,SC,Ww,SC).max(axis=(1,3)).astype(np.uint8);tm=cv2.dilate(tm,np.ones((13,13),np.uint8))
    cv2.imwrite('out/photo%d.png'%ci,cv2.inpaint(ph,tm,5,cv2.INPAINT_TELEA));cv2.imwrite('out/photo%d.png'%(ci+len(CAMS)),ph)
    for i,(idx,m) in enumerate(F):
        ang=math.degrees(math.atan2(Va[list(idx)][:,1].mean()-PC[1],Va[list(idx)][:,0].mean()-PC[0]))%360
        nearroof=m in('roof','fascia','roofu') and 168<=ang<=256
        if ci==1 and not(NEAR0<=i<NEAR1 or nearroof):continue
        if ci==2 and not(30<=ang<=120):continue
        if ci==0 and NEAR0<=i<NEAR1:continue           # the reference photo never sees the near facade          # the 2012 photo only for the near stand's facade (unchanged since 2008)
        pts=Va[list(idx)];n=np.cross(pts[1]-pts[0],pts[2]-pts[0]);nn=np.linalg.norm(n)
        if nn<1e-9 or not all(front[j] for j in idx):continue
        n/=nn;view=Cc-pts.mean(0);view/=np.linalg.norm(view);c=abs(n@view)
        qq=uv[list(idx)]*SC;area=0.5*abs(np.dot(qq[:,0],np.roll(qq[:,1],1))-np.dot(qq[:,1],np.roll(qq[:,0],1)))
        if not(cnt[i]>=6 and cnt[i]>=0.5*area and c>0.3):continue
        wa=nn*(0.5 if len(idx)==3 else 1.0)
        sc_=c*math.sqrt(area/SC/SC/max(wa,1e-6))           # obliqueness x pixels per metre
        if ci==0:sc_+=1000                                  # the reference photo wins wherever it sees the face
        if ci==2 and m=='grass':continue                   # 063 was shot during a baseball event
        raw=m in('tower','lamp','headback')
        if sc_>score[i]:score[i]=sc_;best[i]=(ci+(len(CAMS) if raw else 0),[[float(uv[j,0]/Ww),float(1-uv[j,1]/Hh)] for j in idx])
# faces no photo sees: borrow the photo patch of the nearest seen face of the same part (same material, same shape)
from scipy.spatial import cKDTree
cen=np.array([Va[list(idx)].mean(0) for idx,m in F]);borrow=0
for mm in set(m for idx,m in F):
    for nv in (3,4):
        S_=[i for i,(idx,m) in enumerate(F) if m==mm and len(idx)==nv and best[i]];U_=[i for i,(idx,m) in enumerate(F) if m==mm and len(idx)==nv and not best[i]]
        if not S_ or not U_:continue
        _,nb=cKDTree(cen[S_]).query(cen[U_])
        for u,k in zip(U_,nb):best[u]=best[S_[k]];borrow+=1
print('borrowed',borrow)
faces=[{'v':list(idx),'m':m,'ph':best[i][0] if best[i] else None,'uv':best[i][1] if best[i] else None} for i,(idx,m) in enumerate(F)]
json.dump({'V':V,'F':faces,'MATS':MATS,'NPH':2*len(CAMS)},open('scg_mesh.json','w'))
print('faces',len(F),'near',NEAR1-NEAR0,'per photo',[sum(f['ph']==k for f in faces) for k in range(len(CAMS))],'flat',sum(f['ph'] is None for f in faces))
