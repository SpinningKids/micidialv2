const fs=require('fs');
const terser=require('terser');
const src=fs.readFileSync('v2/synth.js','utf8');
const m=terser.minify_sync(src,{toplevel:true});
if(!m.code){console.log('NULLRESULT keys',Object.keys(m),'err',JSON.stringify(m.error||null),'warn',JSON.stringify(m.warnings||null));process.exit(1);}
const r=m.code;
fs.writeFileSync('v2/build/synth.min.js',r);
const raw=Buffer.from(r,'utf8').length;
const zlib=require('zlib');
const defl=zlib.deflateRawSync(Buffer.from(r,'utf8'),9).length;
console.log('raw',raw,'defl',defl);
