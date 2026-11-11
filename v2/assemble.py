import os, sys, zlib
from pathlib import Path

ROOT = Path('.')
BUILD = ROOT / 'v2' / 'build'

def arg(name, dflt):
    return next((x.split('=', 1)[1] for x in sys.argv[1:] if x.startswith(name + '=')), dflt)

OUT = Path(arg('--out', 'micidial_v2.html'))
shell_path = Path(arg('--shell', str(BUILD / 'shell.html')))
carrier_path = Path(arg('--carrier', 'micidial_v2.html'))

# section order is contractual with boot.js (MICIDIAL_V2.md §9.1)
sections = [
    (BUILD / 'boot.min.js').read_bytes(),
    (BUILD / 'outer.js').read_bytes(),
    (BUILD / 'synth.min.js').read_bytes(),
    (BUILD / 'stream.bin').read_bytes(),
    (BUILD / 'statics.txt').read_bytes(),
    (BUILD / 'pv.json').read_bytes(),
    (BUILD / 'meta.json').read_bytes(),
    (BUILD / 'audio.bin').read_bytes(),
    (BUILD / 'skeleton.json').read_bytes(),
    shell_path.read_bytes(),
]

# container: [u16 BE count][u32 LE compressed len xN][deflate-raw body xN]
cont = bytearray()
cont += len(sections).to_bytes(2, 'big')
gz = [zlib.compress(sec, 9, wbits=-15) for sec in sections]
for g in gz:
    cont += len(g).to_bytes(4, 'little')
for g in gz:
    cont += g

# page-safe embedding (§9.2): payload bytes ride raw inside a /* */ comment
# under meta charset=windows-1252; '*' bytes become '*' + chr(b+1) escape
# pairs, so the comment can never contain a real '*' -> NUL/CR/'*' escaped.
ESCAPES = {0, 13, 42}
enc = bytearray()
for b in cont:
    if b in ESCAPES:
        enc += b'*' + bytes([b + 1])
    else:
        enc += bytes([b])

# carrier = shipped page's pre + decoder code + post; code has no real /* or */
# (uses "\x2A" literals), so first real '/*' = payload open, last '*/' = close.
orig = carrier_path.read_bytes()
i = orig.find(b'<script>')
j = orig.rfind(b'</script>')
body = orig[i + 8:j]
a = body.find(b'/*')
b = body.rfind(b'*/')
assert a != -1 and b > a, 'carrier payload markers not found'
code = body[:a]
final = orig[:i] + b'<script>' + code + b'/*' + bytes(enc) + b'*/' + b'</script>' + orig[j + 9:]
OUT.write_bytes(final)
print('written', OUT, 'size', len(final))
print('sections raw', [len(s) for s in sections], 'defl', [len(g) for g in gz], 'sum', sum(len(g) for g in gz))
print('payload chars', len(enc), 'escapes', len(enc) - len(cont))
