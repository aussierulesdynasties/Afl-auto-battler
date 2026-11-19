# Texture proof: each hand-made texture tile beside the photo crop it copies (photo = reference only).
import cv2,numpy as np,os
ph=cv2.imread('photo_clean.png')
B={'roof':(1000,880,1100,930),'navy':(990,848,1070,868),'seat_up':(850,450,950,510),'seat_low':(700,560,800,600),
'aisle_up':(930,455,990,515),'led':(950,516,1000,531),'grass':(900,650,1000,750),'podroof':(720,1000,850,1060),
'stripes':(620,1010,720,1080),'dark':(540,900,640,960),'red':(740,928,830,962),'redsign':(918,962,982,1012),
'yellow':(1140,955,1210,1030),'tower':(655,790,690,900),'lamps':(635,690,712,742),'scorefront':(425,515,515,625),
'concrete':(420,640,500,700),'walk':(880,510,940,518),'white':(1420,850,1500,900),'fencelow':(885,552,935,560),
'roofunder':(1120,945,1230,985)}
rows=[];H=200
for k,b in B.items():
    t=cv2.imread(f'htex/{k}.png')
    if t is None:continue
    x0,y0,x1,y1=b;c=ph[y0:y1,x0:x1]
    tt=cv2.resize(t,(int(t.shape[1]*H/t.shape[0]),H),interpolation=cv2.INTER_AREA)[:, :400]
    cc=cv2.resize(c,(int(c.shape[1]*H/c.shape[0]),H),interpolation=cv2.INTER_NEAREST)[:, :400]
    r=np.full((H,840,3),40,np.uint8);r[:,:tt.shape[1]]=tt;r[:,440:440+cc.shape[1]]=cc
    cv2.rectangle(r,(0,0),(300,26),(0,0,0),-1);cv2.putText(r,f'{k}: hand-made | photo {x0},{y0}',(4,19),0,0.55,(255,255,255),1);rows.append(r)
h=len(rows)//2+len(rows)%2;L=rows[:h];R=rows[h:]+[np.full((H,840,3),40,np.uint8)]*(h-len(rows[h:]))
cv2.imwrite('z_texboard.jpg',np.hstack([np.vstack(L),np.full((H*h,10,3),255,np.uint8),np.vstack(R)]),[cv2.IMWRITE_JPEG_QUALITY,90])
print(len(rows))
