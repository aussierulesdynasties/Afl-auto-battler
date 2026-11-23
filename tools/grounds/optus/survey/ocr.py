import re,subprocess,sys,glob,os
from PIL import Image
def dms(d,m,s,h):v=float(d)+float(m)/60+float(s)/3600;return -v if h in 'SW' else v
def read(path):
    im=Image.open(path).convert('L');big=path[:-4]+'_x.png'
    im.resize((im.width*4,im.height*4),Image.LANCZOS).save(big)
    t=subprocess.run(['tesseract',big,'-','--psm','7'],capture_output=True,text=True,env=dict(os.environ,OMP_THREAD_LIMIT='1')).stdout;os.remove(big)
    m=re.search(r"(\d+)\D+(\d+)'\s*([\d.]+)\"?\s*([NS])\s+(\d+)\D+(\d+)'\s*([\d.]+)\"?\s*([EW])\s+(-?[\d,.]+)\s*m",t)
    if not m:return None,t.strip()
    g=m.groups();return (dms(*g[0:4]),dms(*g[4:8]),float(g[8].replace(',',''))),t.strip()
