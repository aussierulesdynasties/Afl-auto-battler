import cv2,numpy as np,sys
r=cv2.imread(sys.argv[1],cv2.IMREAD_UNCHANGED);ph=cv2.imread('photo.png')
a=r[:,:,3:4]/255.0;comp=(r[:,:,:3]*a+ph*(1-a)).astype(np.uint8)
ov=cv2.addWeighted(ph,0.5,comp,0.5,0)
# edges of render in red
e=cv2.Canny(cv2.cvtColor(comp,cv2.COLOR_BGR2GRAY),60,140);ov2=ph.copy();ov2[e>0]=(0,0,255)
cv2.imwrite(sys.argv[2]+'_blend.jpg',cv2.resize(ov,(1400,933)));cv2.imwrite(sys.argv[2]+'_edge.jpg',cv2.resize(ov2,(1400,933)));cv2.imwrite(sys.argv[2]+'_comp.jpg',cv2.resize(comp,(1400,933)))
