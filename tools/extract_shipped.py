#!/usr/bin/env python3
"""Decode the shipped v0.2 embed (micidial_v2.html) and dump its container sections.
Mirrors the shipped decoder: payload rides raw between /* */; byte '*' -> next byte - 1.
Usage: python tools/extract_shipped.py <shipped.html> <outdir>
"""
import sys, zlib, os, hashlib

src, out = sys.argv[1], sys.argv[2]
orig = open(src, 'rb').read()
i = orig.find(b'<script>'); j = orig.rfind(b'</script>')
body = orig[i + 8:j]
a = body.find(b'/*'); b = body.rfind(b'*/')
payload = body[a + 2:b]
cont = bytearray()
esc = 0
k = 0
while k < len(payload):
    c = payload[k]
    if c == 42:
        cont.append(payload[k + 1] - 1); k += 2; esc += 1
    else:
        cont.append(c); k += 1
n = int.from_bytes(cont[:2], 'big')
lens = [int.from_bytes(cont[2 + 4 * t: 6 + 4 * t], 'little') for t in range(n)]
off = 2 + 4 * n
names = ['boot.min.js', 'outer.js', 'synth.min.js', 'stream.bin', 'statics.txt',
         'pv.json', 'meta.json', 'audio.bin', 'skeleton.json', 'shell.html']
os.makedirs(out, exist_ok=True)
print(f'payload chars {len(payload)} container {len(cont)} escapes {esc}')
for t in range(n):
    g = cont[off:off + lens[t]]; off += lens[t]
    sec = zlib.decompress(g, -15)
    open(os.path.join(out, names[t]), 'wb').write(sec)
    print(f'{names[t]:>13}: defl {len(g)} -> raw {len(sec)} sha {hashlib.sha256(sec).hexdigest()[:8]}')
assert off == len(cont), 'container trailing bytes'
