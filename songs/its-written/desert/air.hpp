#pragma once
struct Pin{float x,y,z,lum,blue;};std::vector<Pin>pins;
struct Projection{float x,y,depth,scale;};
Projection project(const Camera&c,V p,int w,int h){V delta=p-c.o;float depth=dot(delta,c.fw),fac=.5f*w*c.lens/max(depth,.0001f);return {w*.5f+dot(delta,c.right)*fac-.5f*w*c.sx,h*.5f-dot(delta,c.up)*fac+.5f*w*c.sy,depth,fac};}
void lightPoint(Img&im,const std::vector<float>&depth,const std::vector<unsigned char>&domains,Projection p,float rad,float stretch,V color,bool macro,float threshold,float sx=1,float sy=0){
 if(p.depth<.00001f||rad<.16f)return;float extent=min(24.f,3.25f*rad*max(1.f,stretch));
 if(p.x< -extent||p.y< -extent||p.x>=im.w+extent||p.y>=im.h+extent)return;
 int x0=max(0,(int)floorf(p.x-extent)),x1=min(im.w-1,(int)ceilf(p.x+extent));
 int y0=max(0,(int)floorf(p.y-extent)),y1=min(im.h-1,(int)ceilf(p.y+extent));
 for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++){
  int i=y*im.w+x;if(bool(domains[i])!=macro||depth[i]+threshold<p.depth)continue;
  float dx=x+.5f-p.x,dy=y+.5f-p.y;float a=(dx*sx+dy*sy)/(rad*stretch),b=(-dx*sy+dy*sx)/rad;
  float d2=a*a+b*b;if(d2>9.5f)continue;im.d[i]+=color*expf(-d2);
 }
}
void atmosphere(Img&im,const Frame&f,const std::vector<float>&depth,const std::vector<unsigned char>&domains){
 float density=im.w/1920.f;
 if(f.t<1.75f||f.t>9.65f){
  float q=f.q,d=f.inner.dist,span=d*1.65f;V aim=f.inner.aim;
  int x0=floorf((aim.x-span)/MINTILE+.23f),x1=ceilf((aim.x+span)/MINTILE+.23f);
  int y0=floorf(-(aim.y+span)/MINTILE+.17f),y1=ceilf(-(aim.y-span)/MINTILE+.17f);
  // In the far exterior view of the primary quartz the whole inscription is a fleck.
  if(d>1.5f){x0=y0=1;x1=y1=0;}
  for(int ty=y0;ty<=y1;ty++)for(int tx=x0;tx<=x1;tx++)for(size_t j=0;j<pins.size();j++){
   const Pin&g=pins[j];float ran=hash(j+tx*31,ty,49);float illum=sm(-4.45,-1.88,q);
   if(illum>.5f&&g.lum<.89f&&ran<.54f)continue;
   float x=(tx+g.x-.23f)*MINTILE,y=-(ty+g.y-.17f)*MINTILE,z=bootFloor(x,y)+(g.z-.012f)*MINTILE+.00004f;
   auto p=project(f.inner,{x,y,z},im.w,im.h);if(p.x< -9||p.x>im.w+9||p.y< -9||p.y>im.h+9)continue;
   float strength=min(3.7f,g.lum);float rad=(.48f+.34f*min(2.6f,strength))*density;
   float r=max(.42f,rad);float energ=min(1.f,sq(rad/r));float visibility=1-sm(.52f,1.35f,q);
   float falloff=mix(1.f,min(1.f,sq(.14f/max(.04f,d))),illum);
   float shimmer=.86f+.12f*sinf(q*3.7f+ran*19+.94f*f.answer)+.20f*f.hat*sm(.54f,.89f,ran);
   V tint=mix(V(1.f,.71f,.38f),V(.63,.82f,1.f),sat((g.blue-.35f)*1.4f+.33f*ran));
   V radiance=tint*(strength*strength*.88f+.13f)*energ*visibility*falloff*shimmer;
   lightPoint(im,depth,domains,p,r,1,radiance,true,.0022f);
   if(strength>1.62f&&ran>.62f){
    lightPoint(im,depth,domains,p,max(.4f,.36f*r),3.65f,radiance*.27f,true,.0019f,.94f,.341f);
    lightPoint(im,depth,domains,p,max(.4f,.36f*r),2.65f,radiance*.18f,true,.0019f,-.341f,.94f);
    lightPoint(im,depth,domains,p,r*2.8f,1,radiance*.032f,true,.0024f);
   }
  }
 }
 // On bar 28 the dying image of Earth and one quartz highlight share
 // position and radiance. The lens diffraction outlives the resolved globe.
 if(f.t>15.36f&&f.t<19.55f){
  auto p=project(f.inner,lodestar,im.w,im.h);float gain=sm(15.36f,16.095f,f.t)*(1-sm(16.70f,19.55f,f.t));
  float radius=max(.51f,density*(1.52f+.78f*f.impact));V amber=V(2.15,1.21,.34)*gain;
  // Draw both visible portions at the common optical axis during hand-over.
  for(bool mac:{false,true}){
    lightPoint(im,depth,domains,p,radius,1,amber,mac,1e7f);
    lightPoint(im,depth,domains,p,radius*2.80f,1,amber*.20f,mac,1e7f);
    lightPoint(im,depth,domains,p,radius*.52f,5.9f,amber*.49f,mac,1e7f,.94f,.341f);
    lightPoint(im,depth,domains,p,radius*.45f,4.4f,amber*.31f,mac,1e7f,-.341f,.94f);
  }
 }
 if(f.t<1.65f||f.t>8.9f)return;
 for(int i=0;i<(int)beats.size();i++){
  float age=f.t-beats[i].t;if(age<-.017f||age>1.02f)continue;age=max(0.f,age);Step step=walkerStep(i,0);bool gust=beats[i].k%2==0;
  if(gust){
   // Saltation close to the ground: the wind picks up the heel's fine dust
   // and carries it over a neighbouring crest on the answering backbeat.
   float lift=sm(-.013f,.041f,age)*expf(-age*3.0f);
   for(int j=0;j<31;j++){
    float u=(j+.4f)/31.f,random=hash(i,j,202),travel=.22f+1.22f*u+1.76f*age;
    float x=step.x+travel*.93f+.081f*sinf(u*9-.6f),y=step.y+travel*.33f+.068f*sinf(4.8f*u+3.5f*age)+.039f*random;
    float z=terrain(x,y,.009f).z+.025f+.13f*sinf(PI*u)*(.46f+.54f*age)+.033f*age;
    Projection p=project(f.main,{x,y,z},im.w,im.h),pd=project(f.main,{x+.09f,y+.033f,z+.004f},im.w,im.h);
    float dx=pd.x-p.x,dy=pd.y-p.y,in=1/max(.001f,hypotf(dx,dy)),rad=max(.44f,min(5.5f*density,p.scale*(.011f+.016f*random)));
    float volume=lift*sinf(PI*u)*(.56f+.44f*random)*(.76f+.24f*f.clap);
    lightPoint(im,depth,domains,p,rad,2.8f,V(.041f,.029f,.016f)*volume,false,.055f,dx*in,dy*in);
   }
  }
  int count=gust?162:58;for(int j=0;j<count;j++){
   float a=hash(i,j,1),b=hash(i,j,34),h=hash(i,j,81),ang=hash(i,j,12)*TAU;
   float dt=age-.063f*a;if(dt<0)continue;float duration=.24f+.53f*b;if(dt>duration)continue;
   float x=step.x+.055f*cosf(ang)+(.08f+1.45f*a)*dt*(gust?1.65f:1.f)+.095f*sinf(14*dt+ang)*dt;
   float y=step.y+.055f*sinf(ang)+(.82f*sinf(ang)+.23f)*dt;
   float z=terrain(x,y,.003f).z+(.095f+.28f*h)*sinf(PI*dt/duration)+.012f;
   auto p=project(f.main,{x,y,z},im.w,im.h);
   float nominal=p.scale*(.0009f+.00124f*b);float rad=max(.40f,min(1.29f*density,nominal));
   float glint=(.30f+1.21f*powf(h,4))*sinf(PI*dt/duration)*min(1.f,sq(nominal/rad));
   lightPoint(im,depth,domains,p,rad,1.28f,V(1.46,.68,.17)*glint,false,.042f,.94f,-.342f);
  }
 }
}
