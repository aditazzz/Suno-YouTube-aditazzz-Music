#include "traveller.hpp"
static Frame state;
extern "C" {
void scene_init(){
 M.load();const Tex*tm[]={&M.dune,&M.humm,&M.rip};for(int i=0;i<3;i++)baseline[i]=tm[i]->at(UO[i],VO[i])[0];std::ifstream bf("work/maps/timing.dat");Beat b;while(bf>>b.t>>b.bar>>b.k>>b.onset>>b.accent)beats.push_back(b);
}
int scene_frame(int frame,float*out){
 frameSetup(state,frame,1920,1080);walker.build(state,false);V axes[]={state.main.right,state.main.up,-state.main.fw,state.main.o};
 for(int j=0;j<4;j++)for(int k=0;k<3;k++)out[j*3+k]=axes[j][k];
 out[12]=state.main.dist;out[13]=state.t;out[14]=state.bi;out[15]=state.beatPhase;out[16]=state.impact;out[17]=state.answer;
 for(int j=0;j<4;j++){Step step=walkerStep(state.bi-j,0);out[18+3*j]=step.x;out[19+3*j]=step.y;out[20+3*j]=state.t-beats[max(0,state.bi-j)].t;}
 return int(walker.tri.size());
}
void scene_walker(float*out,int*materials){
 int k=0;for(auto&t:walker.tri){materials[k++]=t.mat;Vertex vertices[]={t.a,t.b,t.c};for(auto &v:vertices){*out++=v.p.x;*out++=v.p.y;*out++=v.p.z;*out++=v.u;*out++=v.v;}}
}
void scene_ground(int n,float*coords,float*out){
 for(int i=0;i<n;i++){float x=*coords++,y=*coords++;Land land=terrain(x,y,.0005f);*out++=land.z+oldSteps(x,y)[0]-.031f*(x*x+y*y)/(2*RADIUS);}
}
void scene_grid(float x,float y,float*out){auto p=terrain(x,y,.0005f);*out++=p.z;*out++=p.x;*out=p.y;}
}
