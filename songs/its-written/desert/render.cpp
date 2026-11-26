#include "mineral.hpp"
#include "traveller.hpp"
#include <chrono>
#include <filesystem>
#include <sstream>
V microSand(Ray r,const Surface&s,const Frame&f,V base){
 float amt=1-sm(.034f,.39f,f.mainDist);if(amt<=0)return base;
 float tile=.055f,px=s.pixel;int lod=mip(px,1024,tile);
 float x=s.pos.x/tile+.412f,y=-s.pos.y/tile+.712f;
 auto g=M.geo.at(x,y,lod),l=M.light.at(x,y,lod);
 V n=norm(s.n+V(g[1],g[2],g[3]-1)*.88f);
 V c=V(l[0],l[1],l[2])*V(.20,.147,.113)*(.66f+.62f*max(0.f,dot(s.n,KEY)))+V(.0025,.006,.013);
 float dist=len(s.pos-V(0,0,.0034f));c+=V(.76,.332,.059)*expf(-dist/.014f)*(.18f+.68f*max(0.f,dot(n,norm(V(-s.pos.x,-s.pos.y,.004f)))));
 return mix(base,c,amt);
}
V desertSky(Ray r,const Frame&f){
 float az=atan2f(r.d.x,r.d.y),h=r.d.z;
 float rid=.006f+.013f*sinf(az*7+.58f)+.005f*sinf(az*24)+.002f*sinf(az*62+1.2f);
 float next=rid+.038f+.019f*sinf(5.6f*az+.3f)+.008f*sinf(az*29);
 float sunset=gauss((az+.60f)/.68f),haze=expf(-max(0.f,h)*9.4f);
 V sky=mix(V(.007,.017,.038),V(.067,.064,.068)+V(.09,.045,.01)*sunset,haze);
 if(h<rid)return mix(V(.012,.022,.038),V(.055,.064,.077),sm(-.15f,.08f,h))*.82f;
 if(h<next)return mix(V(.042,.049,.065),V(.087,.086,.096),sm(-.08f,.16f,h))*(.81f+.10f*noise(az*61,h*93));
 float flash=0;float points=stars(az,h,137.f,.00055f,616,.64f,flash);
 auto g=M.galaxy.at(.42f+.12f*az,.54f-.38f*h,1);
 return sky+V(g[0],g[1],g[2])*.027f+V(.61,.74,.87)*points*(.018f+.28f*sm(.055,.30,h));
}
V orbitalErg(const Surface&s,const Frame&f){
 float u=.51f+s.pos.x/1200.f,v=.55f-s.pos.y/804.f;
 auto a=M.erg.at(u,v,mip(s.pixel,2048,1200));
 float mid=sat((a[0]-.20f)*1.9f),ridge=max(0.f,a[1]);
 V c=mix(V(.007,.014,.026),V(.13,.095,.061),mid*mid)+V(.52,.32,.136)*ridge;
 float x=s.pos.x,cy=threadY(x);
 float thread=gauss((s.pos.y-cy)/max(.34f,s.pixel*.9f))*(.28f+.4f*noise(x*.81f,0))*sm(39,4,x);
 c+=V(1.5,.69,.14)*thread+.025f*V(1,.5,.15)*gauss((s.pos.y-cy)/4.f);
 return c;
}
V renderPixel(float u,float v,const Frame&f){
 Ray r=f.main.ray(u,v),ir=f.inner.ray(u,v);insideGrain=false;tracedDepth=1e8f;macroDepth=1e8f;defocus=0;
 V inner;bool innerLoaded=false;
 auto getInner=[&](){if(!innerLoaded){inner=mineralWorld(ir,f).color;innerLoaded=true;}return inner;};
 if(f.t>18.7f){
  V c=getInner();if(f.q> -1.45f){float q=f.q;auto cam=camera({0,0,terrain(0,0,.004f).z},.0038f*expf(q*1.36f),-.49f+q*.068f,69*PI/180,-8*PI/180);V shell; if(grainShell(cam.ray(u,v),cam,q,f,u,v,shell))c=shell;}
  insideGrain=true;return c;
 }
 if(f.t<1.9f){V c;if(grainShell(r,f.main,f.q,f,u,v,c)){insideGrain=true;return c;}}
 Surface s=intersectLand(r,f);
 MeshHit wh{s.t};if(walker.intersect(r,wh)){tracedDepth=wh.t;return walker.shade(r,wh,f);}
 if(s.hit){
  tracedDepth=s.t;  if(f.groundGeo>=.999f){V c=globeColor(r,s,f);if(f.t>16.1f){c=mix(c,getInner(),sm(16.10,17.23,f.t));if(f.t>16.9f)insideGrain=true;}return c;}
  V sand=sandColor(r,s,f);sand=microSand(r,s,f,sand);
  if(walker.active&&fabsf(s.pos.x-walker.root.x)<6.f&&fabsf(s.pos.y-walker.root.y)<6.f){
   Ray sh{s.pos+V(0,0,.010f),KEY};MeshHit h{8.f};if(walker.intersect(sh,h,true))sand=mix(sand*V(.28,.38,.60),V(.012,.021,.031),.13f);
  }
  float erg=sm(8.6f,9.85f,f.t)*(1-sm(9.95f,11.1f,f.t));
  if(erg>0)sand=mix(sand,orbitalErg(s,f),erg*.88f);
  if(f.t>1.8f&&f.t<5.6f){float mist=sm(10,143,s.t)*.79f;sand=mix(sand,V(.052,.062,.076),mist);}
  if(f.groundGeo<.001f)return sand;
  return mix(sand,globeColor(r,s,f),f.groundGeo);
 }
 if(f.t<9.65f)return desertSky(r,f);
 V bg=getInner();insideGrain=true;V ctr={0,0,-RADIUS},op=r.o-ctr;
 float off=len(cross(op,r.d))/RADIUS-1;V rim=norm(op+r.d*(-dot(op,r.d)));float sun=sm(-.4,.85,dot(rim,norm(V(-.91,.26,-.37))));
 float pix=f.mainDist/f.w/RADIUS;
 if(off>0){
  float halo=expf(-off/max(.012f,pix*.63f))*(.10f+.90f*sun)+.12f*expf(-off/.054f)*sun;
  bg+=mix(V(.072,.23,.32),V(1.3,.68,.21),sun)*halo*min(1.f,.2f/max(pix,.002f));
 }
 return bg;
}
int threads=8;
template<class F>void rows(int h,F work){std::atomic<int>next(0);std::vector<std::thread>pool;for(int k=0;k<threads;k++)pool.emplace_back([&]{for(;;){int y=next.fetch_add(1);if(y>=h)break;work(y);}});for(auto&t:pool)t.join();}
struct Img{int w,h;std::vector<V>d;V get(int x,int y)const{return d[min(h-1,max(0,y))*w+min(w-1,max(0,x))];}
 V at(float u,float v)const{float x=u*w-.5f,y=v*h-.5f;int i=floorf(x),j=floorf(y);return mix(mix(get(i,j),get(i+1,j),x-i),mix(get(i,j+1),get(i+1,j+1),x-i),y-j);}
};
#include "air.hpp"
#include "physical.hpp"
std::vector<unsigned char> frame(int idx,int w,int h,int spp){
 Frame f;frameSetup(f,idx,w,h);walker.build(f);Img orig{w,h,std::vector<V>((size_t)w*h)};
 std::vector<float>zbuf((size_t)w*h),coc((size_t)w*h);std::vector<unsigned char>domains((size_t)w*h);
 rows(h,[&](int y){for(int x=0;x<w;x++){V c;float z=0,blur=0;bool inner=false;for(int k=0;k<spp;k++){
  float dx=spp==1?.5f:frac(.19f+.618034f*k),dy=spp==1?.5f:frac(.39f+.414214f*k);
  float u=((x+dx)/w-.5f)*2,v=(.5f-(y+dy)/h)*2.f*h/w;V sample=renderPixel(u,v,f);
  if(!std::isfinite(sample.x)||!std::isfinite(sample.y)||!std::isfinite(sample.z)){
   fprintf(stderr,"invalid radiance in frame %d at %d,%d sample %d\n",idx,x,y,k);exit(9);
  }
  c+=sample;
  if(k==0){inner=insideGrain;const Camera&cam=inner?f.inner:f.main;Ray rr=cam.ray(u,v);z=(inner?macroDepth:tracedDepth)*dot(rr.d,cam.fw);
    float amp=inner?(sm(-4.0,-2.48,f.q)*22.f):(8.1f*(1-sm(.12f,.8f,f.mainDist))+2.75f*sm(1.55f,2.8f,f.t)*(1-sm(4.2f,6.15f,f.t)));
    float focus=(inner?.975f:.97f)*cam.dist;blur=min(9.5f,amp*fabsf(focus/max(.0001f,z)-1))*w/1920.f;
  }
 }int ix=y*w+x;orig.d[ix]=c/float(spp);zbuf[ix]=z;domains[ix]=inner;coc[ix]=blur;}});
 PhysicalPass plate;
 if(plate.load(idx)){
  float weight=.86f*sm(1.67f,2.36f,f.t)*(1-sm(8.62f,9.67f,f.t));
  rows(h,[&](int y){for(int x=0;x<w;x++){
   int i=y*w+x;auto a=plate.at(x,y,w,h);float u=(x+.5f)*2/w-1,v=(.5f-(y+.5f)/h)*2.f*h/w;
   Ray r=f.main.ray(u,v);float hot=sm(.15f,.81f,.28f*a[0]+.59f*a[1]+.13f*a[2]);V phys=V(a[0],a[1],a[2])*mix(V(.72f,.83f,1.06f),V(1.23f,1.12f,1.04f),hot);
   float fog=(1-expf(-max(0.f,a[4]-9.f)*.0125f))*a[3]*.82f;
   phys=mix(phys,V(.044f,.055f,.076f),fog);
   if(a[3]<1)phys+=desertSky(r,f)*(1-a[3]);
   orig.d[i]=mix(orig.d[i],phys,weight);if(weight>.45f&&a[3]>.62f){zbuf[i]=a[4]*dot(r.d,f.main.fw);domains[i]=0;}
  }});
 }
 PhysicalPass quartz;
 if(idx>=17&&idx<=53&&quartz.load(idx,"work/quartz")){
  float wgt=.86f*sm(.54f,1.05f,f.t)*(1-sm(1.48f,1.79f,f.t));
  rows(h,[&](int y){for(int x=0;x<w;x++){int i=y*w+x;auto q=quartz.at(x,y,w,h);if(q[3]<.001f)continue;
    float a=sat(q[3]);V warm=V(q[0],q[1],q[2])*V(.93f,.89f,.87f);
    orig.d[i]=mix(orig.d[i],warm+orig.d[i]*(1-a),wgt);
  }});
 }
 atmosphere(orig,f,zbuf,domains);
 if(f.t<5.9f||f.t>16.7f){Img focus=orig;rows(h,[&](int y){for(int x=0;x<w;x++){int i=y*w+x;float b=coc[i];if(b<.47f)continue;V col=orig.d[i]*.09f;
   for(int j=0;j<17;j++){float th=2.399963f*j,rad=b*sqrtf((j+.52f)/17.f);col+=orig.at((x+.5f+rad*cosf(th)*1.18f)/w,(y+.5f+rad*sinf(th))/h)*(.91f/17);}
   focus.d[i]=col;
 }});orig.d.swap(focus.d);}
 std::vector<Img> pyr;int pw=w,ph=h;
 for(int k=0;k<7&&ph>=6;k++){
  auto &src=k?pyr.back():orig;int nw=pw/2,nh=ph/2;Img half{nw,nh,std::vector<V>((size_t)nw*nh)};
  rows(nh,[&](int y){for(int x=0;x<nw;x++){V v=(src.get(x*2,y*2)+src.get(x*2+1,y*2)+src.get(x*2,y*2+1)+src.get(x*2+1,y*2+1))*.25f;if(!k){float lum=.28f*v.x+.57f*v.y+.15f*v.z;v=v*(max(0.f,lum-.16f)/(lum+.0001f));}half.d[y*nw+x]=v;}});
  Img blur{nw,nh,std::vector<V>((size_t)nw*nh)};rows(nh,[&](int y){for(int x=0;x<nw;x++){V s;for(int oy=-1;oy<=1;oy++)for(int ox=-1;ox<=1;ox++)s+=half.get(x+ox,y+oy)*((ox==0?2:1)*(oy==0?2:1)/16.f);blur.d[y*nw+x]=s;}});
  pyr.push_back(std::move(blur));pw=nw;ph=nh;
 }
 std::vector<unsigned char>result((size_t)w*h*3);
 rows(h,[&](int y){for(int x=0;x<w;x++){
  float u=(x+.5f)/w,v=(y+.5f)/h;V c=orig.d[y*w+x];V bloom;
  for(int j=0;j<(int)pyr.size();j++)bloom+=pyr[j].at(u,v)*(.105f+.012f*j);
  c+=bloom*V(1,.91,.75);float vig=1-.20f*(sq((u-.5f)*1.48f)+sq((v-.5f)*1.2f));c=c*vig;
  float grain=(hash(x,y,idx%31)-.5f)*1.55f;
  for(int k=0;k<3;k++){float z=max(0.f,c[k]*1.16f);float film=z*(2.1f*z+.18f)/(z*(2.05f*z+.74f)+.145f);float mapped=film<=.00313f?12.92f*film:1.055f*powf(film,.4166667f)-.055f;
   result[(y*w+x)*3+k]=(unsigned char)std::clamp(mapped*255+grain,0.f,255.f);}
 }});return result;
}
int main(int argc,char**argv){
 if(argc<7){fprintf(stderr,"width height start end stride prefix|pipe [samples] [threads]\n");return 2;}
 int w=atoi(argv[1]),h=atoi(argv[2]),start=atoi(argv[3]),end=atoi(argv[4]),stride=atoi(argv[5]);std::string target=argv[6];int samples=argc>7?atoi(argv[7]):1;if(argc>8)threads=atoi(argv[8]);M.load();
 const Tex* tm[]={&M.dune,&M.humm,&M.rip};for(int i=0;i<3;i++)baseline[i]=tm[i]->at(UO[i],VO[i])[0];
 std::ifstream bf("work/maps/timing.dat");Beat b;while(bf>>b.t>>b.bar>>b.k>>b.onset>>b.accent)beats.push_back(b);
 std::ifstream ef("work/maps/accents.dat");Accent ev;while(ef>>ev.t>>ev.note>>ev.strength)drumEvents.push_back(ev);
 std::ifstream pf("work/maps/pins.dat");Pin pin;while(pf>>pin.x>>pin.y>>pin.z>>pin.lum>>pin.blue)pins.push_back(pin);
 float nearest=1e9f;
 for(int tx=-2;tx<=0;tx++)for(int ty=0;ty<=2;ty++)for(auto g:pins){if(g.lum<1.3f)continue;float x=(tx+g.x-.23f)*MINTILE,y=-(ty+g.y-.17f)*MINTILE;float dist=sq(x+.085f)+sq(y+.148f);if(dist<nearest){nearest=dist;lodestar={x,y,bootFloor(x,y)+(g.z-.012f)*MINTILE+.00004f};}}
 std::vector<int> indices;if(const char*list=getenv("GRAIN_LIST")){std::istringstream ss(list);std::string val;while(std::getline(ss,val,','))indices.push_back(atoi(val.c_str()));}else{for(int i=start;i<=end;i+=stride)indices.push_back(i);}
 auto began=std::chrono::steady_clock::now();for(int i:indices){auto data=frame(i,w,h,samples);if(target=="pipe"){if(fwrite(data.data(),1,data.size(),stdout)!=data.size())return 3;}else{
  char n[64];snprintf(n,sizeof(n),"%04d.ppm",i);std::ofstream of(target+n,std::ios::binary);of<<"P6\n"<<w<<" "<<h<<"\n255\n";of.write((char*)data.data(),data.size());if(!of)return 4;
 }if(i==start||i==end||(i-start)/stride%20==0)fprintf(stderr,"frame %d, %.2fs elapsed\n",i,std::chrono::duration<double>(std::chrono::steady_clock::now()-began).count());}
}
