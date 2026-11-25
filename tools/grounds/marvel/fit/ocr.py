import sys,glob,re,json,subprocess,os
from PIL import Image,ImageOps
d=sys.argv[1];res={}
def dms(s):
    m=re.findall(r'\d+(?:\.\d+)?',s)
    return m
for f in sorted(glob.glob(d+'/p_*.png')):
    x,y=map(int,os.path.basename(f)[2:-4].split('_'))
    im=Image.open(f).convert('L');im=im.resize((im.width*4,im.height*4),Image.LANCZOS);ImageOps.invert(im).save('/tmp/claude-0/obl/_o.png')
    t=subprocess.run(['tesseract','/tmp/claude-0/obl/_o.png','-','--psm','7'],capture_output=True,text=True).stdout.strip()
    m=re.search(r'(\d+)\D+(\d+)\D+(\d+\.\d+)\D*S\s+(\d+)\D+(\d+)\D+(\d+\.\d+)\D*E\s+(-?\d+)\s*m',t)
    if not m: res[f'{x},{y}']=None;continue
    a=list(map(float,m.groups()))
    lat=-(a[0]+a[1]/60+a[2]/3600);lon=a[3]+a[4]/60+a[5]/3600
    res[f'{x},{y}']=(lat,lon,a[6],t)
json.dump(res,open(d+'/picks.json','w'),indent=0)
print(sum(v is not None for v in res.values()),len(res))
