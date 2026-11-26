"""Overture Maps buildings round a ground (heights, floors, roof shape/colour, source). usage: overture.py ground lat lon [half_deg]"""
import duckdb, sys, json, os
g, lat, lon = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]); d = float(sys.argv[4]) if len(sys.argv) > 4 else 0.03
con = duckdb.connect(); con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;")
con.execute("CREATE OR REPLACE SECRET anon (TYPE s3, PROVIDER config, KEY_ID '', SECRET '', REGION 'us-west-2')")
q = f"""select id, height, num_floors, roof_shape, roof_color, facade_color, roof_height, min_height,
 sources[1].dataset as src, names.primary as name, class, ST_AsText(geometry) as wkt
 from read_parquet('s3://overturemaps-us-west-2/release/2026-11-18.0/theme=buildings/type=building/*', hive_partitioning=1)
 where bbox.xmin>{lon-d} and bbox.xmax<{lon+d} and bbox.ymin>{lat-d} and bbox.ymax<{lat+d}"""
cols = ['id','height','num_floors','roof_shape','roof_color','facade_color','roof_height','min_height','src','name','class','wkt']
rows = [dict(zip(cols, r)) for r in con.execute(q).fetchall()]
json.dump(rows, open(os.environ.get('WORK', '/home/user/work') + '/overture/%s.json' % g, 'w'))
import collections
print(g, len(rows), collections.Counter(r['src'] for r in rows).most_common(5), 'height', sum(r['height'] is not None for r in rows))
