#pragma once
#include "base.hpp"
struct Land{float z=0,x=0,y=0,occ=0,small=0;};
struct Print{float depth=0,inside=0,dist=4,tread=0;};
const float XL[3]={182.f,23.f,2.36f},UO[3]={.384f,.18f,.121f},VO[3]={.273f,.714f,.68f};
float baseline[3];
Land terrain(float x,float y,float pixel,bool detail=true){
 Land p;const Tex* maps[]={&M.dune,&M.humm,&M.rip};
 for(int i=0;i<(detail?3:2);i++){float keep=1-sm(XL[i]*.065f,XL[i]*.17f,pixel); if(keep<=0)continue;
  auto a=maps[i]->at(x/XL[i]+UO[i],y/XL[i]+VO[i],mip(pixel,1024,XL[i]));
  if(i==1){a[0]=baseline[i]+(a[0]-baseline[i])*.51f;a[1]*=.51f;a[2]*=.51f;a[3]*=.51f;}p.z+=(a[0]-baseline[i])*keep;p.x+=a[1]*keep;p.y+=a[2]*keep;p.occ=max(p.occ,a[3]*keep);if(i==2)p.small=a[0];
 }return p;
}
inline Print stamp(float x,float y,const Step&s,float scale=1){
 float dx=x-s.x,dy=y-s.y; float l=(dx*cosf(s.angle)+dy*sinf(s.angle))/(.147f*scale),w=(-dx*sinf(s.angle)+dy*cosf(s.angle))*(s.side?1:-1)/(.103f*scale);
 if(fabsf(l)>=.995f||fabsf(w)>=.998f)return {}; auto a=M.boot.at(.5f+.5f*w,.5f-.5f*l);
 return {a[0]*.036f*scale,a[3],a[1],a[2]};
}
V route(float d){
 float a=.47f,R=3.1f,turn=2.62f;
 if(d<0)return {d*.92f,d*.31f+.045f*sinf(d*2.4f),0};
 float e=min(turn,d),b=a+e/R;
 V point={R*(sinf(b)-sinf(a)),R*(cosf(a)-cosf(b)),0};
 return point+V(cosf(b),sinf(b),0)*max(0.f,d-turn);
}
Step walkerStep(int n,float at){
 float d=(n-4)*.49f;V p=route(d),fr=norm(route(d+.025f)-route(d-.025f));float side=n%2?.076f:-.076f;
 return {p.x+fr.y*side,p.y-fr.x*side,atan2f(fr.y,fr.x),float(n%2),at};
}
Print prints(float x,float y,const Frame&f){
 Print p;if(x>3||x< -3||y< -4||y>17)return p;
 for(const Step&s:f.live){if(fabsf(x-s.x)>.19f||fabsf(y-s.y)>.19f)continue;
  auto a=stamp(x,y,s);if(a.dist<p.dist)p=a;
 }return p;
}
inline std::array<float,4> oldSteps(float x,float y,int lod=0){
 if(x< -21.95f||x>1.95f||y< -3.15f||y>4.75f)return {};
 return M.bed.at((x+22)/24,(4.8f-y)/8,lod);
}
float grounds(float x,float y,float pix,const Frame&f){
 float micro=0;if(f.mainDist<.25f){float tile=.055f;auto a=M.geo.at(x/tile+.412f,-y/tile+.712f,mip(pix,1024,tile));micro=(a[0]-.012f)*tile*(1-sm(.035f,.25f,f.mainDist));}
 return micro+terrain(x,y,pix).z+prints(x,y,f).depth+oldSteps(x,y)[0]-(x*x+y*y)/(2*RADIUS)*(.031f+.969f*sm(7.45,9.0,f.t));
}
void frameSetup(Frame&f,int idx,int w,int h){
 f.w=w;f.h=h;f.t=idx/30.f;f.q=f.t>10?f.t-PERIOD:f.t;float t=f.t;
 f.bi=0;for(int i=0;i<(int)beats.size();i++)if(beats[i].t<=t+.5f/30)f.bi=i;
 Beat b=beats[f.bi];float next=f.bi+1<(int)beats.size()?beats[f.bi+1].t:b.t+.575f;
 f.beatPhase=sat((t-b.t)/(next-b.t));f.impact=expf(-max(0.f,t-b.t)*7.4f);
 f.answer=expf(-max(0.f,t-b.t)*4.f)*(b.k%2==0);
 for(auto&e:drumEvents){
  float age=t-e.t;if(age<-.5f/30.f||age>.65f)continue;age=max(0.f,age);
  if(e.note==42)f.hat=max(f.hat,e.strength*expf(-age*18));
  if(e.note==36)f.kick=max(f.kick,e.strength*expf(-age*7.8f));
  if(e.note==39)f.clap=max(f.clap,e.strength*expf(-age*12));
  if(e.note==50)f.tom=max(f.tom,e.strength*expf(-age*11));
 }

 static const std::vector<Knot> distance={{0,.0038},{.48,.0074},{.92,.016},{1.45,.124},{1.76,.59},{1.98,1.79},{2.30,5.12},{3.10,7.42},{4.3,9.14},{5.2,11.12},{6.04,14.1},{6.90,21.5},{8.0,26.9},{8.8,34},{9.55,82},{10.45,299},{11.50,1170},{12.56,1770},{13.43,2350},{14.35,5160},{15.20,13200},{16.1,80000},{18.60,380000},{20.7,999000}};
 float d=curve(distance,t,true);f.mainDist=d;
 float center=sm(3.8,6.95,t);float tx=-8.68f*center,ty=.13f*center+.57f*sm(2.05,3.35,t)*(1-center);
 float eye=(.035f+.65f*sm(1.67,2.65,t))*(1-sm(4.65,6.5,t));eye*=sm(1.52,2.37,t);
 float phi=-.49f+t*.068f,alt=(69.f-50.f*sm(1.65,3.13,t)+57.f*sm(3.68,6.80,t)+7.f*sm(8.4,11.35,t))*PI/180;
 float roll=(-8.f+9.f*sm(1,5.9,t)+1.55f*(t-6.9f)*sm(6.9,13,t))*PI/180;
 // Elevation measures distance above the tangent point. During orbital flight the
 // target gradually falls towards the centre so the globe can leave the horizon.
 tx-=.58f*sm(1.88,3.38,t)*(1-center);
 V aim={tx,ty,terrain(tx,ty,.004f).z+eye}; aim.z-=RADIUS*.90f*sm(9.62,13.05,t);
 float az=phi+.40f*sm(9.4,14.8,t);
 f.main=camera(aim,d,az,alt,roll);
 f.groundGeo=sm(9.1f,11.15f,t);
 // The return has its own physical scale. The same coordinates and camera curve
 // continue beyond the loop boundary, inside the larger grain.
 static const std::vector<Knot> innerD={{-11.f,.025},{-6.3f,.035},{-4.6f,.072},{-3.55f,.153},{-2.4f,.30},{-1.35f,.44},{0,.65},{1.05f,1.05},{2.0f,2.2},{10,3}};
 float q=f.q,di=curve(innerD,q,true);float expand=sm(-4.7,-.2,q);
 V it={-.085f+.075f*expand,-.148f+.14f*expand, .002f};
 if(q>.90f&&q<4)di*=mix(1.f,max(1.f,(d/.015f)/(di/1.0f)),sm(.90,1.57,q));
 f.inner=camera(it,di,-.55f+.105f*q,1.05f+.16f*expand,(-.20f+.036f*q),1.39f);
 // Project the centre of the vanishing Earth onto a particular real quartz highlight.
 if(t>12.0f){
  V pin=lodestar;V pp=pin-f.inner.o;float uz=dot(pp,f.inner.fw);
  V cp=V(0,0,-RADIUS)-f.main.o;float cz=dot(cp,f.main.fw),k=sm(12,15.85,t);
  f.main.sx=k*(dot(cp,f.main.right)*f.main.lens/cz-dot(pp,f.inner.right)*f.inner.lens/uz);
  f.main.sy=k*(dot(cp,f.main.up)*f.main.lens/cz-dot(pp,f.inner.up)*f.inner.lens/uz);
 }
 f.live.clear();for(int i=0;i<(int)beats.size();i++)if(beats[i].t<t+.5f/30&&beats[i].t<10.5f)f.live.push_back(walkerStep(i,beats[i].t));
}
struct Surface{bool hit=false;float t=1e30f;V pos,n;Land land;Print print;float pixel;};
Surface intersectLand(Ray r,const Frame&f){
 Surface s;float D=f.mainDist;float pix=max(1e-6f,D*1.52f/f.w);
 if(D<37.f){
  float k=0;bool grazing=r.d.z>-.57f;
  if(grazing){
   float prior=0;bool crossed=false;
   // Following the actual height field allows front ridges to hide farther
   // dunes, and lets the night sky open above the desert horizon.
   for(int i=0;i<104;i++){
    V p=r.o+r.d*k;float pixel=max(pix,k*1.49f/f.w);
    float h=grounds(p.x,p.y,pixel,f),delta=p.z-h;
    if(delta<.00002f+pixel*.15f){crossed=true;break;}
    prior=k;k+=max(.0025f,max(pixel*.45f,delta*.78f));
    if(k>155.f)break;
   }
   if(!crossed)return s;
   for(int j=0;j<4;j++){float m=(prior+k)*.5f;V p=r.o+r.d*m;if(p.z>grounds(p.x,p.y,max(pix,1.49f*m/f.w),f))prior=m;else k=m;}
  }else{
   k=max(.00001f,(f.main.aim.z-r.o.z)/r.d.z);
   for(int i=0;i<7;i++){V p=r.o+r.d*k;float h=grounds(p.x,p.y,pix,f);float delta=(h-p.z)/r.d.z;k=max(.000001f,k+delta*.81f);if(fabsf(delta)<pix*.16f)break;}
  }
  s.pos=r.o+r.d*k;s.t=k;s.hit=true;s.pixel=max(.000001f,1.48f*k/f.w);s.land=terrain(s.pos.x,s.pos.y,s.pixel);s.print=prints(s.pos.x,s.pos.y,f);
  float bend=.031f+.969f*sm(7.45,9.0,f.t);float nx=s.land.x-s.pos.x/RADIUS*bend,ny=s.land.y-s.pos.y/RADIUS*bend;
  auto old=oldSteps(s.pos.x,s.pos.y);if(s.print.dist<1.8f||fabsf(old[0])>.00002f){
    float e=max(.00065f,s.pixel*.55f);auto depth=[&](float x,float y){return prints(x,y,f).depth+oldSteps(x,y)[0];};
    nx+=(depth(s.pos.x+e,s.pos.y)-depth(s.pos.x-e,s.pos.y))/(2*e);ny+=(depth(s.pos.x,s.pos.y+e)-depth(s.pos.x,s.pos.y-e))/(2*e);
  }
  s.n=norm({-nx,-ny,1});return s;
 }
 V center={0,0,-RADIUS},op=r.o-center;float bb=dot(op,r.d),h2=RADIUS*RADIUS-dot(cross(op,r.d),cross(op,r.d));
 if(h2<=0)return s;float k=-bb-sqrtf(h2);if(k<=0)return s;
 V p=r.o+r.d*k;V n=norm(p-center);s.pixel=max(1e-5f,k*1.48f/f.w);
 float keep=(1-sm(60,460,D))*sm(.02,.33,n.z);
 if(keep>0){
  // Follow the same displaced surface as the low-altitude lens. Refinement
  // matters on the steep lee faces when the curvature first becomes visible.
  for(int i=0;i<5;i++){
   p=r.o+r.d*k;n=norm(p-center);s.land=terrain(p.x,p.y,s.pixel);
   float workHeight=s.land.z+oldSteps(p.x,p.y)[0];
   float gap=len(p-center)-RADIUS-workHeight*keep;float deriv=dot(n-V(s.land.x,s.land.y,0)*keep,r.d);
   float step=gap/min(-.065f,deriv);k-=std::clamp(step,-8.f,8.f);if(fabsf(step)<s.pixel*.12f)break;
  }
  p=r.o+r.d*k;n=norm(norm(p-center)+V(-s.land.x,-s.land.y,0)*keep);
 }
 s.n=n;s.t=k;s.pos=p;s.hit=true;return s;
}
inline float threadY(float x){
 float beyond=sm(0,46,max(-20.25f-x,x-3.0f));
 return .0765f*x+beyond*(5.5f*sinf(x*.042f+.36f)+2.36f*sinf(x*.118f-.71f)+.54f*sinf(x*.345f+1.3f))+.34f*beyond*(noise(x*.17f,2)-.5f);
}
V globeColor(Ray r,const Surface&s,const Frame&f){
 V n=norm(s.pos-V(0,0,-RADIUS));float lat=23.5f*PI/180,lon=11.0f*PI/180;
 V east={-sinf(lon),cosf(lon),0},up={cosf(lat)*cosf(lon),cosf(lat)*sinf(lon),sinf(lat)},north=cross(up,east);
 V g=east*n.x+north*n.y+up*n.z;float u=.5f+atan2f(g.y,g.x)/TAU,v=.5f-asinf(std::clamp(g.z,-1.f,1.f))/PI;
 int lod=mip(s.pixel,4096,2*PI*RADIUS);
 auto a=M.earth.at(u,v,lod);float land=sm(-.008,.15,a[0]-a[2]*.89f),arid=sm(.12,.42,a[0]-.32f*a[2]);
 float lum=(a[0]*.36f+a[1]*.51f+.13f*a[2]);
 V sun=norm(V(-.95,.31,-.24));float l=dot(n,sun);float light=sm(-.12,.64,l),limb=1-sat(dot(n,-r.d));float frontlight=sm(-.5,.96,l);
 V ocean=mix({.0019,.0085,.0185},{.010,.048,.072},light);
 V soil=mix({.022,.026,.030},{.36,.227,.122},light)*(.39f+1.46f*lum);
 V col=mix(ocean,soil,land);
 float cities=powf(max(0.f,M.cities.at(u,v,lod)[0]-.011f),.87f)*1.9f;float flick=.78f+.22f*f.impact;
 col+=V(2.4,1.06,.26)*cities*(.44f+.65f*(1-light))*flick;
 float longitude=atan2f(g.y,g.x)*180/PI,latitude=asinf(g.z)*180/PI;
 // An internal, branching golden current rises through the Sahara. The real
 // Nile and coastal lights continue independently from the night texture.
 float xx=n.x*RADIUS,yy=n.y*RADIUS;
 float gap=yy-threadY(xx),ends=sm(-23,-13,longitude)*(1-sm(28.3f,32.3f,longitude))*sm(.52f,.84f,n.z);
 float belt=gauss(gap/13.8f)*ends;
 float halfw=.37f+.25f*noise(xx*.13f,yy*.13f,16);
 float aa=min(1.9f,s.pixel*.56f);
 float vein=gauss(gap/(halfw+aa))*(.63f+.37f*halfw/(halfw+aa));
 float sparks=noise(xx*3.7f,yy*3.05f,91);float breath=.84f+.30f*f.impact;
 float wave=gauss((xx-66.f*(f.t-13.215f))/30.f);
 float dream=gauss((f.t-13.215f)/.41f),wind=gauss((f.t-14.80f)/.47f),road=gauss((f.t-15.95f)/.39f);
 col+=V(1.36,.589,.104)*ends*vein*(breath+.85f*wave+.30f*road);
 col+=V(.24,.105,.018)*belt*(.10f+.77f*sm(.68,.94,sparks))*(breath+.48f*wave);
 // Small eroded side channels part from the one walked line. Their much
 // lower radiance leaves the persistent trail visible at the orbital scale.
 for(int j=0;j<3;j++){float anchor=-133.f+j*88.f,d=xx-anchor;
   float stream=threadY(xx)+(j%2?1.f:-1.f)*(.27f*d+1.1f*sinf(d*.16f)+.43f*sinf(d*.47f));
   col+=V(.20,.080,.013)*gauss((yy-stream)/(.33f+aa))*sm(-1,7,d)*(1-sm(21,46,d))*ends;
 }
 // Underlit mineral seams follow actual mapped land; the Nile delta and
 // coastal settlements retain the topology of the night-light mosaic.
 float northern=gauss((latitude-24)/16.f)*gauss((longitude-10)/37.f)*land;
 float grainy=noise(longitude*16,latitude*17,76),lode=gauss((noise(longitude*.82f+2*noise(longitude*.23f,latitude*.23f),latitude*.84f,16)-.57f)/.049f);
 col+=V(.093,.042,.008)*northern*lode*(.2f+1.3f*sm(.47,.93,grainy))*(.54f+.42f*wave+.27f*dream);
 float clouds=M.cloud.at(u+.001f+(f.t-12)*.00027f,v,lod)[0];float cloudshade=M.cloud.at(u+.004f,v-.002f,lod)[0];
 col=col*(1.f-.31f*sm(.16,.75,cloudshade));
 col=mix(col,V(.117,.15,.18)*(.31f+1.73f*frontlight),sm(.025,.9,clouds)*(.75f+.07f*wind));
 float fres=powf(sat(limb),3.2f);col+=mix(V(.023,.103,.152),V(.62,.326,.11),sm(.1,.85,l))*fres*(.64f+.87f*frontlight);
 col+=V(1.6,.83,.25)*powf(limb,19)*sm(-.48,.68,l);
 return col;
}
float trailDist(float x,float y,float pixel){
 if(x< -21.9||x>1.9||y< -3.1||y>4.7)return 10;return M.trail.at((x+22)/24,(4.8f-y)/8,mip(pixel,3072,24))[0];
}
V sandColor(Ray r,Surface&s,const Frame&f){
 V p=s.pos;float px=s.pixel;V n=s.n;
 auto grain=M.sand.at(p.x*.83f+.32f,p.y*.83f+.53f,mip(px,1024,1.2f));
 float detail=(1-sm(.004f,.04f,px));n=norm(n+V((grain[1]-.5f)*.61f,(grain[2]-.5f)*.61f,0)*detail);
 float key=max(0.f,dot(n,KEY));float shadow=1-sm(.25,.59,s.land.occ);float direct=key*(.12f+.88f*shadow);
 float grit=.83f+.82f*(grain[0]-.26f);float pale=.65f+.35f*noise(p.x*.24,p.y*.24,37);
 V col=(V(.0034,.0064,.0125)*(.75f+.4f*n.z)+V(.090,.066,.048)*direct*sqrtf(key)*grit*pale);
 col+=V(.010,.020,.036)*powf(max(0.f,dot(n,COOL)),2.f)*(.24f+.76f*shadow);
 float fleck=sm(.122,.265,grain[0]-.22f)*(.4f+.6f*sq(max(0.f,dot(n,norm(KEY-r.d)))));
 col+=V(.091,.12,.145)*fleck*shadow*detail;
 float td=trailDist(p.x,p.y,px);
 float jitter=noise(p.x*22,p.y*22,38);
 float width=.023f+.016f*jitter+.009f*sinf(p.x*1.8+p.y);
 float d=max(0.f,td+.018f*(jitter-.5f));float trail=expf(-sq(d/(width+px*.58f)))*min(1.f,.060f/max(.001f,px));
 float heat=gauss(d/.16f),broad=gauss(d/.40f);
 float future=1.f;
 if(f.t<2.40f&&p.x>-2.5f){float edge=walkerStep(f.bi,0).x;future=.019f+.981f*sm(-.045f,.13f,edge-p.x+.065f);}
 float pathglow=(.46f+.62f*noise(p.x*9,p.y*9))*(.81f+.19f*sinf(p.x*.9f-f.t*4+p.y))*(1+.22f*f.impact);
 auto step=oldSteps(p.x,p.y,mip(px,3072,24));
 float mica=sm(.51,.93,noise(p.x*52,p.y*52,81));float chisel=.54f+.46f*sm(-.28,.53,dot(n,KEY));
 float crawl=gauss((f.t-6.88f-.030f*(p.x+10))/.37f);
 col+=(V(1.63f,.76f,.173f)*trail*pathglow*chisel+V(.123,.038,.006)*heat+V(.052,.019,.004)*broad)*future;
 col+=V(1.54,.66,.13)*step[1]*(.16f+.61f*step[2]+.40f*mica)*(.78f+.31f*crawl)*future;
 col+=V(.58,.28,.063)*mica*gauss(td/.105f)*sm(.32,.75,jitter)*future;
 // The first pen stroke has a longer, quieter approach winding through the dunes.
 if(p.x<-19.6f){
   float xx=p.x+20.25f,cy=threadY(p.x);
   float dist=fabsf(p.y-cy);float thin=gauss(dist/max(.049f,px))*.060f/max(.060f,px);
   col+=V(.98,.42,.082)*thin*sm(0,2,-xx);
 }
 if(f.t<10.2f&&p.x> -3&&p.x<5&&p.y>-5&&p.y<13){
  for(auto it=f.live.rbegin();it!=f.live.rend();++it){
   float age=max(0.f,f.t-it->time); if(age>2.4f)break;
   float dx=p.x-it->x,dy=p.y-it->y,rr=sqrtf(dx*dx+dy*dy);if(rr>2.8f)continue;
   float along=.82f*dx+.57f*dy,across=-.57f*dx+.82f*dy;
   float front=sqrtf(sq(along*.91f)+sq(across*1.29f));
   float wob=.045f*sinf(9*p.x+3*p.y)+.024f*sinf(13*p.y)+s.land.small*1.3f;
   float wave=gauss((front-age*1.44f-wob)/(.044f+.043f*age+px));
   float tail=gauss((front-age*1.03f-wob)/(.084f+.072f*age+px));
   float crest=sm(-.08f,.23f,s.land.small*49.f+s.land.x*.43f);
   float grains= .22f+.78f*sm(.32f,.79f,noise(p.x*26.f,p.y*25.f,44));
   float contact=gauss(rr/(.084f+.029f*age))*expf(-age*5.8f);
   col+=V(4.6f,2.12f,.41f)*contact;
   col+=V(.81f,.37f,.061f)*(wave*.77f+tail*.16f)*(.10f+.90f*crest)*grains*expf(-age*2.45f);
  }
  float glow=s.print.inside*(.16f+.57f*s.print.tread);col+=V(.74,.315,.064)*glow;
 }
 // Amber airborne highlights answer the offbeats along lee-facing ripple crests.
 float gust=sm(.55,.9,noise(p.x*4.1f-f.t*.8f,p.y*12.2f,5))*sm(.1,.4,key);
 col+=V(.042,.033,.020)*gust*f.answer;
 return col;
}
