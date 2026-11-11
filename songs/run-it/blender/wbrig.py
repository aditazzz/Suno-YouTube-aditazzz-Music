"""Run It: posing her real Claude rig (same conventions as Asking for a Friend's rig_lib / anim_lib).
World-space targets; the armature may sit anywhere but is assumed unrotated except about Z."""
import bpy, math
from mathutils import Vector, Matrix, Euler, Quaternion
D = bpy.data
def upd(): bpy.context.view_layer.update()
class Rig:
    def __init__(self, arm=None):
        self.arm = arm or D.objects['RIG_Claude']; self.PB = self.arm.pose.bones; self.BB = self.arm.data.bones; self.O = D.objects
    def bone(self, name, off=(0, 0, 0), R=None, f=None):
        """rest head + offset in armature space, optional rotation (Matrix/Euler/Quaternion, armature axes) on top of rest."""
        rest = self.BB[name].matrix_local
        Rm = Matrix.Identity(4) if R is None else (R.to_matrix().to_4x4() if not isinstance(R, Matrix) else R.to_4x4())
        self.PB[name].matrix = Matrix.Translation(rest.translation + Vector(off)) @ Rm @ rest.to_3x3().to_4x4(); upd()
        if f is not None: self.PB[name].keyframe_insert('location', frame=f); self.PB[name].keyframe_insert('rotation_quaternion', frame=f)
    def at(self, name, world, R=None, f=None):
        """put a control bone's head at a world position."""
        p = self.arm.matrix_world.inverted() @ Vector(world); rest = self.BB[name].matrix_local.translation; self.bone(name, p - rest, R, f)
    def hand(self, s, world, R=None, f=None, pole=None):
        self.at('CTRL_hand_' + s, world, R, f)
        if pole is not None: self.at('POLE_elbow_' + s, pole, None, f)
    def foot(self, s, world, R=None, f=None): self.at('CTRL_foot_' + s, world, R, f)
    def hips(self, off=(0, 0, 0), R=None, f=None): self.bone('hips', off, R, f)
    def spine(self, lean=0.0, twist=0.0, side=0.0, f=None):
        """armature axes: lean + = forward (toward -Y), twist + = turn toward his left (screen right shoulder back), side = roll."""
        upd(); p = self.PB['spine']; rest = self.BB['spine'].matrix_local; cur = p.matrix.translation.copy()
        Rm = Matrix.Rotation(twist, 4, 'Z') @ Matrix.Rotation(side, 4, 'Y') @ Matrix.Rotation(lean, 4, 'X')
        loc0 = p.location.copy(); p.matrix = Matrix.Translation(cur) @ Rm @ rest.to_3x3().to_4x4(); p.location = loc0; upd()
        if f is not None: p.keyframe_insert('rotation_quaternion', frame=f)
    def obj(self, name, eul, f=None, path='rotation_euler'):
        o = self.O[name]; setattr(o, path, eul)
        if f is not None: o.keyframe_insert(path, frame=f)
    def head(self, eul, f=None): self.obj('head', eul, f); upd()     # x+ = nod down, z+ = turn toward +X, y = tilt
    def neck(self, eul, f=None): self.obj('neck', eul, f); upd()
    def lids(self, close=0.0, f=None, L=None, R=None):
        """0 = deadpan half-lidded rest, 1 = closed, negative = wider."""
        for s, c in (('L', close if L is None else L), ('R', close if R is None else R)): self.obj('lidpivot_' + s, (-0.567 + 1.82 * c, 0, 0), f)
    def brows(self, tilt=0.0, f=None, L=None, R=None):
        self.obj('browpivot_L', (0, math.radians(6 + (tilt if L is None else L)), 0), f); self.obj('browpivot_R', (0, math.radians(-6 - (tilt if R is None else R)), 0), f)
    def gaze_euler(self, target, s):
        eye = self.O['eye_' + s]; mw = eye.matrix_world; v = (mw.inverted().to_3x3() @ (Vector(target) - mw.translation)).normalized()
        return (-math.atan2(v.z, math.hypot(v.x, v.y)), 0.0, math.atan2(v.x, -v.y))
    def eyes(self, target, f=None, clamp=.62):
        upd()
        for s in 'LR':
            e = self.gaze_euler(target, s); e = (max(-clamp, min(clamp, e[0])), 0.0, max(-clamp, min(clamp, e[2]))); self.obj('aim_' + s, e, f)
    def fingers(self, s, curl=0.0, f=None, thumb=None, each=None):
        """curl in radians on top of the rest curl; each = dict finger->curl."""
        sg = -1 if s == 'L' else 1; Dg = math.radians
        for a in ('index', 'middle', 'ring'):
            c = (each or {}).get(a, curl); self.obj(f'{a}1_{s}', (0, sg * (Dg(14) + c), 0), f); self.obj(f'{a}2_{s}', (0, sg * (Dg(18) + 1.2 * c), 0), f)
        t = curl if thumb is None else thumb
        self.obj(f'thumb1_{s}', (Dg(-22) - .5 * t, sg * (Dg(26) + .4 * t), 0), f); self.obj(f'thumb2_{s}', (Dg(-6), sg * (Dg(16) + .5 * t), 0), f)
    def world(self, name): upd(); return self.O[name].matrix_world.copy()
    def bone_world(self, name): upd(); return self.arm.matrix_world @ self.PB[name].matrix
def RX(a): return Matrix.Rotation(a, 4, 'X')
def RY(a): return Matrix.Rotation(a, 4, 'Y')
def RZ(a): return Matrix.Rotation(a, 4, 'Z')
