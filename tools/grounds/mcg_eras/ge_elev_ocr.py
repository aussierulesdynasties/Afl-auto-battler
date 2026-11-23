# Reads the Google Earth status-bar crops (lat, lon, elevation) and converts to the MCG model frame.
import cv2,re,subprocess,glob,json,math,sys
def read(f):
    im=cv2.imread(f); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)[:,300:]; g=cv2.resize(g,None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC)
    cv2.imwrite('/tmp/o.png',g); t=subprocess.run(['tesseract','/tmp/o.png','-','--psm','7'],capture_output=True,text=True).stdout
    m=re.search(r"37.49.(\d\d\.\d\d).{0,3}S\s*144.(\d\d).(\d\d\.\d\d).{0,3}E\s*(-?\d+)\s*m",t)
    if not m: return None,t.strip()
    lat=-(37+49/60+float(m.group(1))/3600); lon=144+int(m.group(2))/60+float(m.group(3))/3600
    return (lat,lon,int(m.group(4))),t.strip()
def model_xy(lat,lon):
    p=math.radians(-37.81977)
    mlat=111132.92-559.82*math.cos(2*p); mlon=111412.84*math.cos(p)-93.5*math.cos(3*p)
    E=(lon-144.98316)*mlon; N=(lat+37.81977)*mlat
    return E-24.77, N+23.11
if __name__=='__main__':
    out=[]
    for f in sorted(glob.glob(sys.argv[1]+'/s_*.png')):
        r,t=read(f)
        if r is None: print('fail',f,t); continue
        x,y=model_xy(r[0],r[1]); out.append([f,x,y,r[2]])
    json.dump(out,open(sys.argv[2],'w')); print(len(out))
