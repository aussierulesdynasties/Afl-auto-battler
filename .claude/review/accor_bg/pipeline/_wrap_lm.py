L = open('accor_landmarks.py', encoding='utf-8', newline='').read().split('\n')
i = next(k for k, l in enumerate(L) if l.startswith('def _lm_drop'))
out = L[:i] + ['def _accor_landmarks():'] + ['    ' + l if l.strip() else l for l in L[i:]] + ['_accor_landmarks()', '']
open('accor_landmarks.py', 'w', encoding='utf-8', newline='').write('\n'.join(out)); print('ok')
