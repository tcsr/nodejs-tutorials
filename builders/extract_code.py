import re, sys, os
src, outdir = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf8').read().split('class Doc(')[0]
blocks = []
g = {'__file__': os.path.abspath(src)}
exec(compile(s, src, 'exec'), g)          # builds story; we re-run capturing code()
cap = []
g2 = {'__file__': os.path.abspath(src)}
s2 = s.replace('def code(src, caption=None):', 'def code(src, caption=None):\n    CAP.append(src)\ndef _orig_code(src, caption=None):')
g2['CAP'] = cap
exec(compile(s2, src, 'exec'), g2)
files = {}
for blk in cap:
    cur = None
    for ln in blk.strip('\n').split('\n'):
        m = re.match(r'^// ((?:src|test)/[\w/.-]+\.ts)\s*$', ln)
        if m:
            cur = m.group(1); files[cur] = []; continue
        if cur: files[cur].append(ln)
for f, lines in files.items():
    p = os.path.join(outdir, f); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf8').write('\n'.join(lines).strip('\n') + '\n')
    print(f, len(lines))
