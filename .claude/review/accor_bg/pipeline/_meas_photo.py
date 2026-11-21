import numpy as np; from PIL import Image
im=np.asarray(Image.open('review/accor_ref/Looking_down_Olympic_Boulevard_during_the_Sydney_Royal_Easter_Show.jpg').convert('RGB'),np.float32)
for k,(x,y) in {'red_sunlit':(1500,880),'red_sunlit2':(560,790),'charcoal_sunlit':(1450,1200),'charcoal_sunlit2':(1200,1350),'white_line':(870,1200)}.items():
    print(k,im[y-15:y+15,x-15:x+15].reshape(-1,3).mean(0).round())
