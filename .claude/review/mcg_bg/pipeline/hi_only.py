"""re-run only the hi layer on the cached pre-hi bake (iteration aid)"""
import os,sys,json,numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
H=os.path.dirname(os.path.abspath(__file__)); D=os.path.join(H,'data','mcg','prep'); NE=json.load(open(os.path.join(D,'meta.json')))['near']
out=np.array(Image.open(os.path.join(D,'ground_prehi.png')).convert('RGB')); sys.path.insert(0,H); import hilayer; hilayer.paint(out,NE)
Image.fromarray(out).save(os.path.join(D,'ground_baked.png')); print('ok')
