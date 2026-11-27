# ocr.py DIR PTS.json OUT.json : read each status-bar strip (lat/lon/height under the mouse) -> [x,y,lat,lon,h]
import sys,glob,json,re,subprocess,os
d,pf,out=sys.argv[1:4];pts=json.load(open(pf));res=[]
rx=re.compile(r"(\d+)°(\d+)'([\d.]+)\"S\s*(\d+)°(\d+)'([\d.]+)\"E\s*(-?\d+)\s*m")
for i,p in enumerate(pts):
    f='%s/r%05d.png'%(d,i)
    if not os.path.exists(f): break
    subprocess.run(['convert',f,'-resize','400%','-colorspace','gray','/tmp/ocr_x.png'])
    t=subprocess.run(['tesseract','/tmp/ocr_x.png','-','--psm','7'],capture_output=True,text=True).stdout
    m=rx.search(t.replace(' ',''))
    if m:
        g=[float(x) for x in m.groups()];res.append(p+[-(g[0]+g[1]/60+g[2]/3600),g[3]+g[4]/60+g[5]/3600,g[6]])
    else: res.append(p+[None,None,None])
json.dump(res,open(out,'w'));print(len(res),sum(r[2] is None for r in res),'unread')
