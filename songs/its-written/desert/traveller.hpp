#pragma once
#include "land.hpp"
struct Vertex{V p,n;float u,v;};
struct Triangle{Vertex a,b,c;int mat;V centre()const{return(a.p+b.p+c.p)/3;}};
struct Box{V lo=V(1e30f),hi=V(-1e30f);void add(V p){for(int i=0;i<3;i++){lo[i]=min(lo[i],p[i]);hi[i]=max(hi[i],p[i]);}}
 bool hit(Ray r,float mt)const{
  float t0=0,t1=mt;for(int i=0;i<3;i++){float inv=1.f/(fabsf(r.d[i])>1e-16f?r.d[i]:1e-16f);float a=(lo[i]-r.o[i])*inv,b=(hi[i]-r.o[i])*inv;if(a>b)std::swap(a,b);t0=max(t0,a);t1=min(t1,b);}return t1>=t0;
 }};
struct Node{Box box;int first=0,last=0,left=-1,right=-1;};
struct MeshHit{float t;V n;float u,v;int mat=-1;};
enum Material{COAT,SLEEVE,HOOD,CORD,TROUSERS,BOOT,GLOVE,KNIT,CUFF,POM,SCARF,HEM,BAG,WELT};
struct Walker{
 std::vector<Triangle>tri;std::vector<Node>bvh;V root,side,forward;float z0,t,phase;bool active=false;
 V world(V a)const{return root+side*a.x+forward*a.y+V(0,0,a.z);}
 void triangle(Vertex a,Vertex b,Vertex c,int mat){tri.push_back({a,b,c,mat});}
 template<class F>void surface(int nu,int nv,int mat,F pos,bool closed=true){
  std::vector<Vertex> grid((nu+1)*(nv+1));float e=.0002f;for(int j=0;j<=nv;j++)for(int i=0;i<=nu;i++){
   float u=float(i)/nu,v=float(j)/nv;V p=pos(u,v);
   V tu=pos(u+e,v)-pos(u-e,v),tv=pos(u,min(1.f,v+e))-pos(u,max(0.f,v-e));V n=norm(cross(tu,tv));grid[j*(nu+1)+i]={world(p),norm(side*n.x+forward*n.y+V(0,0,n.z)),u,v};
  }
  for(int j=0;j<nv;j++)for(int i=0;i<nu;i++){int a=j*(nu+1)+i,b=a+1,c=a+nu+1,d=c+1;triangle(grid[a],grid[b],grid[d],mat);triangle(grid[a],grid[d],grid[c],mat);}
 }
 void ellipsoid(V pos,V size,int mat,int N=32){surface(N,16,mat,[=](float u,float v){float th=TAU*(u-.5f),ph=(v-.5f)*PI;return pos+V(sinf(th)*cosf(ph)*size.x,-cosf(th)*cosf(ph)*size.y,sinf(ph)*size.z);});}
 void sleeve(V a,V b,float ra,float rb,int mat){V dir=norm(b-a),ax=norm(cross(dir,V(0,1,0)));if(len(ax)<.1)ax={1,0,0};V ay=norm(cross(dir,ax));
  surface(24,11,mat,[=](float u,float v){float th=TAU*u,rad=mix(ra,rb,v)*(1+.065f*sinf(5*th+3*v)+.045f*sinf(26*v+3*sinf(th)));return mix(a,b,v)+(ax*cosf(th)+ay*sinf(th))*rad;});
 }
 int makeNode(int a,int b){int index=bvh.size();bvh.push_back({});Box box;for(int i=a;i<b;i++){box.add(tri[i].a.p);box.add(tri[i].b.p);box.add(tri[i].c.p);}
  bvh[index].box=box;if(b-a<=8){bvh[index].first=a;bvh[index].last=b;return index;}
  V size=box.hi-box.lo;int k=size.y>size.x?1:0;if(size.z>size[k])k=2;int mid=(a+b)/2;
  std::nth_element(tri.begin()+a,tri.begin()+mid,tri.begin()+b,[k](const auto&l,const auto&r){return l.centre()[k]<r.centre()[k];});
  int l=makeNode(a,mid),r=makeNode(mid,b);bvh[index].left=l;bvh[index].right=r;return index;
 }
 bool intersect(Ray r,MeshHit&h,bool any=false)const{
  if(!active||!bvh[0].box.hit(r,h.t))return false;int stack[64]={0},nn=1;bool found=false;
  while(nn){const Node&nd=bvh[stack[--nn]];if(!nd.box.hit(r,h.t))continue;if(nd.left>=0){stack[nn++]=nd.left;stack[nn++]=nd.right;continue;}
   for(int i=nd.first;i<nd.last;i++){const auto&a=tri[i];V e=a.b.p-a.a.p,g=a.c.p-a.a.p,P=cross(r.d,g);float det=dot(e,P);if(fabsf(det)<1e-10)continue;float inv=1/det;V s=r.o-a.a.p;float u=dot(s,P)*inv;if(u<0||u>1)continue;V Q=cross(s,e);float v=dot(r.d,Q)*inv;if(v<0||u+v>1)continue;float tt=dot(g,Q)*inv;if(tt<=.00012f||tt>=h.t)continue;
    if(any)return true;h.t=tt;float w=1-u-v;h.n=norm(a.a.n*w+a.b.n*u+a.c.n*v);if(dot(h.n,r.d)>0)h.n=-h.n;h.u=a.a.u*w+a.b.u*u+a.c.u*v;h.v=a.a.v*w+a.b.v*u+a.c.v*v;h.mat=a.mat;found=true;
   }
  }return found;
 }
 void build(const Frame&f,bool sortTree=true){
  tri.clear();bvh.clear();active=f.t>1.15f&&f.t<9.25f;if(!active)return;
  t=f.t;int i=f.bi;float ph=f.beatPhase;phase=i+ph;
  auto a=walkerStep(i,0),b=walkerStep(i+1,0);V ac={a.x,a.y,0},bc={b.x,b.y,0};
  float distance=(phase-4.f)*.49f-.205f;V mid=route(distance);
  forward=norm(route(distance+.02f)-route(distance-.02f));side={forward.y,-forward.x,0};
  root=mid;root.z=terrain(mid.x,mid.y,.001f).z;float bob=.025f*sinf(PI*ph)-.014f*cosf(TAU*ph);
  for(int foot=0;foot<2;foot++){
   int last=(i%2==foot)?i:i-1;auto s0=walkerStep(last,0),s1=walkerStep(last+2,0);bool swing=last!=i;
   float lift=swing?.107f*sinf(PI*ph):0;float p=swing?sm(0,1,ph):0.f;
   V F=mix(V{s0.x,s0.y,0},V{s1.x,s1.y,0},p);
   float z=terrain(F.x,F.y,.001f).z-root.z+lift;float lx=dot(F-mid,side),ly=dot(F-mid,forward);
   // A separate welt, shaped toe box and cuff keep the planted boot readable.
   float pitch=swing?.12f*sinf(TAU*ph):0;
   surface(36,6,WELT,[=](float u,float v){float th=TAU*(u-.5f),along=-cosf(th),toe=.90f+.095f*along;
    return V(lx+.071f*sinf(th)*toe,ly+.162f*along,z+.012f+.025f*v+pitch*.12f*along);});
   ellipsoid({lx,ly+.009f,z+.065f},{.073f,.157f,.060f},BOOT,30);
   sleeve({lx,ly-.048f,z+.064f},{lx,ly-.045f,z+.178f},.062f,.068f,BOOT);
   sleeve({lx,ly-.045f,z+.163f},{lx,ly-.045f,z+.184f},.069f,.070f,WELT);
   V ankle={lx,ly-.047f,z+.115f},hip={foot?.096f:-.096f,0,.83f+bob};
   V knee=(hip+ankle)*.5f+V(0,.115f+.09f*(swing?sinf(PI*ph):0),.03f);
   sleeve(ankle,knee,.061f,.087f,TROUSERS);sleeve(knee,hip,.087f,.10f,TROUSERS);
  }
  float sway=.036f*sinf(phase*PI),turn=.09f*sinf(phase*PI);
  // Circular sewn panels fall from the shoulders in irregular axial folds.
  surface(76,36,COAT,[=](float u,float v){float th=TAU*(u-.5f);float hip=sm(.44,.76,v),neck=sm(.84,1,v);
   float w=.274f-.079f*hip+.034f*sm(.65,.86,v)-.119f*neck;float thick=.202f-.053f*hip-.054f*neck;
   float fold=(.020f*sinf(9*th+2.6f*v+turn)+.008f*sinf(17*th-3*v)+.006f*sinf(24*th+7*v))*(.55f+.6f*(1-v));
   float swing=(1-v)*(1-v)*(.044f*sinf(th*2+t*6)+.025f*sinf(4*th-t*5));
   return V(sway*v+(w+fold)*sinf(th)+swing,-(thick+fold)*cosf(th)-.055f*(1-v)+.055f*v,.47f+1.01f*v+bob+.026f*(1-v)*sinf(7*th+t*3));});
  for(int sign:{-1,1}){
   float swing=sign*.22f*cosf(phase*PI);V shoulder={sway+sign*.178f,.043f,1.36f+bob},elbow={sign*.228f,.025f+swing*.38f,1.12f+bob};
   V hand={sign*(.239f+.018f*sinf(t*4)),-.025f+swing,.919f+.064f*sq(swing/.22f)+bob};
   ellipsoid(shoulder+V(0,0,-.010f),{.099f,.091f,.081f},SLEEVE,26);sleeve(shoulder,elbow,.099,.077,SLEEVE);sleeve(elbow,hand,.077,.060,SLEEVE);ellipsoid(elbow,{.078f,.079f,.080f},SLEEVE,18);ellipsoid(hand+V(0,.012f,-.044f),{.039,.048,.066},GLOVE,20);ellipsoid(hand+V(-sign*.030f,.043f,-.022f),{.019,.021,.039},GLOVE,13);
  }
  // Folded hood draped across the back, a crossed sash and one loose woven end.
  surface(64,16,HOOD,[=](float u,float v){float th=TAU*(u-.5f);float back=.5f+.5f*cosf(th);float rad=mix(.101f,.20f,v)+.023f*sinf(PI*v);
   return V(sway+rad*sinf(th),.052f-rad*(.78f+.25f*back)*cosf(th),1.49f+bob-v*(.058f+.18f*back)+.018f*sinf(3*th+18*v)*sinf(PI*v));});
  surface(18,58,SCARF,[=](float u,float v){
   float gust=.43f+.44f*sinf(t*4.4f-.7f)+.13f*f.answer;
   float width=.074f*(1-.37f*v)*(1-.33f*sm(.84f,1.f,v));float edge=2*u-1;
   float twist=-.52f+v*2.71f+.71f*sinf(7*v-t*3.3f);
   float cx=sway-.077f-v*(.48f+.22f*gust)+.043f*v*sinf(7*v-t*4.8f);
   float cy=-.072f-v*.21f+.084f*sinf(7.2f*v-t*4.7f)*v;
   float cz=1.446f+bob-v*(.34f-.11f*gust)+.090f*sinf(8.3f*v-t*4.5f)*v;
   return V(cx+.014f*edge,cy+width*edge*cosf(twist),cz+width*edge*sinf(twist)+.010f*cosf(PI*edge)*sinf(13*v-2*t));},false);
  V head={sway,.065f,1.525f+bob};
  ellipsoid(head,{.109f,.108f,.153f},HOOD);
  // Wool crown and wide folded cuff; ribbing and yarn twist follow the surface.
  V hat=head+V(0,0,.054f);
  surface(112,30,KNIT,[=](float u,float v){float th=TAU*(u-.5f),rad=.127f*sqrtf(max(.0009f,1-v*v))*(1+.019f*cosf(34*th)+.018f*sinf(th*6+v*4));return hat+V(rad*sinf(th),-rad*.97f*cosf(th),.172f*v-.010f);});
  surface(120,12,CUFF,[=](float u,float v){float th=TAU*(u-.5f),rad=.131f+.006f*sinf(PI*v)+.0014f*cosf(64*th);return hat+V(rad*sinf(th),-rad*.98f*cosf(th),-.014f+.079f*v+.008f*cosf(th));});
  ellipsoid(hat+V(-.011f,.008f,.181f),{.050,.051,.048},POM,44);
  // A short pile halo gives the cream pom a soft boundary against dark sand.
  for(int j=0;j<70;j++){float z=2*hash(j,17)-1,ang=TAU*hash(j,23),rad=sqrtf(1-z*z);V off={cosf(ang)*rad,sinf(ang)*rad,z};V pp=hat+V(-.011f,.008f,.181f)+off*.044f;ellipsoid(pp,{.008,.0085,.008},POM,6);}
  if(sortTree)makeNode(0,tri.size());
 }
 V shade(Ray r,const MeshHit&h,const Frame&f)const{
  float noise1=noise(h.u*220,h.v*244,11);V albedo;float spec=.015f;float u=h.u,v=h.v;
  switch(h.mat){
   case KNIT:case CUFF:{
    float rib=.77f+.23f*cosf(TAU*64*u+.7f*sinf(v*68));albedo=V(.77,.014,.026)*rib*(.85f+.15f*noise1);
    if(h.mat==CUFF){float uu=(u-.603f)/.323f+.5f,vv=(.94f-v)/.87f;if(uu>0&&uu<1&&vv>0&&vv<1){float ink=M.love.at(uu,vv)[0];albedo=mix(albedo,V(.96,.87,.70),ink*.99f);}}
    break;}
   case POM: albedo=V(.90,.79,.59)*(.78f+.22f*noise1);break;
   case WELT:albedo={.081f,.065f,.050f};spec=.010f;break;
   case BOOT:albedo={.139,.078,.052};spec=.037f;break;
   case GLOVE:albedo={.25,.15,.089};break;
   case TROUSERS:albedo={.22,.176,.130};break;
   case HOOD:albedo=V(.55,.46,.33)*(.93f+.07f*cosf(125*v));break;
   case SCARF:albedo=mix(V(.43,.277,.139),V(.82,.64,.405),sm(.035,.12,min(u,1-u)));if(v>.89f)albedo=albedo*.70f;break;
   case SLEEVE:albedo={.51,.407,.284};break;
   default:{albedo={.65,.51,.342};float border=sm(.010,.016,v)*(1-sm(.084,.09,v));float woven=.5f+.5f*cosf(104*PI*u+40*fabsf(v-.054f));albedo=mix(albedo,V(.34,.247,.156)*(.62f+.65f*woven),border*.80f);break;}
  }
  float nd=max(0.f,dot(h.n,KEY)),R=powf(1-max(0.f,dot(h.n,-r.d)),3);
  V c=albedo*(V(.046,.064,.104)+V(.71,.52,.296)*nd+V(.060,.083,.119)*max(0.f,dot(h.n,COOL))*.75f);
  if(h.mat==KNIT||h.mat==CUFF)c+=albedo*V(.093,.043,.033);
  return c+V(.33,.24,.14)*R*.30f+V(spec)*powf(max(0.f,dot(h.n,norm(KEY-r.d))),18);
 }
}walker;
