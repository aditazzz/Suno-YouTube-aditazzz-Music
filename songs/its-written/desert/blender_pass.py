from pathlib import Path
import bpy, numpy as np, ctypes as C, math, sys, time, os, struct, zlib
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parent.parent;os.chdir(root)
bridge=C.CDLL(str(root/'work/scene_bridge_v3.dylib'))
flt=np.ctypeslib.ndpointer(dtype=np.float32,flags='C_CONTIGUOUS');integer=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS')
bridge.scene_frame.argtypes=[C.c_int,flt];bridge.scene_frame.restype=C.c_int
bridge.scene_ground.argtypes=[C.c_int,flt,flt];bridge.scene_walker.argtypes=[flt,integer];bridge.scene_grid.argtypes=[C.c_float,C.c_float,flt]
bridge.scene_init()
first=int(sys.argv[1]);width=int(sys.argv[2]);samples=int(sys.argv[3]);last=int(sys.argv[4]) if len(sys.argv)>4 else first
dest=Path(sys.argv[5]).resolve() if len(sys.argv)>5 else root/'work/look';dest.mkdir(exist_ok=True,parents=True)
physical=os.environ.get('GRAIN_PHYSICAL')=='1'
params=np.empty(30,'float32');triangle_count=bridge.scene_frame(first,params)
s=bpy.context.scene;bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
from cycles_device import configure
s.render.engine='CYCLES';configure(s);s.cycles.samples=samples;s.cycles.use_denoising=True;s.cycles.max_bounces=4;s.cycles.diffuse_bounces=3;s.cycles.glossy_bounces=2
s.render.threads_mode='FIXED';s.render.threads=8;s.render.resolution_x=width;s.render.resolution_y=round(width*9/16);s.render.resolution_percentage=100
s.render.use_persistent_data=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
if physical:
 import OpenImageIO as oi
 s.render.image_settings.media_type='MULTI_LAYER_IMAGE';s.render.image_settings.file_format='OPEN_EXR_MULTILAYER';s.render.image_settings.use_exr_interleave=True;s.render.image_settings.color_depth='16';s.render.image_settings.exr_codec='ZIP';s.view_layers[0].use_pass_z=True;s.render.film_transparent=True
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.51
def node(nt,kind):return nt.nodes.new(kind)
def inp(nt,target,index,value):
 if isinstance(value,bpy.types.NodeSocket):nt.links.new(value,target.inputs[index])
 else:target.inputs[index].default_value=value
def mathnode(nt,op,a,b=None):
 n=node(nt,'ShaderNodeMath');n.operation=op;inp(nt,n,0,a)
 if b is not None:inp(nt,n,1,b)
 return n.outputs[0]
def vec(nt,op,a,b):
 n=node(nt,'ShaderNodeVectorMath');n.operation=op;inp(nt,n,0,a);inp(nt,n,1,b);return n.outputs[0]
def tex(nt,path,vector,noncolor=False,clip=False):
 n=node(nt,'ShaderNodeTexImage');n.image=bpy.data.images.load(str(root/path),check_existing=True)
 if noncolor:n.image.colorspace_settings.name='Non-Color'
 if clip:n.extension='CLIP'
 inp(nt,n,'Vector',vector);return n.outputs['Color']
def separate(nt,x):
 n=node(nt,'ShaderNodeSeparateColor');inp(nt,n,0,x);return n.outputs
def material(name,base,rough=.75):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*base,1);p.inputs['Roughness'].default_value=rough;return m,p,m.node_tree
def geom(nt):return node(nt,'ShaderNodeNewGeometry').outputs['Position']
def coords(nt,src,scale,add):return vec(nt,'ADD',vec(nt,'MULTIPLY',src,scale),add)
def mixc(nt,fac,col1,col2):
 n=node(nt,'ShaderNodeMixRGB');inp(nt,n,0,fac);inp(nt,n,1,col1);inp(nt,n,2,col2);return n.outputs[0]
def noise(nt,co,scale,det=2):
 n=node(nt,'ShaderNodeTexNoise');n.inputs['Scale'].default_value=scale;n.inputs['Detail'].default_value=det;inp(nt,n,'Vector',co);return n.outputs['Fac']
def mesh_object(name,xyz,idx):
 mesh=bpy.data.meshes.new(name);mesh.vertices.add(len(xyz));mesh.vertices.foreach_set('co',xyz.ravel());mesh.loops.add(idx.size);mesh.loops.foreach_set('vertex_index',idx.ravel())
 mesh.polygons.add(len(idx));mesh.polygons.foreach_set('loop_start',np.arange(0,idx.size,idx.shape[1],dtype=np.int32));mesh.polygons.foreach_set('use_smooth',np.ones(len(idx),bool))
 mesh.update(calc_edges=True);o=bpy.data.objects.new(name,mesh);s.collection.objects.link(o);return o,mesh
def axis(ctr):
 a=[0]
 while a[-1]<380:a.append(a[-1]+min(2.5,.030+.014*abs(a[-1])))
 a=np.array(a);return np.r_[-a[:0:-1],a]+ctr
ax=axis(-3);ay=axis(.4);xx,yy=np.meshgrid(ax,ay)
xy=np.ascontiguousarray(np.stack([xx.ravel(),yy.ravel()],axis=1),'float32');z=np.empty(len(xy),'float32');bridge.scene_ground(len(xy),xy,z)
xyz=np.ascontiguousarray(np.column_stack([xy,z]),'float32');idx=np.arange(len(xy),dtype=np.int32).reshape(xx.shape);ids=np.stack([idx[:-1,:-1],idx[:-1,1:],idx[1:,1:],idx[1:,:-1]],2).reshape(-1,4)
ground,mesh=mesh_object('Aeolian sand relief',xyz,ids)
m,p,n=material('Blue-hour sand',(.26,.17,.098),.82);mesh.materials.append(m);pos=geom(n)
sand=tex(n,'work/ref/sand-color.jpg',coords(n,pos,(.73,.73,1),(.21,.31,0)))
sand=mixc(n,.64,(.17,.108,.066,1),sand);inp(n,p,'Base Color',sand)
path=tex(n,'work/maps/path.png',coords(n,pos,(1/24,1/8,0),(22/24,3.2/8,0)),True,True);maps=separate(n,path)
strength=mathnode(n,'ADD',mathnode(n,'MULTIPLY',maps[0],3.25),mathnode(n,'MULTIPLY',maps[1],.61))
clock=node(n,'ShaderNodeValue');trailfront=node(n,'ShaderNodeValue')
psep=node(n,'ShaderNodeSeparateXYZ');inp(n,psep,0,pos)
advance=mathnode(n,'MINIMUM',1,mathnode(n,'MAXIMUM',.015,mathnode(n,'MULTIPLY',8.0,mathnode(n,'SUBTRACT',trailfront.outputs[0],psep.outputs['X']))))
strength=mathnode(n,'MULTIPLY',strength,advance)
live=separate(n,tex(n,'work/maps/live.png',coords(n,pos,(1/13,1/13,0),(3/13,3/13,0)),True,True))
since=mathnode(n,'SUBTRACT',clock.outputs[0],mathnode(n,'MULTIPLY',live[1],12));valid=mathnode(n,'GREATER_THAN',since,-.0166)
decay=mathnode(n,'EXPONENT',mathnode(n,'MULTIPLY',mathnode(n,'MAXIMUM',since,0),-.43))
track=mathnode(n,'MULTIPLY',live[0],mathnode(n,'MULTIPLY',valid,mathnode(n,'MULTIPLY',decay,2.95)))
strength=mathnode(n,'ADD',strength,track)
ripple=tex(n,'work/maps/ripple.png',coords(n,pos,(1/2.36,1/2.36,0),(.121,.68,0)),True)
crest=mathnode(n,'MAXIMUM',0,mathnode(n,'SUBTRACT',ripple,.31));pflat=vec(n,'MULTIPLY',pos,(1,1,0));wavecontrols=[]
for i in range(3):
 center=node(n,'ShaderNodeCombineXYZ');age=node(n,'ShaderNodeValue');wavecontrols.append((center,age))
 rr=node(n,'ShaderNodeVectorMath');rr.operation='DISTANCE';inp(n,rr,0,pflat);inp(n,rr,1,center.outputs[0])
 front=mathnode(n,'SUBTRACT',rr.outputs['Value'],mathnode(n,'MULTIPLY',age.outputs[0],1.32))
 g=mathnode(n,'MULTIPLY',front,12.8);g=mathnode(n,'EXPONENT',mathnode(n,'MULTIPLY',-1,mathnode(n,'MULTIPLY',g,g)))
 curl=mathnode(n,'EXPONENT',mathnode(n,'MULTIPLY',age.outputs[0],-3.07))
 wave=mathnode(n,'MULTIPLY',g,mathnode(n,'MULTIPLY',curl,mathnode(n,'MULTIPLY',crest,2.7)));strength=mathnode(n,'ADD',strength,wave)
beatheat=node(n,'ShaderNodeValue')
gild=mathnode(n,'MULTIPLY',maps[1],mathnode(n,'MULTIPLY',crest,mathnode(n,'MULTIPLY',beatheat.outputs[0],2.13)))
strength=mathnode(n,'ADD',strength,gild)
inp(n,p,'Emission Color',(1,.43,.077,1));inp(n,p,'Emission Strength',strength)
micro=noise(n,pos,620,3.1);bn=node(n,'ShaderNodeBump');inp(n,bn,'Height',micro);bn.inputs['Strength'].default_value=.45;bn.inputs['Distance'].default_value=.00092
br=node(n,'ShaderNodeBump');inp(n,br,'Height',ripple);br.inputs['Strength'].default_value=.64;br.inputs['Distance'].default_value=.026;inp(n,br,'Normal',bn.outputs['Normal']);stampbump=node(n,'ShaderNodeBump');inp(n,stampbump,'Normal',br.outputs['Normal']);inp(n,stampbump,'Height',mathnode(n,'MULTIPLY',-1,mathnode(n,'MULTIPLY',live[0],valid)));stampbump.inputs['Distance'].default_value=.016;stampbump.inputs['Strength'].default_value=.78;inp(n,p,'Normal',stampbump.outputs['Normal'])
# Night sky with a long horizon of suspended dust. Diffuse rays receive a
# dimmer open-sky fill, with the sun and the active tracks carrying the key.
s.world.use_nodes=True;wn=s.world.node_tree;wn.nodes.clear();out=node(wn,'ShaderNodeOutputWorld');bg=node(wn,'ShaderNodeBackground');tc=node(wn,'ShaderNodeTexCoord');sep=node(wn,'ShaderNodeSeparateXYZ');inp(wn,sep,0,tc.outputs['Generated'])
ramp=node(wn,'ShaderNodeValToRGB');inp(wn,ramp,0,sep.outputs['Z']);ramp.color_ramp.elements[0].color=(.071,.080,.102,1);ramp.color_ramp.elements[1].color=(.004,.010,.027,1);ramp.color_ramp.elements[1].position=.32
inp(wn,bg,'Color',ramp.outputs['Color']);bg.inputs['Strength'].default_value=.78;inp(wn,out,0,bg.outputs[0])
def sun(name,direction,energy,col,angle):
 a=bpy.data.lights.new(name,'SUN');a.energy=energy;a.color=col;a.angle=angle;o=bpy.data.objects.new(name,a);s.collection.objects.link(o);o.rotation_euler=(-Vector(direction)).to_track_quat('-Z','Y').to_euler()
sun('Low desert moon',(-.86,.47,.28),1.68,(.66,.78,1),.095)
sun('Sand rim',(-.65,.76,.105),.68,(1,.67,.36),.046)
sun('Blue sky counterlight',(.34,.83,.36),.69,(.39,.61,1),.25)
lights=[]
for i in range(4):
 a=bpy.data.lights.new('Gold released at contact','POINT');a.color=(1,.45,.105);a.shadow_soft_size=.14
 o=bpy.data.objects.new(a.name,a);s.collection.objects.link(o);lights.append(o)
# A thin warm ground light grazes the written line and catches the surrounding troughs.
for i,(x,y) in enumerate([(-17,-.9),(-13,-.7),(-9,-.8),(-5,-.9)]):
 aa=np.zeros(3,'float32');bridge.scene_grid(x,y,aa)
 a=bpy.data.lights.new('Emissive sand bounce','POINT');a.energy=1.85;a.color=(1,.47,.13);a.shadow_soft_size=1.21
 ob=bpy.data.objects.new(a.name,a);s.collection.objects.link(ob);ob.location=(x,y,aa[0]+.14)
# The same animated sewn panels and knit hat are furnished in Cycles.
palette=[('Outer wrap',(.40,.306,.204)),('Coat sleeve',(.34,.242,.152)),('Scarf hood',(.47,.386,.278)),('Cord',(.32,.20,.09)),('Trousers',(.14,.102,.075)),('Boot leather',(.12,.066,.044)),('Gloves',(.23,.142,.079)),('Madder wool',(.64,.009,.021)),('Folded LOVE cuff',(.65,.008,.019)),('Wool pom',(.81,.70,.55)),('Loose scarf',(.49,.36,.205)),('Hem',(.25,.18,.12)),('Bag',(.22,.15,.078)),('Leather welt',(.074,.056,.040))]
materials=[]
for k,(name,color) in enumerate(palette):
 m,p,nt=material(name,color,.58 if k==5 else .81);materials.append(m);uv=node(nt,'ShaderNodeTexCoord').outputs['UV'];P=geom(nt)
 p.inputs['Sheen Weight'].default_value=.23 if k!=5 else .04;p.inputs['Sheen Roughness'].default_value=.55
 fib=noise(nt,P,780 if k!=5 else 320);bump=node(nt,'ShaderNodeBump');inp(nt,bump,'Height',fib);bump.inputs['Distance'].default_value=.00056;bump.inputs['Strength'].default_value=.21;inp(nt,p,'Normal',bump.outputs['Normal'])
 if k==8:
  label=tex(nt,'work/maps/love.png',coords(nt,uv,(1/.323,1/.87,0),(.5-.603/.323,1-.94/.87,0)),True,True);inp(nt,p,'Base Color',mixc(nt,label,(*color,1),(.96,.91,.80,1)))
 if k in (0,10):
  sep=node(nt,'ShaderNodeSeparateXYZ');inp(nt,sep,0,uv);V=sep.outputs['Y'];U=sep.outputs['X']
  band=mathnode(nt,'MULTIPLY',mathnode(nt,'GREATER_THAN',V,.020 if k==0 else .82),mathnode(nt,'LESS_THAN',V,.086 if k==0 else .92))
  diamonds=mathnode(nt,'SINE',mathnode(nt,'ADD',mathnode(nt,'MULTIPLY',U,303),mathnode(nt,'MULTIPLY',mathnode(nt,'ABSOLUTE',mathnode(nt,'SUBTRACT',V,.051)),129)))
  band=mathnode(nt,'MULTIPLY',band,mathnode(nt,'ADD',.56,mathnode(nt,'MULTIPLY',diamonds,.34)));inp(nt,p,'Base Color',mixc(nt,band,(*color,1),(.16,.105,.065,1)))
verts=raw_idx=actor=None
def pose(ntri):
 global verts,raw_idx,actor
 raw=np.empty((ntri,3,5),'float32');mat=np.empty(ntri,np.int32);bridge.scene_walker(raw,mat);raw=raw.reshape(-1,5)
 if actor is None:
  _,raw_idx,inv=np.unique(np.round(raw[:,:3],6),axis=0,return_index=True,return_inverse=True)
  actor,am=mesh_object('Traveller',np.ascontiguousarray(raw[raw_idx,:3]),inv.reshape(-1,3).astype('int32'))
  for a in materials:am.materials.append(a)
  am.polygons.foreach_set('material_index',mat);uv=am.uv_layers.new(name='Sewn panels');uv.data.foreach_set('uv',np.ascontiguousarray(raw[:,3:]).ravel())
 else:actor.data.vertices.foreach_set('co',np.ascontiguousarray(raw[raw_idx,:3]).ravel());actor.data.update()
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.lens=25.02;cam.data.sensor_width=36;cam.data.clip_start=.004;cam.data.clip_end=1800;cam.data.dof.use_dof=True;cam.data.dof.aperture_fstop=4.5
frame_list=[int(v) for v in os.environ['GRAIN_FRAMES'].split(',')] if os.environ.get('GRAIN_FRAMES') else range(first,last+1)
for fr in frame_list:
 if (dest/(("plate%04d.cp" if physical else "cycles-%04d.png")%fr)).is_file():continue
 N=bridge.scene_frame(fr,params)
 if N:pose(N)
 for k,o in enumerate(lights):
  x,y,age=params[18+3*k:21+3*k];aa=np.zeros(3,'float32');bridge.scene_grid(x,y,aa)
  o.location=(x,y,aa[0]+.065);o.data.energy=22.5*math.exp(-max(0,age)*2.77)
  if k<3:
   c,ag=wavecontrols[k];c.inputs['X'].default_value=float(x);c.inputs['Y'].default_value=float(y);ag.outputs[0].default_value=max(0,float(age))
 trailfront.outputs[0].default_value=float(params[18])+.12 if params[13]<2.38 else 100.0;clock.outputs[0].default_value=float(params[13]);beatheat.outputs[0].default_value=float(params[16])
 mat=np.eye(4);mat[:3,:3]=params[:9].reshape(3,3).T;mat[:3,3]=params[9:12];cam.matrix_world=Matrix(mat.tolist());cam.data.dof.focus_distance=float(params[12])
 s.render.filepath=str(dest/'framebuffer.exr' if physical else dest/('cycles-%04d.partial.png'%fr));tt=time.monotonic();bpy.ops.render.render(write_still=True)
 if physical:
  reader=oi.ImageInput.open(s.render.filepath);spec=reader.spec();channels=spec.channelnames;data=reader.read_image(format=oi.FLOAT);reader.close()
  def ch(k):return data[:,:,channels.index('ViewLayer.'+k)]
  packed=np.stack([ch('Combined.'+k) for k in 'RGBA']+[np.minimum(16000,ch('Depth.Z'))],axis=2)
  packed=np.ascontiguousarray(np.clip(packed,0,16000),dtype='<f2');h,w,_=packed.shape;raw=zlib.compress(packed.tobytes(),2)
  with open(dest/('plate%04d.partial'%fr),'wb') as file:file.write(struct.pack('<ii',w,h));file.write(raw)
  (dest/('plate%04d.partial'%fr)).replace(dest/('plate%04d.cp'%fr))
 if not physical:(dest/('cycles-%04d.partial.png'%fr)).replace(dest/('cycles-%04d.png'%fr))
 print('frame',fr,'seconds',round(time.monotonic()-tt,3),flush=True)
