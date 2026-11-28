# Colour check: median RGB of the same surface in the photo panel and the model panel of a Gorringe board (panel coords).
import numpy as np,sys
from PIL import Image
def pan(n,k):
    im=Image.open(f'../../../.claude/review/north_hobart/boards/gorringe_{n}.png').convert('RGB');W,H=im.size;w=(W-20)//3;return im.crop((k*(w+10),40,k*(w+10)+w,H))
S={'roof_iron':('se_end',(340,110,440,190)),'seats':('se_end',(280,432,430,490)),'brick':('se_end',(220,565,300,610)),'render_cream':('se_end',(182,530,198,630))}
if __name__=='__main__':
    for k,(n,b) in S.items():
        p=np.median(np.asarray(pan(n,0).crop(b)).reshape(-1,3),0);m=np.median(np.asarray(pan(n,1).crop(b)).reshape(-1,3),0)
        print(f'{k:13s} photo {tuple(int(v) for v in p)} model {tuple(int(v) for v in m)}')
