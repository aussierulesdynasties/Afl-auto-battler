"""Write the proof render job for one oval: 4 turntable stills, a facade close-up, a turntable mp4.
    python py/proof.py KEY  facade_cam_x,y,z  facade_look_x,y,z"""
import json, sys
k = sys.argv[1]; fc = [float(x) for x in sys.argv[2].split(",")]; fl = [float(x) for x in sys.argv[3].split(",")]
job = {"out": "../out/%s/proof" % k.split("_")[0], "res": [1600, 1000], "samples": 32, "sun": {"az": 230, "el": 40, "power": 4.0},
       "views": [{"name": "turn", "orbit": {"r": 175, "z": 70, "look": [0, 0, 0], "frames": 4, "start_deg": 90, "fov_h": 55}},
                 {"name": "facade", "cam": fc, "look": fl, "fov_h": 55},
                 {"name": "turntable", "video": {"r": 175, "z": 70, "look": [0, 0, 0], "frames": 96, "start_deg": 90, "fov_h": 55, "res": [1280, 720], "samples": 12}}]}
json.dump(job, open("spec/%s_job_proof.json" % k.split("_")[0], "w"), indent=1)
