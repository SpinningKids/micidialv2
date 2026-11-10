#!/usr/bin/env python3
"""Reverse the micidial v1 compression of PRESSURE_ATBS135_v13.html.

The compressed file is a single-line HTML with an inline IIFE script that:
  1. decodes a base85 ('85' alphabet) blob into bytes,
  2. decompresses them via DecompressionStream('deflate-raw') (i.e. raw gzip/zlib),
  3. evaluates the resulting text with new Function(s)().

This script extracts that blob, decodes it in Python, and writes the original file.

Script structure (the IIFE):
    let u=(function ca(e,a){...decode85...})(<BLOB>,'<ALPHABET>');
    s=await new Response(new Blob([u]).stream().pipeThrough(
        new DecompressionStream("deflate-raw"))).text();
    new Function(s)()
The blob uses the same custom base85 char range (which includes " and '), so we
locate literals structurally rather than by quote scanning.
"""
import gzip
import zlib
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
COMP = os.path.join(ROOT, '..', 'original', 'PRESSURE_ATBS135_v13.html')
OUT = os.path.join(ROOT, '..', 'reconstructed_original.html')


def main():
    with open(COMP, encoding='utf-8') as f:
        data = f.read()

    i = data.find('<script>')
    j = data.find('</script>')
    body = data[i + 8:j]

    # --- locate the alphabet literal "!'#$...wx" via its backtick-a run ---
    a_pos = body.find(chr(96) + 'abc')           # backtick before 'a' in alphabet
    assert a_pos != -1, 'alphabet not found'
    wx = body.find('qrstuvwx', a_pos)
    close_paren = body.find(')', wx)             # ...wx')  closes the arg
    alpha_close_quote = close_paren - 1          # closing quote of alphabet
    bang = body.rfind(chr(33), 0, alpha_close_quote)  # the '!' inside "!'#"
    alpha_open_quote = bang - 1                  # opening quote of alphabet
    alphabet = body[alpha_open_quote + 1:alpha_close_quote]
    assert len(alphabet) == 85, f'alphabet length {len(alphabet)} != 85'

    # --- locate the blob literal (between ca()'s closing '}' and the alphabet) ---
    brace = body.rfind('}', 0, alpha_open_quote)  # '}' that closes ca()
    # IIFE call form: <fn>)('<BLOB>,...); base85 starts after "')("
    blob_open = brace + 4
    assert body[blob_open] not in ('(', ')', "'"), repr(body[brace:brace + 6])
    blob_close_quote = alpha_open_quote - 2      # quote that closes the blob (before ',')
    blob = body[blob_open:blob_close_quote]

    def dec(s):
        out = bytearray()
        acc = 0
        cnt = 0
        for ch in s:
            acc = acc * 85 + alphabet.index(ch)
            cnt += 1
            if cnt == 5:
                for h in range(4):
                    out.append((acc >> (8 * (3 - h))) & 255)
                acc = 0
                cnt = 0
        if cnt:
            for _ in range(cnt, 5):
                acc = acc * 85 + 84
            for h in range(cnt - 1):
                out.append((acc >> (8 * (3 - h))) & 255)
        return bytes(out)

    raw = dec(blob)
    print(f'base85 blob length: {len(blob)}')
    print(f'decoded (compressed) len: {len(raw)}')

    # DecompressionStream("deflate-raw") == raw DEFLATE == zlib.decompress(raw, -15)
    orig = zlib.decompress(raw, -15)
    print(f'gunzipped original len: {len(orig)}')

    with open(OUT, 'wb') as f:
        f.write(orig)
    print(f'wrote {OUT}')


if __name__ == '__main__':
    main()
