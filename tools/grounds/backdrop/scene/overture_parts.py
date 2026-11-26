"""Overture building parts (towers on podiums etc.) round a ground. usage: overture_parts.py ground lat lon [half_deg]"""
import duckdb, sys, json, os
g, lat, lon = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]); d = float(sys.argv[4]) if len(sys.argv) > 4 else 0.03
con = duckdb.connect(); con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;")
con.execute("CREATE OR REPLACE SECRET anon (TYPE s3, PROVIDER config, KEY_ID '', SECRET '', REGION 'us-west-2')")
q = f"""select id, building_id, height, min_height, num_floors, min_floor, roof_shape, roof_color, facade_color, facade_material,
 roof_height, sources[1].dataset as src, ST_AsText(geometry) as wkt
 from read_parquet('s3://overturemaps-us-west-2/release/2026-11-18.0/theme=buildings/type=building_part/*', hive_partitioning=1)
 where bbox.xmin>{lon-d} and bbox.xmax<{lon+d} and bbox.ymin>{lat-d} and bbox.ymax<{lat+d}"""
cols = ['id','building_id','height','min_height','num_floors','min_floor','roof_shape','roof_color','facade_color','facade_material','roof_height','src','wkt']
rows = [dict(zip(cols, r)) for r in con.execute(q).fetchall()]
json.dump(rows, open(os.environ.get('WORK', '/home/user/work') + '/overture/%s_parts.json' % g, 'w'))
print(g, len(rows), 'height', sum(r['height'] is not None for r in rows), 'facade', sum(r['facade_color'] is not None for r in rows))
