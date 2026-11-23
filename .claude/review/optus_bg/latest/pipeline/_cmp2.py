import numpy as np
from PIL import Image
from scipy import ndimage as ndi
fc=np.asarray(Image.open('data/optus/prep/forecourt.png')).astype(np.int16)
c=fc[:, 2440:3960]
q=(c[...,0]//6)*10000+(c[...,1]//6)*100+(c[...,2]//6)
L=c[...,:3].mean(2)
lab=np.select([c[...,0]-c[...,2]>40, L>175],[0,1],2)
lab=ndi.median_filter(lab,5)
ed=(ndi.grey_dilation(lab,5)!=ndi.grey_erosion(lab,5))&(c[...,3]>128)
s=np.asarray(Image.open('_fc_sat.png').convert('RGB').resize((c.shape[1],c.shape[0]))).copy()
s[ed]=(255,0,0)
bg=Image.new('RGBA',(c.shape[1],c.shape[0]),(40,90,40,255)); bg.alpha_composite(Image.fromarray(c.astype(np.uint8),'RGBA'))
Image.fromarray(np.hstack([s,np.asarray(bg.convert('RGB'))])).resize((1216,1016)).save('_fc_cmp2.png')
print('bands (salmon, beige, grey):',[ndi.label((lab==k)&(c[...,3]>128))[1] for k in range(3)])
