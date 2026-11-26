#pragma once
#include <zlib.h>
struct PhysicalPass{
 int w=0,h=0;std::vector<_Float16>d;
 bool load(int frame,const char*overrideDir=nullptr){
  char path[500];const char*dir=overrideDir?overrideDir:getenv("GRAIN_PLATES");snprintf(path,sizeof(path),"%s/plate%04d.cp",dir?dir:"work/physical",frame);std::ifstream fp(path,std::ios::binary);if(!fp)return false;
  fp.read((char*)&w,4);fp.read((char*)&h,4);if(!fp||w<1||h<1||w>8192)exit(8);
  fp.seekg(0,std::ios::end);size_t bytes=size_t(fp.tellg())-8;fp.seekg(8);
  std::vector<unsigned char>zip(bytes);fp.read((char*)zip.data(),bytes);d.resize(size_t(w)*h*5);uLongf count=d.size()*2;
  if(uncompress((Bytef*)d.data(),&count,zip.data(),zip.size())!=Z_OK||count!=d.size()*2){fprintf(stderr,"invalid physical pass %s\n",path);exit(8);}return true;
 }
 std::array<float,5> at(int xx,int yy,int W,int H)const{
  int ix=min(w-1,int((xx+.5f)*w/W)),iy=min(h-1,int((yy+.5f)*h/H));const _Float16*p=&d[(size_t(iy)*w+ix)*5];return {float(p[0]),float(p[1]),float(p[2]),float(p[3]),float(p[4])};
 }
};
