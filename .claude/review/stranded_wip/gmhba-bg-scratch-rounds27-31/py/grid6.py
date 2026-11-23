import sys
from PIL import Image
d=sys.argv[1]; fs=[61,91,121,151,181,211]; W=Image.new('RGB',(1280*2,720*3))
for k,f in enumerate(fs): W.paste(Image.open(d+'/f_%04d.png'%f),((k%2)*1280,(k//2)*720))
W.save(d+'/grid6.png')
