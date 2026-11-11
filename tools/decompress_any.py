#!/usr/bin/env python3
"""Reverse micidial v1 compression for any PRESSURE_ATBS135_vN.html.
Same container format as v13: base85 blob + deflate-raw inside one <script>.
Usage: python tools/decompress_any.py <in.html> <out.html>
"""
import sys, zlib

def dec(s, alphabet):
    out = bytearray(); acc = 0; cnt = 0
    for ch in s:
        acc = acc * 85 + alphabet.index(ch); cnt += 1
        if cnt == 5:
            for h in range(4): out.append((acc >> (8 * (3 - h))) & 255)
            acc = 0; cnt = 0
    if cnt:
        for _ in range(cnt, 5): acc = acc * 85 + 84
        for h in range(cnt - 1): out.append((acc >> (8 * (3 - h))) & 255)
    return bytes(out)

def main():
    src, dst = sys.argv[1], sys.argv[2]
    data = open(src, encoding='utf-8').read()
    i = data.find('<script>'); j = data.find('</script>')
    body = data[i + 8:j]
    a_pos = body.find(chr(96) + 'abc')
    assert a_pos != -1, 'alphabet not found'
    wx = body.find('qrstuvwx', a_pos)
    close_paren = body.find(')', wx)
    alpha_close_quote = close_paren - 1
    bang = body.rfind(chr(33), 0, alpha_close_quote)
    alpha_open_quote = bang - 1
    alphabet = body[alpha_open_quote + 1:alpha_close_quote]
    assert len(alphabet) == 85, f'alphabet length {len(alphabet)} != 85'
    brace = body.rfind('}', 0, alpha_open_quote)
    blob_open = brace + 4
    assert body[blob_open] not in ('(', ')', "'"), repr(body[brace:brace + 6])
    blob_close_quote = alpha_open_quote - 2
    blob = body[blob_open:blob_close_quote]
    raw = dec(blob, alphabet)
    orig = zlib.decompress(raw, -15)
    open(dst, 'wb').write(orig)
    print(f'blob {len(blob)} chars -> deflated {len(raw)} -> original {len(orig)} bytes; wrote {dst}')

if __name__ == '__main__':
    main()
