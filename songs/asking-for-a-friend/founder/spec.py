"""The founder (Asking for a Friend): the spec. CREATIVE.md section 5 is the direction:
same smooth stylized family as Claude, late thirties, inverted-triangle silhouette (broad shoulders, small head),
a big square-jawed grin, ONE signature: the glossy hair swoop that never moves. Cream and charcoal, ultraviolet accent.

Head parts reuse the studio's toon3d head (songs/great-idea-ted/toon3d: a real mouth with shape keys); the head spec
starts from Ted's and squares the jaw, enlarges the chin and the eyes, thickens the brows.
Metres, z up, the character faces -y, his left is +x. Feet on z = 0.
"""
ZM = -0.052     # the mouth line (head space)
HEAD = dict(
    cranium_c=(0, 0.014, 0.024), cranium=(0.090, 0.104, 0.104),
    jaw_y=-0.024, jaw_z=-0.050, jaw_half=(0.082, 0.072, 0.058), jaw_round=0.030, jaw_k=0.040,
    chin_y=-0.084, chin_z=-0.092, chin_r=(0.056, 0.028, 0.027), chin_k=0.016,
    cheek_x=0.056, cheek_y=-0.066, cheek_z=-0.010, cheek_r=(0.028, 0.024, 0.020), cheek_k=0.02,
    brow_ridge_x=0.046, brow_ridge_y=-0.086, brow_ridge_z=0.044, brow_ridge_r=0.016,
    nose_bridge=((0, -0.098, 0.020), (0, -0.114, -0.010), 0.0090, 0.0130),
    nose_tip=((0, -0.119, -0.017), 0.0160),
    ala_x=0.0150, ala_y=-0.106, ala_z=-0.026, ala_r=0.0100,
    mouth_z=ZM, mouth_w=0.043,
    lip_y=-0.101, ulip_dz=0.0036, ulip_r=(0.044, 0.0090, 0.0060), llip_dz=0.0058, llip_r=(0.040, 0.0100, 0.0075),
    eye_x=0.040, eye_y=-0.080, eye_z=0.012, eye_r=0.0240, socket=0.0, corner_r=0.0024,
    hinge_y=0.004, hinge_z=-0.012,
)
# big dark irises with a lot of gloss: the Claude family's eyes (his are near-black with a big catchlight)
EYE = dict(r=0.0240, iris='#4A3326', iris_angle=50, pupil_angle=24, lid_up=-30, lid_lo=42, tilt=0)
BROW = dict(x0=0.010, x1=0.068, z=0.046, arch=0.007, tilt=0.003, h0=0.0090, h1=0.0050, thick=0.0026, lift=0.0005)
EAR = dict(t=0.0075, w=0.022, h=0.033, x=0.093, y=0.014, z=-0.004, yaw=14, roll=-8)
# veneers: a slightly taller upper row than Ted's so the grin is a wall of teeth
TEETH = dict(yc=-0.0625, rho=0.0370, z_u=ZM - 0.0020, z_l=ZM - 0.0040, h=0.0150, d=0.0060)

# the hair under the swoop: a tight, short cap with a hard side part on his left (toon3d hair_sdf parameters)
HAIR = dict(
    center=(0, 0.014, 0.0),
    line=[(0, 40), (22, 40), (42, 36), (58, 30), (72, 20), (78, 6), (83, 3), (87, 18), (100, 22), (112, 16), (125, 2),
          (150, -14), (180, -22)],
    t_side=0.0035, t_top=0.0090, t_back_extra=0.0015, swoop_th=-14, swoop_w=42, swoop_ph=57, swoop_h=10, swoop_amp=0.0,
    part_th=34, part_w=1.6, part_depth=0.0035, part_flat=0.0020, edge_soft=3, edge_k=0.0030,
    pole_th=150, pole_ph=58, strands=26, groove=0.0006, step=0.0016,
)
COLORS = dict(skin='#C98D66', lips='#B9796A', lash='#1B1512', brow='#1E1A1A',
              hair_dark='#0D0D11', hair_light='#1F1F27',
              cream='#E8DFCC', charcoal='#2A2B30', uv='#4B2A7A', steel='#B9BCC4')

# ---------------------------------------------------------------- the body (standing, A-pose)
BODY = dict(
    head_center_z=1.690, head_pivot_z=1.570, neck_z=1.500, head_scale=1.07,
    shoulder_x=0.226, shoulder_z=1.432, delt_r=0.082, trap_r=0.052,
    chest_z=1.300, chest_w=0.205, chest_d=0.124, chest_h=0.165,
    waist_z=1.100, waist_w=0.138, waist_d=0.100,
    pelvis_z=0.975, pelvis_w=0.150, pelvis_d=0.104,
    upper_r=0.058, elbow_r=0.044, wrist_r=0.031, fore_r=0.050,
    thigh_r=0.090, knee_r=0.056, ankle_r=0.036,
    neck_r=0.064, hand_scale=1.12,
)
