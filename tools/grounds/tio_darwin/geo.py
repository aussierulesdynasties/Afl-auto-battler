# local frame: x east, y north (m), origin = TIO Stadium pitch centroid (OSM way 121389821)
import json,math
J=json.load(open('sat/sat19.json'))
LAT0,LON0=-12.3991417,130.8872844
def ll2m(lat,lon):
    return ((lon-LON0)*111320*math.cos(math.radians(LAT0)), (lat-LAT0)*110574)
def tile(lat,lon,z):
    n=2**z;return (lon+180)/360*n,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n
def m2px(x,y,J=J):
    # local metres -> sat pixel (web mercator; local scale)
    cx,cy=tile(LAT0,LON0,J['z']);m=J['mpp']
    return ((cx-J['x0'])*256+x/m, (cy-J['y0'])*256-y/m)
