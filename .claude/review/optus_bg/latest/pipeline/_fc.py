from PIL import Image
a=Image.open('data/optus/sat.png'); a.crop((2300,2300,3700,3700)).resize((1000,1000)).save('_fc_sat.png')
g=Image.open('out/optus/prep_ground_dbg.png') if False else Image.open('data/optus/prep/ground.png')
g.crop((767,767,1233,1233)).resize((1000,1000),Image.NEAREST).save('_fc_gnd.png')
