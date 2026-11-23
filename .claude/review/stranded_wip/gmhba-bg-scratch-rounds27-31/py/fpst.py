import json,sys,numpy as np
a=np.array(json.load(open(sys.argv[1]))); print(len(a),a.min(),a.max(),a[0],a[45],a[90],a[135])
