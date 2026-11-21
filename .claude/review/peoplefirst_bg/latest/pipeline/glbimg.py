import json,struct,sys,io
from PIL import Image
b=open(sys.argv[1],'rb').read(); n=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+n]); bin_=b[20+n+8:]
for m in j['materials']: print('mat',m['name'],m.get('pbrMetallicRoughness',{}).get('baseColorTexture'))
for i,im in enumerate(j['images']):
    bv=j['bufferViews'][im['bufferView']]; d=bin_[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]
    I=Image.open(io.BytesIO(d)); print('img',i,im.get('name'),I.size)
    if im.get('name') in sys.argv[2:]: I.save('glb_'+im['name']+'.png')
