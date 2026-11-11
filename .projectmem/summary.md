# projectmem - micidial_v2

_Last updated: 2026-11-11_

## Project purpose
Build "micidial v2": a scene compiler that compresses the single-file WebGL
intro `original/uncompressed.html` (5.36 MB) below 64 KiB while remaining a
self-contained HTML that renders identically in a standard browser.

## Recent issues
- [OPEN] #0014 assemble_v02.py produces broken micidial_v2.html: no audio, no particles, 'FLOW PARTICLES · FVD is not defined' error. File size 46KB (too small). Root cause: current build artifacts inconsistent - S5 over-removed FVD from outer.js (actually used), synth.min.js is old version (7939B vs 50521B... [v2/assemble_v02.py] (open)
- [OPEN] #0013 S1: Shader minification + GLSL to SPIR-V pipeline with fallback [v2/shader_optimized.glsl] (open)
- [OPEN] #0012 S3: Prune unused uniform array slots - max 5 objects used, trim uObjects[8] etc to actual max [v2/shader_optimized.glsl] (open)
- [OPEN] #0011 S2: Deduplicate domainModifier/fieldModifier logic in shader - factor into single modify() function [v2/shader_optimized.glsl] (open)
- [OPEN] #0001 built v2/extract+fit prototype (v2/compiler.py): per-(scene,role,slot) tracks, const/lin/quad/poly/RDP fits, varint cost estimator. Scene 0 alone = 55.6KB projected (under 64k); ALL 62 scenes = 157.9KB projected - OVER. Per-scene track splitting fragments smooth global curves (12,334 tracks... (open)
  - Partial attempt: built v2/extract+fit prototype (v2/compiler.py): per-(scene,role,slot) tracks, const/lin/quad/poly/RDP fits, varint cost estimator. Scene 0 alone = 55.6KB projected (under 64k); ALL 62 scenes = 157.9KB projected - OVER. Per-scene track splitting fragments smooth global curves (12,334 tracks...
  - Partial attempt: v2/floor.py fixed-cost measurement (everything except the 26,982 records): outer JS 34,194 -> deflate 13.8k; shaders 28,649 -> 9.4k; engine JS 96,684 (pure code, ZERO base64 samples, already minified; terser saves only 300 chars) -> 27.3k; project JSON 308,452 -> 10.8k; statics 93,890 -> 10.2k...
  - Partial attempt: compile.py v3.3: RDP reduction (reduce_records+rdp_local) + segs finite-difference token codec (fd_pick exact-seed + float LSQ binomial-basis solve, expand_segs verify) wired into choose_fit. Segs never wins: kept keys are jagged polylines (no index-polynomial after RDP); codec harmless but...
- [DONE] #0020 v2/synth.js on disk = legacy 7,939 B draft (min_synth.js -> defl 3,651), but shipped container section 2 = ported synth 50,521 B (sha 453a8b79); release commit a3ffba2 never committed the ported synth source. For variant builds must reuse tmp/shipped/synth.min.js extracted from shipped page [v2/synth.js] (fixed)
- [DONE] #0019 v2/assemble.py on disk is the v0.1 producer (single deflate + base85 + v13 splice) but shipped micidial_v2.html is v0.2 layout (per-section deflate + cp1252 comment embedding + carrier from scratch) — no committed producer for the shipped artifact; min_boot.js (§3 stage 4b) missing from repo [v2/assemble.py] (fixed)
- [DONE] #0018 3D objects missing entirely in rendered output. Music, particles, and other effects work. Likely cause: bounding sphere early-out (P5) is culling all objects because uObjBounds uniform data not populated from JavaScript, or checkBounds logic is wrong. Need to verify uObjBounds is computed and... [v2/outer_working.js] (fixed)
- [DONE] #0017 Shader compilation error: 'checkBounds' : no matching overloaded function found, '!' : wrong operand type. Function likely declared after use in shader (GLSL requires forward declaration or definition before use), or signature mismatch. [v2/hybrid_shader_p5.glsl] (fixed)
- [DONE] #0016 micidial_v2.html fails with shader compilation error: 'ERROR: 0:1: '#' : unexpected token WARNING: 0:1: '' : unexpected end of file found in directive ERROR: 1:1: '' : syntax error'. Likely the minified shader lost required newlines for #version and #define directives. [v2/hybrid_shader_p5.min.glsl] (fixed)
- [DONE] #0015 assemble_v02.py output still broken: no music, no particles. User reports functional regression. Need to compare working v0.2.html vs new output section by section to find what's missing. Key difference: working v0.2.html section 1 (outer.js) is 62,852 B decompressed, new is 42,162 B - 20KB... [v2/assemble_v02.py] (fixed)
- [DONE] #0010 P5: Added bounding sphere early-out in scene() SDF loop via uObjBounds uniform [v2/shader_optimized.glsl] (fixed)
- [DONE] #0009 P1: Replace 4-tap tetrahedral gradient with analytical ∇SDF for all 7 primitives + 11 modifiers (chain rule) — 30-45% fragment time [shader_frag.glsl] (fixed)
- [DONE] #0008 P5: Add early-out bounding spheres for object loop in scene() SDF — skip objectField when ray misses bounds [shader_frag.glsl] (fixed)
- [DONE] #0007 S5: Remove dead code from outer.js (particle field builder, fallback audio, debug code, unused blend modes) (~5 KB savings) [v2/outer.js] (fixed)
- ...and 5 older fixed issues not shown (`pjm search`, or `get_issue(issue_id)` via MCP)

## Decisions
- ...7 earlier decisions not shown (`pjm search`, or `search_events(query)` via MCP)
- Fix #0003: add dedicated shell section to container; boot.js writes it via document.write() (canvas+#setup+#gpu+#start+#fs+styles) BEFORE running outer engine. Preserves original v13 DOM-injection behavior.
- Loss budget accepted for scene stream (default profile --rdp=1 --quant=100 --tol=0.011): RDP keyframe reduction 26,982->4,078 records (vertical metric = engine K() linear-blend error bound <=1.0 raw unit); float requant grid=100; validator measured worst deviation 0.01, 0 hard mismatches. Full... [v2/compile.py]
- Audio blob loss accepted: automation anchors RDP-reduced at eps 1.0 on round(v*100) (0.01 units); vel/prob *100 clamped 0..127 (caps at 1.27); ratchet>=2 boolean collapse; gate steps 2-bit {0,.5,1}; prob==1 implicit (lossless over asserted universe). Sound itself is a procedural atbs-v04 remake... [v2/audio.py]
- Cleanup 2026-11-10: deleted superseded scratch (compiler.py, compiler2.py, dead build.py, floor.py, iface2.py, interp_err.py, protocol.py, shapes.py, ties.py-7, synth_draft*.js.txt, test_synth.js, boot.min.js, unpack_orig.py, __pycache__, root nul) + tools one-shot probes; added audio_extract.py... [v2/]
- FINAL cleanup policy 2026-11-10 (strictens prior Cleanup decision): keep ONLY rerun inputs. v2/: compile.py, iface.py, audio_extract.py, audio.py, assemble.py, min_synth.js, synth.js, boot.js + build/shell.html. v2/build/ holds ONLY shell.html (hand-written input); all other build files are...
- Repo initialized & published to GitHub: origin = https://github.com/SpinningKids/micidialv2.git, branch master (not main); initial import tagged v0.1 with README.md.
- README updated: removed all micidial/ folder refs, linked upstream v1 repo https://github.com/SpinningKids/micidial; pushed to origin/master (synced after a pre-existing remote divergence). micidial/ dir already absent.
- v0.2 pipeline uses per-section deflate-raw container (63,484 B deflated sum) + windows-1252 cp1252 inverse-table encoding with * escape pairs (+712 B overhead), replacing v0.1's single deflate-raw + base85 (52,792 B -> 65,990 base85 chars). Boot code minified. Audio engine completely rewritten...
- v0.2 ambiguity resolutions: (1) v0.2 synth.js is hand-written, replaces legacy v0.1 synth.js (archive legacy); (2) min_boot.js superseded, removed from docs (settings lost); (3) compiler flags unchanged since v0.1; (4) outer.js CRLF is build environment artifact; (5) v02.html code overrides...
- Write v2/assemble_v02.py to produce v0.2 custom container format (per-section deflate-raw + cp1252-safe base85 with C/H alphabet + * escaping). Prerequisite for applying P1+P5 shader optimizations since current assemble.py uses fragile DecompressionStream pipeline that breaks on any outer.js... [v2/assemble_v02.py]
- S5 dead-code removal was over-aggressive - removed FVD/particle code that was actually used at runtime. Working v0.2.html predates S5. assemble_v02.py now sources sections 0-2 from working artifact (boot_working.js, outer_working.js, synth_working.js). Output 64,966 B (570 B under cap)... [v2/assemble_v02.py]
- Applied P5 shader optimization (bounding sphere early-out) successfully. Full P1+P5 shader (analytical gradients + bounding spheres) is 24,985 bytes minified - too large (pushes HTML to 65,818 bytes, 282 B over cap). Hybrid approach: original shader + P5 only = 20,709 bytes minified (smaller... [v2/hybrid_shader_p5.min.glsl]
- Variant-processing baseline (v21 eval): 1) unpack v1 container (base85+deflate-raw); if payload is a document.write bootstrap, eval it with stubbed document (tmp/unwrite_page.js) to recover real page; 2) diff P keys vs uncompressed.html to scope changes; 3) rerun compile.py+iface.py with... [tmp/]
- original/uncompressed.html removed from repo (storage): it is regeneratable — python tools/decompress_any.py original/PRESSURE_ATBS135_v13.html original/uncompressed.html yields the exact 5,359,781 B v13 payload; pipeline uses --src= or stage-0 regen. Tools made permanent in tools/ so tmp/... [original/]
- original/uncompressed.html removed from repo (storage; supersedes prior claim): byte-exact copy lives in git history (git restore source HEAD~). Functional regen = tools/decompress_any.py + tools/unwrite_page.js; output is 27 B SHORTER than browser-decoded page because Node lacks document.write... [original/]

## Notes
- v0.2 unpacked: 10 sections recovered. Shader (20.9K chars), outer.js (92K), boot.js (3K), scene stream (26K), audio (3.7K). Engine is full raymarcher with 7 primitives, 11 modifiers, CSG, thin-film, glass, volumetrics, AO, bloom, lens flare, motion blur. Decoder handles 6 track kinds... [v2/build/v02_unpack]
- New rule established: keep reusable tools (unpack_v02.py, check_alphabet.py) in tools/ directory. Temporary tools deleted after use. v0.3 pipeline: compile.py -> audio_extract.py -> audio.py -> min_synth.js -> iface.py -> assemble.py -> micidial_v2_v03.html [tools/]
- Pre-delivery validation: test micidial_v2_v04.html in browser/headless to ensure no 'BDE PACK ERROR · SyntaxError: Invalid or unexpected token' at launch. This catches shader/JS syntax issues from the P5+P1 patch. [tools/patch_shader.py]
- Parse error 'missing ) after argument list' was caused by HTML structure differences between assemble.py output and working hybrid template. Fixed by generating HTML from working hybrid template structure. Shader optimizations (P1+P5) increase size by ~1.5KB over 64KiB cap. [tools/generate_v04_from_hybrid.py]
- gotcha: v1-compressed pages >= v21 use a document.open/document.write('...') bootstrap instead of new Function(payload); payload HTML has JS-string escapes (\" \n). Decompress = base85+deflate-raw (tools/decompress.py logic) THEN eval payload with stubbed document (tmp/unwrite_page.js) to... [original/PRESSURE_ATBS135_v21.html]
- v21 demo vs v13: P.a/x/t/d/q/b/n identical; P.s all 62 scenes changed, records 26,982->30,839 (+14%); P.v all 62 differ; engine tail 62,866->65,681 chars; head 1,790->1,770. Eval run: v2 must retool for any ABTS-generated page [original/]
- variant tooling (tmp/): decompress_any.py = generic v1 container decoder (any PRESSURE_ATBS135_vN.html -> payload); unwrite_page.js = recovers real page from document.write payloads; diff_v13_v21.py = P-key scoping diff. v21 decompressed page lives in tmp/uncompressed_v21.html [tmp/]
- note: shipped micidial_v2.html defl streams came from an older zlib build; current Python 3.13 zlib compresses the same raw sections SMALLER (defl sum 63,115 vs 63,484). Rebuilds with assemble.py are byte-different but decode-identical; verification = extract shipped embed, byte-compare inflated... [v2/assemble.py]
- variant tooling now PERMANENT in tools/ (not tmp/): decompress_any.py (v1 container -> payload), unwrite_page.js (document.write payload -> real page), diff_pages.py (generic P-key scoping diff, argv A B), extract_shipped.py (decode shipped embed -> sections), verify_page.js (Chrome-faithful... [tools/]
- gotcha: v13 payload IS also a document.write bootstrap (not runnable JS); unwrite_page output misses browser auto-inserted html/head/body tags (+27 B vs committed page) — fine for pipeline, never claim byte-exact regen from tools alone [tools/unwrite_page.js]

## Key files
- `original/PRESSURE_ATBS135_v13.html`
- `tools\decompress.py`
- `decompress.py`
- `tools\dbg.py`
- `dbg.py`
- `micidial\tools\verify_reconstruct.js`
- `verify_reconstruct.js`
- `tools\parse_probe.js`
- `parse_probe.js`
- `tools\finalize_reconstruct.js`
- `finalize_reconstruct.js`
- `P.s`
- `uncompressed.html`
- `1.8KB`
- `P.a`
- `P.v`
- `P.x`
- `tools/analyze_scene.py`
- `budget.py`
- `probe_inner.py`

## Open questions
- None logged yet.
