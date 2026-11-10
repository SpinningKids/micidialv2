# #0003 #0002 boot.js never injects DOM shell (#start/#setup/#gpu/canvas); outer JS queries them and throws 'Cannot set properties of null (onclick)'

- 2026-11-09T21:11:10Z `issue`: #0002 boot.js never injects DOM shell (#start/#setup/#gpu/canvas); outer JS queries them and throws 'Cannot set properties of null (onclick)'
- 2026-11-09T21:15:00Z `attempt`: Diagnosed: outer JS queries #start/#setup/#gpu/canvas at top-level; boot never injects shell DOM. Original v13 used one document.write() for whole page. (failed)
- 2026-11-09T21:17:46Z `attempt`: Added shell.html section (S[9]); boot.js now document.write()s it before running outer engine via new Function. Rebuilt via assemble.py. (partial)
- 2026-11-09T21:23:34Z `fix`: #0003 FIXED: boot.js now document.write()s shell.html (S[9]) before running outer engine. Browser test: 0 exceptions/0 console errors over 24s; #start/#setup/#gpu/canvas all present; shaders compile; demo launches.
