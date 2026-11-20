cd "$(dirname "$0")/.."
python - <<'PY' > model/bb.txt
import sys;sys.path.insert(0,'work');import spec
for n,b in spec.B.items():
  xs=[p[0] for p in b['fp']];ys=[p[1] for p in b['fp']];zt=max(r['ridge'] for r in b['roofs'])
  print(n,min(xs)-2,min(ys)-2,max(xs)+2,max(ys)+2,zt+1)
PY
while read n a b c d z; do python model/cmp.py $n $a $b $c $d $z rr/b_$n.png; done < model/bb.txt
