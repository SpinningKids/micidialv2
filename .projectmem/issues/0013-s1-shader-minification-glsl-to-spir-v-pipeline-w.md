# #0013 S1: Shader minification + GLSL to SPIR-V pipeline with fallback

- 2026-11-10T19:41:50Z `issue`: S1: Shader minification + GLSL to SPIR-V pipeline with fallback [v2/shader_optimized.glsl]
- 2026-11-11T07:45:13Z `attempt`: Created v2/assemble_v02.py that outputs v0.2 custom container format (per-section deflate-raw + cp1252-safe base85 with C/H alphabet + * escaping). Fixed tools/unpack_v02.py to extract C/H from bootstrap. Verified container decodes correctly - all 10 sections match build artifacts (only outer.js line ending diff). New HTML is 46,414 bytes (well under 64 KiB cap). This assembler is prerequisite for P1+P5 shader optimizations since it doesn't use fragile DecompressionStream pipeline. (worked)
