import os, zlib, json
from pathlib import Path

ROOT = Path('.')
BUILD = ROOT / 'v2' / 'build'
OUT = ROOT / 'micidial_v2.html'

# load sections
boot = (BUILD.parent / 'boot.js').read_text(encoding='utf-8')
outer = (BUILD / 'outer.js').read_text(encoding='utf-8')
synth = (BUILD / 'synth.min.js').read_text(encoding='utf-8')
stream = (BUILD / 'stream.bin').read_bytes()
statics = (BUILD / 'statics.txt').read_bytes()
pv = (BUILD / 'pv.json').read_bytes()
meta = (BUILD / 'meta.json').read_bytes()
audio = (BUILD / 'audio.bin').read_bytes()
skeleton = (BUILD / 'skeleton.json').read_bytes()
shell = (BUILD / 'shell.html').read_bytes()

sections = [
    boot.encode('utf-8'),
    outer.encode('utf-8'),
    synth.encode('utf-8'),
    stream,
    statics,
    pv,
    meta,
    audio,
    skeleton,
    shell,
]

count = len(sections)
# build container
out = bytearray()
out += count.to_bytes(2,'big')
for sec in sections:
    out += len(sec).to_bytes(4,'little')
for sec in sections:
    out.extend(sec)
# pad to multiple of 4
pad = (-len(out)) % 4
if pad: out.extend(b'\x00'*pad)

# deflate raw
out = zlib.compress(bytes(out), 9, wbits=-15)

alphabet = '!"#$%&()*+,-./0123456789:;=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwx'

def base85_encode(data, alphabet):
    out = []
    for i in range(0, len(data), 4):
        chunk = data[i:i+4]
        if len(chunk) < 4:
            chunk += b'\x00'*(4-len(chunk))
        v = int.from_bytes(chunk, 'big')
        chars = []
        for _ in range(5):
            chars.append(alphabet[v % 85])
            v //= 85
        out.extend(reversed(chars))
    return ''.join(out)

blob = base85_encode(out, alphabet)

# read original html to get pre/post
orig = (ROOT / 'original' / 'PRESSURE_ATBS135_v13.html').read_text(encoding='utf-8')
i = orig.find('<script>')
j = orig.find('</script>')
body = orig[i+8:j]
a_pos = body.find(chr(96)+'abc')
wx = body.find('qrstuvwx', a_pos)
cp = body.find(')', wx)
aq = cp-1
bang = body.rfind(chr(33),0,aq)
aoq = bang-1
brace = body.rfind('}',0,aoq)
blob_open = brace+4
head = body[:blob_open]
tail_start = body[brace+4:brace+5]  # should be '('
# construct final script
# head ends with '})('
# we need to close the ca call: head + blob + ',\'' + alphabet + '\');' + new code
script_body = head + blob + '\',\'' + alphabet + '\');'
# new code to parse container and run boot
code = '''
let d=new TextDecoder();
let b=await new Response(new Blob([u]).stream().pipeThrough(new DecompressionStream("deflate-raw"))).arrayBuffer();
let D=new Uint8Array(b),n=D[0]<<8|D[1],L=[],p=2;for(let i=0;i<n;i++){L.push(D[p]|D[p+1]<<8|D[p+2]<<16|D[p+3]<<24);p+=4;}
let off=2+4*n,S=[];for(let i=0;i<n;i++){S.push(D.subarray(off,off+L[i]));off+=L[i];}
await eval(d.decode(S[0]))(S);
'''
script_body += code + '})().catch(e=>document.body.textContent="BDE PACK ERROR · "+e)'

pre = orig[:i]
post = orig[j+9:]
final_html = pre + '<script>' + script_body + '</script>' + post
OUT.write_text(final_html, encoding='utf-8')
print('written', OUT, 'size', len(final_html))

