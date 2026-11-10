#!/usr/bin/env python3
"""Find the audio contract between outer JS and inner engine."""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'original', 'uncompressed.html')
BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
os.makedirs(BUILD, exist_ok=True)

s = open(TARGET, encoding='utf-8').read()
i_js, j_js = s.find('<script>'), s.find('</script>')
js = s[i_js + 8:j_js]
vi = js.find('const P=') + len('const P=')
P, vend = json.JSONDecoder().raw_decode(js, vi)
rest = js[vend:]

engine = P['a'][1][0]
open(os.path.join(BUILD, 'engine.js'), 'w', encoding='utf-8').write(engine)
open(os.path.join(BUILD, 'outer.js'), 'w', encoding='utf-8').write(rest)
open(os.path.join(BUILD, 'project.json'), 'w', encoding='utf-8').write(
    json.dumps(P['a'][1][1], separators=(',', ':'), ensure_ascii=False))

def show(name, txt, pats, width=90):
    print(f'--- {name} ---')
    for pat in pats:
        ms = list(re.finditer(pat, txt))
        print(f'  {pat!r}: {len(ms)} hits')
        for m in ms[:4]:
            a, b = max(0, m.start() - 40), min(len(txt), m.end() + width)
            print(f'    ...{txt[a:b]}...')

hits_out = ['AudioWorklet', 'audioContext|AudioContext', 'postMessage', 'new Worker',
            r'\bworker\b', "'message'|\"message\"", 'onbeat|beat', r'on\("ci|on\(\'ci', 'addEventListener']
hits_eng = ['postMessage', r'\bself\b', 'worklet', 'connect\\(', 'resume\\(', 'currentTime', 'startRendering']
show('OUTER (render) audio refs', rest, hits_out)
show('ENGINE audio refs', engine, hits_eng, width=70)

# what does the engine expose globally?
t = re.findall(r'(?:window\.)?([A-Za-z_$][\w$]*)\s*=\s*\{|module\.exports|exports\.[A-Za-z_$]+', engine[:4000])
print('\nengine head 1000:', engine[:1000])
