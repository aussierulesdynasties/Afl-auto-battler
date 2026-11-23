from PIL import Image
# same window in both: ground 1.5 m/px, sat 0.5 m/px
x0,y0,x1,y1=1080,880,1280,1060
Image.open('data/optus/prep/ground.png').crop((x0,y0,x1,y1)).resize((800,720),Image.NEAREST).save('_fc_g2.png')
Image.open('data/optus/sat.png').crop((x0*3,y0*3,x1*3,y1*3)).resize((800,720)).save('_fc_s2.png')
