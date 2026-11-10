#!/usr/bin/env python3
"""Producer for v2/build/audio.pkl: the audio model extracted from the input page.

Pulls P.a = ['json', [w, song]] out of original/uncompressed.html and pickles
{'w': workletSrc, 'song': projectObj} to build/audio.pkl (consumed by
v2/audio.py, which reads ['song']). Re-derived from original/uncompressed.html,
so the previously-orphan audio.pkl becomes reproducible.
"""
import json, os, pickle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'original', 'uncompressed.html')
BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
os.makedirs(BUILD, exist_ok=True)

s = open(TARGET, encoding='utf-8').read()
i_js, j_js = s.find('<script>'), s.find('</script>')
js = s[i_js + 8:j_js]
vi = js.find('const P=') + len('const P=')
P, vend = json.JSONDecoder().raw_decode(js, vi)

assert P['a'][0] == 'json'
w, song = P['a'][1][0], P['a'][1][1]
print(f'worklet src: {len(w)} chars; song obj: {len(song)} keys')
pickle.dump({'w': w, 'song': song},
            open(os.path.join(BUILD, 'audio.pkl'), 'wb'), protocol=4)
print('wrote build/audio.pkl')
