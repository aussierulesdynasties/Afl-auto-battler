# ID-buffer visibility, tower-free photo, mesh + UV export for Blender
exec(open('geo.py').read())
import cv2
from PIL import Image,ImageDraw
SC=2;Va=np.array(V,float);d=(Va-C)@M.T;uv=np.stack([cx0+fo*d[:,0]/d[:,2],cy0-fo*d[:,1]/d[:,2]],1)
order=sorted(range(len(F)),key=lambda i:-np.mean([d[j,2] for j in F[i][0]]))
idimg=Image.new('I',(W*SC,H*SC),0);dr=ImageDraw.Draw(idimg)
for i in order:
    idx,m=F[i];dr.polygon([tuple(uv[j]*SC) for j in idx],fill=i+1)
ID=np.array(idimg).astype(np.int64)-1
cnt=np.bincount(ID[ID>=0].ravel(),minlength=len(F))
ph=cv2.imread('refs/scg.jpg')
tmask=np.isin(ID,[i for i,(idx,m) in enumerate(F) if m in('tower','lamp','headback')]).astype(np.uint8)*255
tmask=tmask.reshape(H,SC,W,SC).max(axis=(1,3)).astype(np.uint8)
tmask=cv2.dilate(tmask,np.ones((13,13),np.uint8))
clean=cv2.inpaint(ph,tmask,5,cv2.INPAINT_TELEA);cv2.imwrite('g/scg_clean.png',clean)
faces=[]
for i,(idx,m) in enumerate(F):
    pts=Va[list(idx)];n=np.cross(pts[1]-pts[0],pts[2]-pts[0]);nn=np.linalg.norm(n)
    vis=False
    if nn>1e-9 and m not in('tower','lamp','headback','grass'):
        n/=nn;view=(C-pts.mean(0));view/=np.linalg.norm(view)
        q=uv[list(idx)]*SC;area=0.5*abs(np.dot(q[:,0],np.roll(q[:,1],1))-np.dot(q[:,1],np.roll(q[:,0],1)))
        vis=cnt[i]>=6 and cnt[i]>=0.5*area and abs(n@view)>0.3   # only faces the photo mostly sees
    faces.append({'v':list(idx),'m':m,'uv':[[float(uv[j,0]/W),float(1-uv[j,1]/H)] for j in idx] if vis else None})
json.dump({'V':V,'F':faces,'MATS':MATS},open('scg_mesh.json','w'))
print('faces',len(F),'photo faces',sum(f['uv'] is not None for f in faces))
