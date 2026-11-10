(function(){var CT=[[0,3,7],[0,4,7],[0,7,10],[0,3,6,10],[0,3,7,10],[0,4,7,11,14],[0,3,7,10,14],[0,5,7],[0,5,7,10,14],[0],[0,7],[0,12]],TAU=6.283185307179543,U32=4294967295;
function B(g,t){return g<t?(g=g/t,g+g-g*g-1):g>1-t?(g=(g-1)/t,g*g+g+g+1):0}
function H(x){x=(x^(x<<13))&U32;x=(x^(x>>>17))&U32;x=(x^(x<<5))&U32;return x/U32}
function it(g){return 440*Math.pow(2,(g-69)/12)}
class D{
constructor(sr){this.sr=sr;this.pos=0;this.vs=[];this.ei=0;this.L=0;this.R=0;this.pa=[0,0];this.acc=[0,0,0]}
av(i,k,b,j){var m=this.au[i][k];if(!m)return b;var p=0,c=null,d=null;while(p<m.length&&m[p][0]<=j){c=m[p];p++}if(!c)return b;d=p<m.length?m[p]:null;if(!d)return c[1];if(d[0]==c[0])return d[1];return c[1]+(d[1]-c[1])*(j-c[0])/(d[0]-c[0])}
st(u){var n=u[0],o=1,j,p,q;this.n=n;this.ba=[];this.g=[];for(p=0;p<6;p++)this.g.push([]);
for(j=0;j<n;j++){this.ba.push(u[o]);for(p=0;p<6;p++)this.g[p].push(u[o+1+p]-1);o+=7}
this.au=[];for(j=0;j<n;j++)this.au.push({});
var nt=u[o++];for(p=0;p<nt;p++){var si=u[o],k=u[o+1],na=u[o+2],Q=[];o+=3;for(q=0;q<na;q++)Q.push([u[o],u[o+1]/100]),o+=2;this.au[si][k]=Q}
var mx=[0,0,0,0,0,0];for(p=0;p<6;p++)for(j=0;j<n;j++)if(this.g[p][j]+1>mx[p])mx[p]=this.g[p][j]+1;
this.ac=[[],[]];
for(p=0;p<mx[0]+mx[1];p++){var N=[],F=[];for(q=0;q<64;q++)N.push(u[o]+24),F.push(u[o+1]),o+=2;var P={},np=u[o++];for(q=0;q<np;q++)P[u[o]]=u[o+1]/100,o+=2;this.ac[p<mx[0]?0:1].push([N,F,P])}
this.dr=[];
for(j=0;j<mx[2];j++){var nr=u[o++],R=[];for(p=0;p<nr;p++){var ri=u[o++],bm=o,on=[],A=[];o+=8;for(q=0;q<64;q++)if(u[bm+(q>>3)]>>(q&7)&1)on.push(q);for(q=0;q<on.length;q++){var vb=u[o++];A[on[q]]=[(vb&127)/100,vb>>7]}var nP=u[o++],PR={};for(q=0;q<nP;q++)PR[u[o]]=u[o+1]/100,o+=2;R.push([ri,A,PR])}this.dr.push(R)}
this.st2=[];this.fx2=[];
for(p=0;p<mx[3]+mx[4];p++){var on2=[],q2;for(q2=0;q2<64;q2++)if(u[o+(q2>>3)]>>(q2&7)&1)on2.push(q2);o+=8;var rec=[];for(q2=0;q2<on2.length;q2++)rec.push([on2[q2],u[o]+24,u[o+1],u[o+2],u[o+3]/100]),o+=4;var en=u[o],rate=u[o+1],pk=0,st16=[];for(q2=0;q2<4;q2++)pk|=u[o+3+q2]<<(8*q2);for(q2=0;q2<16;q2++){var vv=(pk>>(2*q2))&3;st16.push(vv==0?0:vv==1?0.5:1)}o+=7;(p<mx[3]?this.st2:this.fx2).push([rec,st16,en,rate])}
this.cs=[];this.smap=[];var g0=0;for(j=0;j<n;j++){this.cs.push(g0);for(q=0;q<this.ba[j]*16;q++)this.smap.push(j);g0+=this.ba[j]*16}
this.gsn=g0}
build(){var sr=this.sr,sS=sr*60/135/4,gs=0,ev=[],i,j,p,S=303909;this.vs=[];this.ei=0;this.pos=0;this.pa=[0,0]
for(i=0;i<this.n;i++){var nl=this.ba[i]*16
for(j=0;j<nl;j++,gs++){var pc=j&63,tm=(gs+((j&1)?.03:0))*sS,gi,bl,f,nt,pr
for(p=0;p<2;p++){gi=this.g[p][i];if(gi<0)continue;bl=this.ac[p][gi];f=bl[1][pc];if(!(f&1))continue;pr=bl[2][pc];if(pr==null)pr=1;if(H(S+gs*131+p*17+11)>=pr)continue;nt=bl[0][pc]
ev.push([tm,0,it(nt),f&2?1.3:.92,this.av(i,2*p,.3+p*.11,j),this.av(i,2*p+1,.71-p*.33,j),p,f&4?1:0,f&2?1:0])
if(f&8)ev.push([tm+sS*.5,0,it(nt),f&2?1.3:.92,this.av(i,2*p,.3+p*.11,j),this.av(i,2*p+1,.71-p*.33,j),p,f&4?1:0,0])}
gi=this.g[2][i];if(gi>=0){var dr=this.dr[gi];for(var z=0;z<dr.length;z++){var rw=dr[z],a2=rw[1][pc];if(!a2)continue;pr=rw[2][pc];if(pr==null)pr=1;if(H(S+gs*131+rw[0]*17+3)>=pr)continue
ev.push([tm,1,rw[0],a2[0]*.975]);if(a2[1])ev.push([tm+sS*.5,1,rw[0],a2[0]*.68])}}
for(p=3;p<5;p++){gi=this.g[p][i];if(gi<0)continue;var b3=p==3?this.st2[gi]:this.fx2[gi],rec=b3[0],lv2=p==3?this.av(i,8,.45,j):this.av(i,9,.33,j),cu=p==4?this.av(i,4,.5,j):.5,rs=p==4?this.av(i,5,.12,j):.42
for(var w=0;w<rec.length;w++)if(rec[w][0]==pc){if(b3[2]){var st16=b3[1],nf=b3[3]==32?32:16;for(var m2=0;m2<nf;m2++){var sv2=st16[(b3[3]==32?(2*(m2>>1)+(m2&1)):m2)%16];if(sv2>0)ev.push([tm+m2*sS/nf,2,rec[w][1],rec[w][2],rec[w][3],rec[w][4]*lv2*sv2,p-3,cu,rs])}}else ev.push([tm,2,rec[w][1],rec[w][2],rec[w][3],rec[w][4]*lv2,p-3,cu,rs]);break}}}}
ev.sort(function(a,b){return a[0]-b[0]});this.ev=ev
var mm=65536,mx2=this.gsn*sS;while(mm<mx2+this.sr+4096)mm*=2;this.ring=new Float64Array(mm);this.rm=mm-1
this.vs.push(this.drn(0,this.gsn+4))}
drn(sp,eS){var sr=this.sr,sS=sr*60/135/4,u2=Math.min(30*Math.pow(520,.22),sr*.43),q0=Math.tan(Math.PI*u2/sr),hh=2-1.965*.5,a1=1/(1+q0*(q0+hh)),a2=q0*a1,a3=q0*a2;return[eS*sS,3,sp*sS,sp*7717+9,0,0,a1,a2,a3,0,0,64,.21,.22,.22,0,0,0,0,0]}
spawn(e){var sr=this.sr,sS=sr*60/135/4,p=e[0],k=e[1]
if(k==0){var g=e[6],dc=g?1:.42,rel=Math.exp(-1/((.045+dc*.85)*sr)),hold=Math.round(sS*(e[7]?1.06:.72)),tl=Math.ceil(11.51/-Math.log(rel)),lv2=g?.08:.07,dy=g?.37:.8,pn=g?.32:-.3,wz=g?.52:.48,r0=Math.min(Math.max(e[2]/sr,1e-6),.45)
this.pa[g]=(this.pa[g]+hold*r0)%1
this.vs.push([p+hold+tl,0,p,this.pa[g],e[3],e[8]?1.35:1,hold,e[4],e[5],e[4],e[5],(g?.7:.34)*(.19+.08*e[8]),r0,g,(g?.14:.13),rel,Math.exp(-1/(.4*sr)),1,lv2*dy*(1-pn)/2,lv2*dy*(1+pn)/2,lv2*wz,0,0,1,0,0,0,0,0])}
else if(k==1)this.vs.push([p+sr*.9,1,p,e[2],e[3],e[2]*99991+p*7])
else if(k==2)this.sp2(e,p)
else this.vs.push(e)}
sp2(e,p){var sr=this.sr,g2=e[6],ct2=CT[e[3]%12],ln2=ct2.length,u3=Math.min(30*Math.pow(520,e[7]),sr*.43),q3=Math.tan(Math.PI*u3/sr),h3=2-1.965*e[8],a13=1/(1+q3*(q3+h3)),a23=q3*a13,a33=q3*a13,hz2=[]
for(var m2=0;m2<ln2;m2++){var dg2=ct2[(m2+e[4])%ln2]+(m2+e[4]>=ln2?12:0);hz2.push(it(e[2]+dg2))}
while(hz2.length<5)hz2.push(hz2[0])
var MW=g2?[.066,.154,.88]:[.2775,.0925,1]
this.vs.push([p+sr*(g2?1.8:2),2,p,e[5],e[8],g2?3.84:2.31,g2,a13,a23,a33,0,0,0,0,ln2].concat(hz2).concat(MW))}
voice(v,pos){var k=v[1];if(k==0)return this.v0(v,pos);if(k==1)return this.v1(v,pos);if(k==2)return this.v2(v,pos);return this.v3(v,pos)}
v0(v,pos){var sr=this.sr,acc=this.acc,ph=v[3],r=v[12],o2
if(v[13]){o2=ph<.5?1:-1;o2+=B(ph,r);var l2=ph+.5;if(l2>=1)l2-=1;o2-=B(l2,r)}else o2=2*ph-1-B(ph,r)
ph+=r;if(ph>=1)ph-=1;v[3]=ph;v[5]*=v[16]
if(v[6]>0){v[6]--;v[4]*=.999992}else v[4]*=v[15]
v[7]+=.003*(v[9]-v[7]);v[8]+=.003*(v[10]-v[8])
if((v[17]&15)==0){var l3=v[7]+v[5]*v[11];if(l3>1)l3=1;if(l3<0)l3=0;var u4=30*Math.pow(520,l3);if(u4>sr*.43)u4=sr*.43;var q4=Math.tan(Math.PI*u4/sr),h4=2-1.965*v[8];v[23]=1/(1+q4*(q4+h4));v[24]=q4*v[23];v[25]=q4*v[24]}v[17]++
var c2=Math.tanh(o2*(1.1+v[14]*8)),s2=c2-v[22],i21=v[23]*v[21]+v[24]*s2,h21=v[22]+v[24]*v[21]+v[25]*s2;v[21]=2*i21-v[21];v[22]=2*h21-v[22];v[26]=i21
c2=h21+v[26]*v[8]*.24;c2=Math.tanh(c2*(1+v[14]*5.2))*v[4]
acc[0]+=c2*v[18];acc[1]+=c2*v[19];acc[2]+=c2*v[20];return v[4]>1e-6}
v1(v,pos){var sr=this.sr,acc=this.acc,t=(pos-v[2])/sr,KK=[55,65,20,5,6,11,90,210,120,45,20,80,15,30,150,90,45,20,70,15,25,420,300,60,70,45,70,20,560,30,30,45,85,45,15,400,10,4,10,85,6,12,190,130,32,10,45,8,70,150,120,30,11,40,8,70,120,110,30,12,35,8,70,270,80,20,20,60,20,25,60,90,14,5,70,6,20,380,15,8,11,35,8,25],q=v[3]*7,nz=H((v[5]+pos*2654435761)&U32)*2-1
var y=(KK[q+6]/100)*Math.sin(TAU*(KK[q]+KK[q+1]*Math.exp(-t*KK[q+2]))*t)*Math.exp(-t*KK[q+3])+(KK[q+4]/100)*nz*Math.exp(-t*KK[q+5])
var c2=y*v[4];if(c2>1)c2=1;else if(c2<-1)c2=-1
acc[0]+=c2*.535;acc[1]+=c2*.535;acc[2]+=c2*.1284;return 1}
v2(v,pos){var sr=this.sr,acc=this.acc,t=(pos-v[2])/sr,m3,sum=0
for(m3=0;m3<v[14];m3++)sum+=Math.sin(TAU*v[15+m3]*(t+.013))
var y2=Math.tanh(sum*.42)*Math.exp(-t*v[5]),s2=y2-v[11],i21=v[7]*v[10]+v[8]*s2,h21=v[11]+v[8]*v[10]+v[9]*s2;v[10]=2*i21-v[10];v[11]=2*h21-v[11];v[12]=i21
var c2=h21+v[12]*v[4]*.24;c2=Math.tanh(c2*1.6)*v[3]
acc[0]+=c2*v[20];acc[1]+=c2*v[21];acc[2]+=c2*v[22];return 1}
v3(v,pos){var sr=this.sr,acc=this.acc,sS=sr*60/135/4,t3=(pos-v[2])/sr
v[19]+=1/sS
if((v[11]&63)==0){var gs3=v[19]|0,sc3=this.smap[gs3<this.smap.length?gs3:this.smap.length-1],j3=v[19]-this.cs[sc3]
v[14]=this.av(sc3,6,.22,j3);v[12]=this.av(sc3,7,.21,j3)
var u5=Math.min(30*Math.pow(520,v[14]),sr*.43),q5=Math.tan(Math.PI*u5/sr),h5=2-1.965*.5;v[6]=1/(1+q5*(q5+h5));v[7]=q5*v[6];v[8]=q5*v[6]}v[11]++
v[13]+=.02*(v[14]-v[13])
var f0=130.8128,nz3=(H((v[3]+pos*131517)&U32)*2-1)*.3
var y3=(.42*Math.sin(TAU*f0*t3)+(.5*v[13]+.08)*Math.sin(TAU*f0*2.01*t3)*.8+v[13]*.22*Math.sin(TAU*f0*3.03*t3)*.55+(.5-v[13]*.4)*nz3)*Math.min(1,t3*2)
var y3c=Math.tanh(y3*1.5),s2=y3c-v[5],i21=v[6]*v[4]+v[7]*s2,h21=v[5]+v[7]*v[4]+v[8]*s2;v[4]=2*i21-v[4];v[5]=2*h21-v[5];v[9]=i21
var c3=Math.tanh(h21*1.25)*v[12]
acc[0]+=c3*.5;acc[1]+=c3*.5;acc[2]+=c3*.08;return 1}
sp(){var sr=this.sr,pos=this.pos++,acc=this.acc,ev=this.ev,vs=this.vs,i,mm=this.rm,w2=this.ring
if(!this.dl0){this.dl0=Math.round(sr*.533);this.dr0=Math.round(sr*.767)}
while(this.ei<ev.length&&ev[this.ei][0]<=pos)this.spawn(ev[this.ei++])
acc[0]=acc[1]=acc[2]=0;var k2=0
for(i=0;i<vs.length;i++)if(vs[i][0]>pos&&this.voice(vs[i],pos))vs[k2++]=vs[i]
vs.length=k2
w2[pos&mm]=acc[2]
var x1=acc[0]+w2[(pos-this.dl0)&mm],x2=acc[1]+w2[(pos-this.dr0)&mm]
this.L=x1/(1+Math.abs(x1)*.45)*1.2;this.R=x2/(1+Math.abs(x2)*.45)*1.2}
}
class Lt extends AudioWorkletProcessor{constructor(){super(),this.E=new D(sampleRate),this.port.onmessage=t=>{var s=t.data||{};s.type=="state"?this.E.st(s.state):s.type=="play"?this.E.build():s.type=="stop"&&(this.E.playing=0)}}process(t,s){var i=s[0];if(!i||i.length<2)return!0;var h=i[0],n=i[1],r=this.E;if(!r)return!0;for(let o=0;o<h.length;o++)r.sp(),h[o]=r.L,n[o]=r.R;return!0}}
registerProcessor("atbs-v04",Lt);})();
