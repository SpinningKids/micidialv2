// recreate §3 stage 4b (file was cleaned from repo): terser, compress:false keeps eval completion value
const fs=require('fs'), terser=require('terser'), zlib=require('zlib');
const src=fs.readFileSync('v2/boot.js','utf8');
const m=terser.minify_sync(src,{compress:false,toplevel:true});
fs.writeFileSync('v2/build/boot.min.js',m.code);
console.log('boot.min.js raw',Buffer.from(m.code,'utf8').length,'defl',zlib.deflateRawSync(Buffer.from(m.code,'utf8'),{level:9}).length);
