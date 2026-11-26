#pragma once
#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <string>
#include <thread>
#include <vector>
using std::max;using std::min;
constexpr float PI=3.14159265359f, TAU=6.28318530718f;
struct V{
 float x=0,y=0,z=0;
 V()=default; V(float a):x(a),y(a),z(a){} V(float a,float b,float c):x(a),y(b),z(c){}
 V operator+(V b)const{return {x+b.x,y+b.y,z+b.z};} V operator-(V b)const{return {x-b.x,y-b.y,z-b.z};} V operator-()const{return {-x,-y,-z};}
 V operator*(float b)const{return {x*b,y*b,z*b};} V operator/(float b)const{return *this*(1/b);}V operator*(V b)const{return {x*b.x,y*b.y,z*b.z};}
 V&operator+=(V b){x+=b.x;y+=b.y;z+=b.z;return *this;}float& operator[](int i){return (&x)[i];} const float& operator[](int i)const{return (&x)[i];}
};
inline V operator*(float a,V v){return v*a;}
inline float dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}inline V cross(V a,V b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
inline float len(V p){return sqrtf(dot(p,p));}inline V norm(V p){return p/max(1e-15f,len(p));}
inline float sat(float x){return std::clamp(x,0.f,1.f);} inline float sm(float a,float b,float x){x=sat((x-a)/(b-a));return x*x*(3-2*x);}
inline float mix(float a,float b,float t){return a+(b-a)*t;}inline V mix(V a,V b,float t){return a+(b-a)*t;}
inline float frac(float x){return x-floorf(x);}inline float sq(float x){return x*x;}inline float gauss(float x){return expf(-x*x);} 
inline uint32_t hash32(uint32_t x){x ^= x>>16;x*=0x7feb352dU;x^=x>>15;x*=0x846ca68bU;return x^(x>>16);}
inline float hash(int x,int y,int s=0){return (hash32(uint32_t(x)*0x8da6b343u^uint32_t(y)*0xd8163841u^uint32_t(s)*0xcb1ab31fu)>>8)*(1.f/16777216.f);}
inline float noise(float x,float y,int s=0){int a=floorf(x),b=floorf(y);float u=sm(0,1,x-a),v=sm(0,1,y-b);return mix(mix(hash(a,b,s),hash(a+1,b,s),u),mix(hash(a,b+1,s),hash(a+1,b+1,s),u),v);}
struct Tex{
 struct Level{int w,h;std::vector<float>d;};int c=0;std::vector<Level>m;
 void load(const char*name,bool mip=true){std::ifstream f(std::string("work/maps/")+name+".map",std::ios::binary);int w=0,h=0;f.read((char*)&w,4);f.read((char*)&h,4);f.read((char*)&c,4);if(!f||w<1||c<1){std::cerr<<"missing map "<<name<<"\n";exit(2);}m.push_back({w,h,std::vector<float>((size_t)w*h*c)});f.read((char*)m[0].d.data(),m[0].d.size()*4);if(!f){std::cerr<<"truncated map "<<name<<"\n";exit(2);}while(mip&&w>1&&h>1){auto &p=m.back();int nw=w/2,nh=h/2;Level l{nw,nh,std::vector<float>(size_t(nw)*nh*c)};for(int y=0;y<nh;y++)for(int x=0;x<nw;x++)for(int k=0;k<c;k++){size_t j=((y*2)*w+x*2)*c+k;l.d[(y*nw+x)*c+k]=.25f*(p.d[j]+p.d[j+c]+p.d[j+w*c]+p.d[j+w*c+c]);}m.push_back(std::move(l));w=nw;h=nh;}}
 std::array<float,4> at(float u,float v,int l=0)const{
  if(!std::isfinite(u)||!std::isfinite(v))return {};
  const auto&p=m[std::clamp(l,0,int(m.size())-1)];
  u=frac(u)*p.w;v=frac(v)*p.h;
  // For tiny negative coordinates, float subtraction can round frac() to
  // exactly one. Keep the base tap in the texture and let its neighbour wrap.
  int x=std::clamp(int(u),0,p.w-1),y=std::clamp(int(v),0,p.h-1);
  float a=sat(u-x),b=sat(v-y);
  int x1=x+1==p.w?0:x+1,y1=y+1==p.h?0:y+1;
  int j=(y*p.w+x)*c,j1=(y*p.w+x1)*c,j2=(y1*p.w+x)*c,j3=(y1*p.w+x1)*c;
  std::array<float,4> res{};
  for(int k=0;k<c;k++)res[k]=mix(mix(p.d[j+k],p.d[j1+k],a),mix(p.d[j2+k],p.d[j3+k],a),b);
  return res;
 }
};
inline int mip(float pix,float texres,float size){return max(0,(int)floorf(log2f(max(1.f,pix*texres/size))));}
struct Ray{V o,d;};
thread_local float tracedDepth=1e8f,macroDepth=1e8f,defocus=0;thread_local bool insideGrain=false;
struct Camera{V o,aim,right,up,fw;float lens=1.39f,dist,sx=0,sy=0;
 Ray ray(float u,float v)const{return {o,norm(fw*lens+right*(u+sx)+up*(v+sy))};}
};
inline Camera camera(V target,float d,float angle,float elev,float roll,float lens=1.39f){
 Camera c;c.dist=d;c.aim=target;c.lens=lens;V offset={sinf(angle)*cosf(elev),-cosf(angle)*cosf(elev),sinf(elev)};c.o=target+offset*d;c.fw=-offset;V right=norm(cross(c.fw,{0,0,1})),up=cross(right,c.fw);c.right=right*cosf(roll)+up*sinf(roll);c.up=up*cosf(roll)-right*sinf(roll);return c;
}
struct Knot{float t,v;};
// Monotone cubic in log(distance), continuous velocity through each scale.
float curve(const std::vector<Knot>&p,float t,bool logvalue=false){
 auto v=[&](int i){return logvalue?logf(p[i].v):p[i].v;};int n=p.size(),i=0;while(i<n-2&&t>p[i+1].t)i++;
 auto slope=[&](int j){return (v(j+1)-v(j))/(p[j+1].t-p[j].t);};
 auto tangent=[&](int j){if(!j)return slope(0);if(j==n-1)return slope(n-2);float a=slope(j-1),b=slope(j);return (a*b<=0)?0.f:2*a*b/(a+b);};
 float dt=p[i+1].t-p[i].t,u=sat((t-p[i].t)/dt),u2=u*u,u3=u2*u;
 float a=(2*u3-3*u2+1)*v(i)+(u3-2*u2+u)*dt*tangent(i)+(-2*u3+3*u2)*v(i+1)+(u3-u2)*dt*tangent(i+1);
 return logvalue?expf(a):a;
}
struct Maps{Tex dune,humm,rip,sand,boot,trail,earth,cloud,love,grain,bed,light,geo,stellar,erg,galaxy,cities;void load(){dune.load("dunes2");humm.load("hummocks");rip.load("ripples");sand.load("sand");boot.load("bootsoft");trail.load("trail");earth.load("earth");cloud.load("clouds");love.load("love");grain.load("grains");bed.load("trailbed");light.load("mineralLight");geo.load("mineralGeo");stellar.load("stellar");erg.load("erg");galaxy.load("galaxy");cities.load("cities");}}M;
struct Accent{float t;int note;float strength;};std::vector<Accent>drumEvents;
struct Beat{float t;int bar,k;float onset,accent;};std::vector<Beat>beats;
struct Step{float x,y,angle,side,time;};std::vector<Step>written;
constexpr float PERIOD=20.7f, RADIUS=520.f;
V lodestar={-.085f,-.148f,0};
const V KEY=norm(V(-.83,.40,.32)), COOL=norm(V(.45,.9,.64));
struct Frame{
 int w,h;float t,q,groundGeo,mainDist,beatPhase,impact,answer,hat=0,kick=0,clap=0,tom=0;int bi;Camera main,inner;std::vector<Step>live;
};
