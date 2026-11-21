from PIL import Image
import numpy as np
for n in ('seat_up','seat_low'):
    a=np.asarray(Image.open('seatimg_%s.png'%n).convert('RGB')).astype(float); L=a.mean(2)
    print(n, a.shape, 'light share', round((L>170).mean(),2), 'mean', a.reshape(-1,3).mean(0).round())
    Image.open('seatimg_%s.png'%n).resize((a.shape[1]*3,a.shape[0]*3),Image.NEAREST).save('seatimg_%s_x3.png'%n)
