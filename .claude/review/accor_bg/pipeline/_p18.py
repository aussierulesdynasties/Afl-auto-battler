# arena_01/02/03/05/08: eave is a saucer rim flaring up and out from the glass wall (18 m at wall -> 21 m, 12 m out).
p = 'accor_landmarks.py'; s = open(p, newline='').read()
x = "(*p, z0 + 20), (*q, z0 + 20), (*qo, z0 + 14), (*po, z0 + 14)"; assert x in s
s = s.replace(x, "(*p, z0 + 18), (*q, z0 + 18), (*qo, z0 + 21), (*po, z0 + 21)"); open(p, 'w', newline='').write(s); print('ok')
