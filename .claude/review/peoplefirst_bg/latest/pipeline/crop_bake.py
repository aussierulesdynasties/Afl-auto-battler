from PIL import Image
Image.MAX_IMAGE_PIXELS=None
g=Image.open('data/peoplefirst/prep/ground_baked.png')
g.crop((3000,4600,5400,6400)).resize((1200,900)).save('ck_bake_a.png')
g.crop((4200,5000,5000,5600)).save('ck_bake_b.png')
