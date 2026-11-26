#pragma once
#include "land.hpp"
float stars(float x,float y,float cells,float pixel,int seed,float threshold,float&flash){
 float xx=x*cells,yy=y*cells;int ix=floorf(xx),iy=floorf(yy);float rand=hash(ix,iy,seed);if(rand<threshold)return 0;
 float u=frac(xx)-(.16f+.68f*hash(ix,iy,seed+4)),v=frac(yy)-(.16f+.68f*hash(ix,iy,seed+7));
 float rare=powf(rand,15);float sr=.009f+.029f*rare;
 float aa=max(sr,pixel*cells*.55f);float d=(u*u+v*v)/(aa*aa);if(d>22&&rare<.84f)return 0;
 float I=expf(-d)*min(1.f,sq(sr/aa))*(.32f+5.0f*rare);
 if(rare>.85f){float R=sr*.68f;float spike=(gauss(u/max(R,pixel*cells*.40f))*expf(-fabsf(v)/(sr*3.5f))+gauss(v/max(R,pixel*cells*.40f))*expf(-fabsf(u)/(sr*3.5f)))*.35f;I+=spike*rare;flash=max(flash,rare);}
 return I;
}
struct MacroSample{V color;float stars;};
constexpr float MINTILE=.119f;
inline float bootFloor(float x,float y){
 static const Step shoe={-.013f,.008f,1.20f,0,0},next={.344f,.175f,1.16f,1,0},prev={-.29f,-.47f,1.28f,1,0};
 float press=stamp(x,y,shoe,1.64f).depth+stamp(x,y,next,1.64f).depth*.78f+stamp(x,y,prev,1.64f).depth*.72f;return press*.49f+.0027f*sinf(96*y+25*x+1.7f*sinf(14*x))+.0017f*sinf(22*x-10*y);
}
inline float mineralFloor(float x,float y){return bootFloor(x,y)+(M.geo.at(x/MINTILE+.23f,-y/MINTILE+.17f,1)[0]-.012f)*MINTILE;}
MacroSample mineralWorld(Ray ray,const Frame&f){
 float q=f.q;float pix=max(.000012f,f.inner.dist*1.47f/f.w);
 Step shoe={-.013f,.008f,1.20f,0,0};float scale=1.64f,tile=.119f;
 auto base=bootFloor;
 auto relief=mineralFloor;
 float nearT=max(.0001f,(.018f-ray.o.z)/ray.d.z),farT=max(nearT+.002f,(-.047f-ray.o.z)/ray.d.z),t=nearT;
 for(int j=0;j<11;j++){
   V p=ray.o+ray.d*t;float gap=p.z-relief(p.x,p.y);if(gap<0){farT=t;break;}
   nearT=t;t+=max(.00035f,gap*.72f);
   if(t>farT){t=farT;break;}
 }
 for(int j=0;j<4;j++){float mid=(nearT+farT)*.5f;V p=ray.o+ray.d*mid;if(p.z>relief(p.x,p.y))nearT=mid;else farT=mid;}
 t=farT;macroDepth=t;V p=ray.o+ray.d*t;auto print=stamp(p.x,p.y,shoe,scale);float e=max(.00044f,pix*.57f);
 float du=(base(p.x+e,p.y)-base(p.x-e,p.y))/(2*e),dv=(base(p.x,p.y+e)-base(p.x,p.y-e))/(2*e);
 float gx=p.x/tile+.23f,gy=-p.y/tile+.17f;int lod=mip(pix,1024,tile);
 auto gm=M.geo.at(gx,gy,lod),lt=M.light.at(gx,gy,lod),pin=M.stellar.at(gx,gy);
 V n=norm({gm[1]-du*.94f,gm[2]-dv*.94f,gm[3]});V L=norm(V(-.89,.23,.25));float nd=max(0.f,dot(n,L));
 float direct=max(.015f,dot(norm(V(-du,-dv,1)),L));float edge=gauss((print.dist-.019f)/.15f);
 float ambocc=1-.56f*print.inside;float spec=powf(max(0.f,dot(n,norm(L-ray.d))),28);
 float photoLum=.34f*lt[0]+.51f*lt[1]+.15f*lt[2];
 V rock={lt[0],lt[1],lt[2]};float lum=.025f+.205f*direct+(.12f+.35f*direct)*edge;
 V body=rock*V(1,.81,.67)*lum*ambocc+V(.0038,.012,.026)*(.34f+gm[3]*.65f);
 body+=V(.74,.36,.088)*spec*(.12f+.42f*edge)+V(.51,.203,.032)*edge*(.14f+.75f*nd)*(.19f+.81f*photoLum);
 body+=V(.09,.041,.009)*print.tread*print.inside*(.7f+.3f*f.impact);
 // Point sources are pulled from real Cycles specular maxima in this exact bed.
 // As the raking illumination rises they become the glints on the grains.
 // The diffuse galactic dust sits behind the discrete foreground stars. Its
 // angular position rolls with the lens while the foreground has real parallax.
 float gu=.51f+atan2f(ray.d.x,ray.d.y)*.117f;
 float gv=.55f+.27f*ray.d.x+.21f*ray.d.y;
 auto galaxy=M.galaxy.at(gu,gv,0);
 V night=V(.0011,.0023,.0072)+V(galaxy[0]*galaxy[0],galaxy[1]*galaxy[1],galaxy[2]*galaxy[2])*V(.115,.102,.135);
 float distanceToStar=len(p-lodestar);
 float sweep=q+3.42f-(p.x+.44f*p.y)*2.65f-min(.42f,distanceToStar)*1.69f;
 float illum=sm(-1.22f,1.62f,sweep);
 float packed=.55f+.45f*sm(.18f,.68f,photoLum);float flatLight=max(0.f,dot(norm(V(-du,-dv,1)),L));
 V dustsand=V(.006,.009,.014)+V(.090,.053,.027)*flatLight*(.64f+.59f*noise(p.x*471,p.y*476,6));
 body=mix(dustsand,body,min(1.f,packed+.26f*edge));
 float footFar=stamp(p.x,p.y,Step{.344f,.175f,1.16f,1,0},1.64f).inside;
 float footBack=stamp(p.x,p.y,Step{-.29f,-.47f,1.28f,1,0},1.64f).inside;
 body+=V(.078,.031,.0055f)*(footFar+.51f*footBack);
 float dt=f.beatPhase*.575f,ax=(f.bi%2?.344f:-.013f),ay=(f.bi%2?.175f:.008f);
 float rr=hypotf(p.x-ax,p.y-ay);float wave=gauss((rr-dt*.60f-.009f*sinf(p.x*76+p.y*49))/.018f);
 body+=V(.17f,.075f,.014f)*wave*(.15f+.85f*nd)*expf(-dt*4.6f)*sm(-3.2f,-1.3f,q);
 // An advancing foot outside the crop briefly casts a soft-edged shadow
 // across the far lip, leaving the heel and forefoot relief in raking light.
 float limb=gauss((p.x-.21f+.025f*sinf((q+.02f)*TAU/.575f))/.10f)*sm(.08f,.28f,p.y);
 body=body*(1-.27f*limb*sm(-2.0f,-.66f,q));
 V color=mix(night,body,illum);
 color+=V(.115,.050,.010)*expf(-distanceToStar/.019f)*sm(-4.56f,-3.68f,q)*(1-.48f*illum);
 float st=0;float az=atan2f(ray.d.x,ray.d.y),el=asinf(std::clamp(ray.d.z,-1.f,1.f));
 float faint=stars(az,el,74.f,1.2f/f.w,37,.60f,st)*.16f+stars(az,el,151.f,1.2f/f.w,72,.59f,st)*.086f;
 color+=V(.66,.76,.91)*faint*(1-illum);
 color+=V(.058,.028,.006)*gauss((sweep-.06f)/.46f)*nd*sm(.11,.62,photoLum);
 float spark=0; return {color,spark};
}
bool grainShell(Ray r,const Camera&lens,float q,const Frame&f,float u,float v,V&color){
 // The host is a worn piece of quartz, clipped along actual fracture planes.
 // All crossings below are in 3-D, including rays starting inside the solid.
 V centre={0,0,.0028f};V rad={.0099f,.0074f,.0070f};
 const float twist=.36f,ct=cosf(twist),st=sinf(twist);
 auto local=[&](V p){return V((ct*p.x+st*p.y)/rad.x,(-st*p.x+ct*p.y)/rad.y,p.z/rad.z);};
 auto normalWorld=[&](V n){float x=n.x/rad.x,y=n.y/rad.y;return norm(V(ct*x-st*y,st*x+ct*y,n.z/rad.z));};
 V O=local(r.o-centre),D=local(r.d);
 float A=dot(D,D),B=dot(O,D),C=dot(O,O)-1,disc=B*B-A*C;if(disc<=0)return false;
 float enter=(-B-sqrtf(disc))/A,leave=(-B+sqrtf(disc))/A;if(leave<0)return false;
 struct Cut{V n;float h;};static const Cut cuts[]={
  {norm(V(-.66f,.25f,.86f)),.73f},{norm(V(.61f,.45f,.83f)),.77f},{norm(V(.95f,-.13f,.36f)),.86f},
  {norm(V(-.53f,-.71f,.54f)),.79f},{norm(V(.18f,-.89f,.45f)),.83f},{norm(V(.22f,.98f,.28f)),.85f},
  {norm(V(-.94f,-.20f,-.27f)),.88f},{norm(V(.61f,-.71f,-.46f)),.79f},{norm(V(-.11f,.38f,-.94f)),.76f}};
 for(auto&c:cuts){float k=dot(D,c.n),dist=c.h-dot(O,c.n);if(fabsf(k)<1e-9f){if(dist<0)return false;continue;}
  float t=dist/k;if(k>0)leave=min(leave,t);else enter=max(enter,t);
 }if(leave<=max(enter,0.f))return false;
 bool interior=enter<0;float hit=interior?leave:enter;V P=O+D*hit;
 V localN=norm(P);float nearPlane=fabsf(1-len(P)),nextPlane=4;
 for(auto&c:cuts){float dist=fabsf(dot(P,c.n)-c.h);if(dist<nearPlane){nextPlane=nearPlane;nearPlane=dist;}else if(dist<nextPlane)nextPlane=dist;}
 for(auto&c:cuts){float dist=fabsf(dot(P,c.n)-c.h);float w=(1-sm(.001f,.105f,dist))*sm(.61f,.81f,len(P));localN=norm(mix(localN,c.n,w*.95f));}
 float su=P.x+.42f*P.z,sv=P.y-.27f*P.z;float pit=noise(su*34,sv*31,68)-.50f;
 localN=norm(localN+V(.023f*pit,.018f*(noise(su*29,sv*36,112)-.5f),0));V n=normalWorld(localN);
 float incidence=sat(fabsf(dot(n,r.d))),fres=powf(1-incidence,2.1f);float opt=sm(-1.58f,-.18f,q);
 float bend=(interior?.024f:.13f)*opt;
 float offx=dot(n,lens.right)*bend+.010f*pit*opt,offy=dot(n,lens.up)*bend;
 // The exit-surface refraction moves the encased footprint with each facet.
 Ray ir=f.inner.ray(u+offx,v+offy);V under=mineralWorld(ir,f).color;
 float strata=noise(su*8.4f+.43f*P.z,sv*7.1f,74);
 float envelope=sm(.18f,.86f,noise(su*3.4f,sv*3.6f,17));float conch=len(V((P.x+.58f)*1.07f,(P.y-.38f),P.z*.38f));
 float strike=fabsf(sinf(41.f*conch+2.1f*strata+1.3f*P.z));float rib=expf(-sq(strike/.107f))*envelope*sm(.41f,.83f,conch);
 float fracture=gauss((su+.35f*sv+.31f+.13f*strata)/.009f)*sm(-.89,.38,sv);
 float lip=gauss(nextPlane/.019f)*sm(.70,.93,len(P));float nd=max(0.f,dot(n,KEY));
 V refl=r.d-n*(2*dot(r.d,n));float strip=powf(max(0.f,dot(refl,norm(V(-.55f,.35f,.74f)))),23)*(.47f+.53f*noise(su*4.6f,sv*5.3f,38));
 float ice=sm(.25,.85,noise(su*4.6f,sv*5.3f,11));
 V mineral=mix(V(.108,.050,.018),V(.113,.164,.198),ice)*(.36f+.9f*nd)+V(.39,.241,.10)*strip+V(.26,.169,.084)*fres;
 float opacity=interior?(.027f+.22f*fres):(.17f+.54f*fres+.14f*strata);
 color=mix(under,mineral,opacity*opt);
 color+=V(.62,.313,.081)*(rib*(interior?.07f:.17f)+fracture*.31f+lip*(interior?.16f:.35f)*(.36f+.64f*nd))*opt;
 // A few iron-gold inclusions run inside the volume, each on a different plane.
 for(int i=0;i<3;i++){V pl=norm(V(.32f+i*.22f,-.67f+i*.31f,.72f));float t=(.061f-.21f*i-dot(pl,O))/dot(pl,D);
  if(t<=max(enter,0.f)||t>=leave)continue;V w=O+D*t;
  float branch=w.x*.91f-w.y*(.20f+.17f*i)+.41f-.31f*i+.18f*sinf(4.8f*w.y+1.8f*i)+.067f*noise(w.y*31,w.z*28,66);
  float line=gauss(branch/(.0055f+.009f*noise(w.y*17,w.z*22,17)));
  float fade=sm(.1f,.74f,fabsf(w.y)+.4f*w.z)*sm(.15f,.8f,noise(w.y*3.2f,w.z*4.1f,47+i));
  color+=V(1.44,.67,.125)*line*fade*opt*(.82f+.25f*f.hat+.16f*f.kick);
 }
 return true;
}
