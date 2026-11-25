import math,sys
def sun(doy,hm,lat=-37.82):
    L=math.radians(lat); dec=math.radians(-23.44*math.cos(2*math.pi*(doy+10)/365))
    H=math.radians((hm-12)*15)
    e=math.asin(math.sin(L)*math.sin(dec)+math.cos(L)*math.cos(dec)*math.cos(H))
    az=math.atan2(-math.sin(H)*math.cos(dec), math.cos(L)*math.sin(dec)-math.sin(L)*math.cos(dec)*math.cos(H))
    return math.degrees(e),math.degrees(az)%360
def at_az(doy,az):
    lo,hi=6.0,12.0
    for _ in range(60):
        m=(lo+hi)/2; a=sun(doy,m)[1]
        if a>az: lo=m
        else: hi=m
    return m,sun(doy,m)
if __name__=='__main__':
    doy=int(sys.argv[1]); az=float(sys.argv[2]); print(at_az(doy,az))
