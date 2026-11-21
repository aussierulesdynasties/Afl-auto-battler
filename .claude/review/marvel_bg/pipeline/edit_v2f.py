"""Close still: facades varied up close, but light glass frames (176 grey) wash curtain walls to pale at orbit range. Dark frames."""
p = 'facade_mix.py'; s = open(p, newline='').read()
a = "'glass': [(58, 60, 64), (176, 178, 182), (36, 36, 38), (120, 124, 128)],"
assert s.count(a) == 1; s = s.replace(a, "'glass': [(44, 46, 50), (70, 74, 80), (36, 36, 38), (92, 96, 102)],")
open(p, 'w', newline='').write(s); print('ok')
