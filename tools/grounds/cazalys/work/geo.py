import math
# Cazaly's Stadium origin: centroid of the OSM pitch outline (way 614183155)
LAT0,LON0=-16.935653,145.749062
p=math.radians(LAT0)
MLAT=111132.92-559.82*math.cos(2*p)+1.175*math.cos(4*p)
MLON=111412.84*math.cos(p)-93.5*math.cos(3*p)
def ll2xy(lat,lon): return ((lon-LON0)*MLON,(lat-LAT0)*MLAT)
def xy2ll(x,y): return (LAT0+y/MLAT,LON0+x/MLON)
