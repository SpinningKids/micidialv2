(async S=>{
var D=new TextDecoder();
var B,p=0,uvb,svb,R;
uvb=function(B){var v=0,s=0;return function(){var b=B[p++];v|=(b&127)<<s;if(!(b&128)){p++;return v;}s+=7;}};
svb=function(){var z=uvb(B)();return z&1?-(z>>1)-1:z>>1;};
R=function(x){var f=Math.floor(x),d=x-f;return d<.5?f:d>.5?f+1:f%2?f+1:f;};
var ss=D.decode(S[4]),k=ss.indexOf("\x01"),lines=ss.slice(0,k).split(";"),pool=ss.slice(k+1).split("\x00").map(JSON.parse);
var ns=lines.length;
var sk=JSON.parse(D.decode(S[8]));
B=S[3];p=0;
function _uvb(){var v=0,s=0;var b;for(;;){b=B[p++];v|=(b&127)<<s;if(!(b&128))return v;s+=7;}}
function _svb(){var z=_uvb();return z&1?-(z>>1)-1:z>>1;}
var nR=_uvb();var roles=[];for(var i=0;i<nR;i++){var L=_uvb();roles.push(D.decode(B.subarray(p,p+L)));p+=L;}
var scenesRec=[],occ=Array(nR).fill(0);
for(var si=0;si<ns;si++){
 var vN=_uvb();var vocab=[];for(var j=0;j<vN;j++){var m=_uvb();var vs=[];for(var k2=0;k2<m;k2++)vs.push(_uvb());vocab.push(vs);}
 var seqLen=_uvb();var recs=[];var tm=0;
 for(var j=0;j<seqLen;j++){var dt=_svb();tm=j?tm+dt:dt;var sid=_uvb();var vs=vocab[sid];for(var q=0;q<vs.length;q++){var r=vs[q];recs.push({r:r,t:tm/1e4});occ[r]++;}
 }
 scenesRec.push(recs);
}
var leafVals=Array(nR);for(var i=0;i<nR;i++)leafVals[i]=[];
function regen(kind,cnt){
 var s=[];
 if(kind===0){var v=_svb();for(var i=0;i<cnt;i++)s.push(v);}
 else if(kind===1){var a=_svb(),d=_svb();for(var i=0;i<cnt;i++){s.push(a);a+=d;}}
 else if(kind===2){var v=_svb(),d=_svb(),c=_svb();for(var i=0;i<cnt;i++){s.push(v);v+=d;d+=c;}}
 else if(kind===3){var m=_uvb(),prev=0,o=[];for(var i=0;i<m;i++){var n=_uvb(),dv=_svb();prev+=dv;for(var k2=0;k2<n;k2++)o.push(prev);}s=o;}
 else if(kind===4){var m=_uvb(),pi=0,pv=0,kn=[];for(var i=0;i<m;i++){pi+=_uvb();pv+=_svb();kn.push([pi,pv]);}var o=Array(cnt);for(var j=0;j+1<kn.length;j++){var i0=kn[j][0],v0=kn[j][1],i1=kn[j+1][0],v1=kn[j+1][1],sp=i1-i0;for(var i=i0;i<=i1;i++)o[i]=sp?R(v0+(v1-v0)*(i-i0)/sp):v0;}o[kn[0][0]]=kn[0][1];o[kn[kn.length-1][0]]=kn[kn.length-1][1];s=o;}
 else if(kind===5){var v=_svb();s.push(v);for(var i=1;i<cnt;i++){v+=_svb();s.push(v);}}
 return s;
}
while(p<B.length){
 var rid=_uvb();var g=_uvb();var kb=B[p++];var isDict=kb&0x80;var kind=kb&0x7F;
 var series=regen(kind,occ[rid]);
 if(isDict){var uniq=[];for(var i=0;i<g;i++){var L=_uvb();uniq.push(D.decode(B.subarray(p,p+L)));p+=L;}series=series.map(i=>uniq[i]);}else{var grid=g;series=series.map(v=>v/grid);}
 leafVals[rid].push(series);
}
function buildTemplate(paths){
 var root=[];
 for(var i=0;i<paths.length;i++){
   var p=paths[i];var cur=root;for(var j=0;j<p.length-1;j++){var idx=p[j];if(!cur[idx])cur[idx]=[];cur=cur[idx];}
   var idx=p[p.length-1];cur[idx]=i;
 }
 return root;
}
var tmpl=[];for(var i=0;i<nR;i++)tmpl[i]=buildTemplate(sk[roles[i]]);
function fill(node,vals,idx){
 if(typeof node==='number')return vals[node][idx];
 if(Array.isArray(node))return node.map(ch=>fill(ch,vals,idx));
 return node;
}
var occPtr=Array(nR).fill(0);
var scenes=[];
for(var si=0;si<ns;si++){
 var f=lines[si].split(',').map(Number);var sc=[pool[f[0]],pool[f[1]],pool[f[2]],pool[f[3]],pool[f[4]],pool[f[5]],[],pool[f[6]]];
 var recs=scenesRec[si];var out=[];
 for(var j=0;j<recs.length;j++){var r=recs[j].r;var t=recs[j].t;var idx=occPtr[r]++;var pay=fill(tmpl[r],leafVals[r],idx);out.push([0,roles[r],t,0,pay]);}
 sc[6]=out;scenes.push(sc);
}
var P={s:scenes,v:JSON.parse(D.decode(S[5])),a:['json',[D.decode(S[2]),S[7]]]};
var meta=JSON.parse(D.decode(S[6]));P.x=meta.x;P.t=meta.t;P.d=meta.d;P.q=meta.q;P.b=meta.b;P.n=meta.n;
// Inject the page shell (canvas + #setup/#gpu/#start/#fs + styles) before the engine runs.
var SH=D.decode(S[9]);
document.open();document.write(SH);document.close();
var O=D.decode(S[1]);
await new Function('P','(async()=>{const '+O.slice(1)+'})()')(P);
})