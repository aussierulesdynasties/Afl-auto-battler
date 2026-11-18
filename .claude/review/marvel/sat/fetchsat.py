import math,subprocess,io,sys
from PIL import Image
Z=int(sys.argv[1]) if len(sys.argv)>1 else 20
la0,lo0=-37.81650,144.94756;R=240  # metres half-span
def tile(la,lo,z):
    n=2**z;x=(lo+180)/360*n;y=(1-math.asinh(math.tan(math.radians(la)))/math.pi)/2*n;return x,y
mpd=111320
x0,y0=tile(la0+R/110574,lo0-R/(mpd*math.cos(math.radians(la0))),Z);x1,y1=tile(la0-R/110574,lo0+R/(mpd*math.cos(math.radians(la0))),Z)
X0,Y0,X1,Y1=int(x0),int(y0),int(x1),int(y1)
im=Image.new('RGB',(256*(X1-X0+1),256*(Y1-Y0+1)))
for x in range(X0,X1+1):
    for y in range(Y0,Y1+1):
        u='https://mt1.google.com/vt/lyrs=s&x=%d&y=%d&z=%d'%(x,y,Z)
        for k in range(4):
            r=subprocess.run(['curl','-s','-f','-A','stadium-ref/1.0',u],capture_output=True).stdout
            if r:break
        if r:im.paste(Image.open(io.BytesIO(r)).convert('RGB'),(256*(x-X0),256*(y-Y0)))
im.save('sat_z%d.jpg'%Z,quality=92)
open('sat_z%d.txt'%Z,'w').write('%d %d %d\n'%(Z,X0,Y0))
print(im.size,X0,Y0)
