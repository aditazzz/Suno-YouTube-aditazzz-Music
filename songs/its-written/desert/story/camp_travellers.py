"""Seated company in the lamp light. Dimensions are in metres, facing local +Y."""
import math
import bpy
import numpy as np
from mathutils import Matrix
from world import obj, mesh_obj, material, unit
from camp_surfaces import fabric

ANGLE = np.arange(80) * math.tau / 80


def garment(name, root, rows, cloth, lining=None, trim=()):
    """Sew closed circumferences together and turn the selvage at selected rows."""
    n = len(rows[0])
    faces = [(j*n+i, j*n+(i+1)%n, (j+1)*n+(i+1)%n, (j+1)*n+i)
             for j in range(len(rows)-1) for i in range(n)]
    ob = mesh_obj(name, np.concatenate(rows), faces, cloth)
    ob.parent = root
    if lining:
        ob.data.materials.append(lining)
        for j in trim:
            for p in range(j*n, (j+1)*n):
                ob.data.polygons[p].material_index = 1
    return ob


def bent_cloth(name, root, path, widths, thicknesses, cloth, lining, phase):
    # Follow the bend of the knee or elbow with a continuous run of bias-cut cloth.
    t = np.linspace(0, 1, 41)
    xyz = np.array([np.interp(t, np.linspace(0, 1, len(path)), col)
                    for col in np.transpose(path)]).T
    for _ in range(4):
        xyz[1:-1] = (xyz[:-2]+2*xyz[1:-1]+xyz[2:])*.25
    tangent = unit(np.gradient(xyz, axis=0))
    rows = []
    for i, (at, forward) in enumerate(zip(xyz, tangent)):
        lateral = unit(np.cross(forward, [0, 0, 1]))
        up = unit(np.cross(lateral, forward))
        width, depth = [np.interp(t[i], np.linspace(0, 1, len(v)), v) for v in (widths, thicknesses)]
        tuck = 1 + .065*np.cos(5*ANGLE + 2*t[i]+phase) + .045*np.sin(38*t[i] + 2*np.sin(ANGLE))
        if i < 4:
            tuck *= [.035,.48,.78,.96][i]
        rows.append(at + tuck[:,None]*(width*np.cos(ANGLE)[:,None]*lateral + depth*np.sin(ANGLE)[:,None]*up))
    return garment(name, root, rows, cloth, lining, (36, 38))


def sculpt(root, source, name, skin):
    ob = obj(name, source.data, root)
    for slot in ob.material_slots:
        slot.link = 'OBJECT'
        slot.material = skin
    return ob


def traveller(stage, x, y, scale, heading, variant):
    root = obj('Seated traveller in a wool burnous', None)
    root.location = stage.ground(x, y, -.021)
    root.scale = (scale,)*3
    normal = unit([-(stage.floor(x+.05,y)-stage.floor(x-.05,y))/.1,
                   -(stage.floor(x,y+.05)-stage.floor(x,y-.05))/.1, 1])
    forward = np.array([-math.sin(heading),math.cos(heading),0.])
    right = unit(np.cross(forward,normal))
    root.rotation_euler = Matrix(np.column_stack([right,np.cross(normal,right),normal]).tolist()).to_euler()
    palette = [(.018,.032,.048), (.045,.026,.022), (.025,.034,.030)]
    colour = np.array(palette[variant % 3])
    outer = fabric('Wool mantle', tuple(colour))
    hood = fabric('Brushed wool hood', tuple(colour*1.18))
    edging = fabric('Turned wool selvage', tuple(colour*.72))
    trousers = fabric('Heavy woven trousers', tuple(colour*.60))
    for textile in (outer, hood, edging, trousers):
        textile.node_tree.nodes.get('Principled BSDF').inputs['Sheen Weight'].default_value = .055
    skin = material('Skin under the awning', (.113,.066,.046), rough=.86)
    shade = material('Face under the hood', (.020,.011,.008), rough=.93)
    a = ANGLE
    phase = variant*.85
    # Both shins cross in front. One passes under the other and both ankles tuck
    # away beneath the opposite knee. The robe drops over the backs of the thighs.
    for side in (-1,1):
        over = .036 if side == 1 else 0
        fore = .032 if side == 1 else -.034
        bent_cloth('Crossed trouser leg', root,
                   [(side*.098,-.060,.170), (side*.294,.080,.197),
                    (side*.377,.236,.168), (side*.288,.310+fore,.097+over),
                    (side*.084,.310+fore,.066+over), (-side*.221,.245+fore,.058+over*.3)],
                   [.113,.135,.116,.094,.085,.046], [.100,.103,.096,.081,.065,.044],
                   trousers, edging, phase)
    rows = []
    # Wide seated hem, hollow waist, shoulder break, gathered neck. Folds fan
    # over the knees and gather more densely towards the collar.
    for t in np.linspace(0,1,54):
        levels = [0,.13,.28,.42,.59,.75,.85,1]
        w = np.interp(t,levels,[.397,.396,.313,.233,.197,.232,.222,.097])
        d = np.interp(t,levels,[.295,.282,.235,.176,.142,.145,.121,.091])
        z = np.interp(t,levels,[.050,.119,.213,.278,.409,.560,.624,.707])
        front = np.maximum(0,np.sin(a))
        f = (1-.44*t)*(.018*np.sin(9*a+.9*t+phase)+.013*np.cos(5*a-2.85*t)+.005*np.sin(16*a+2*t))
        lift = (.110*front**2+.045*np.cos(2*a+phase))*(1-t)**2
        rows.append(np.c_[(w+f)*np.cos(a)-.017*t,
                          .034-.094*t+(d+.8*f)*np.sin(a), z+lift+.010*np.sin(6*a+2*t)*(1-t)])
    garment('Mantle falling from shoulders over the knees',root,rows,outer,edging,(1,3))
    # A second length of wool is thrown diagonally over one shoulder. Leave
    # the overlapping selvages open so the light catches the casting edges.
    wrap_rows = []
    for j, body in enumerate(rows):
        t = j/(len(rows)-1)
        u = np.linspace(0,1,88)
        theta = .59 + 1.21*t + phase*.19 + u*(math.tau-.70+.17*t)
        ix = (theta % math.tau)*len(a)/math.tau
        points = np.array([np.interp(ix, np.arange(len(a)+1), np.r_[col,col[0]])
                           for col in body.T]).T
        roll = (.010+.019*np.exp(-u*22)+.018*np.exp(-(1-u)*20)
                + .014*np.sin(4*theta-4*t+phase)*(1-.6*t))
        points[:,0] += roll*np.cos(theta)
        points[:,1] += roll*np.sin(theta)
        points[:,2] += (.015+.072*(1-t)**2*np.sin(theta+.8)+.010*np.cos(8*theta+2*t))
        wrap_rows.append(points)
    cols = len(wrap_rows[0])
    panels = [(j*cols+i,j*cols+i+1,(j+1)*cols+i+1,(j+1)*cols+i)
              for j in range(len(wrap_rows)-1) for i in range(cols-1)]
    wrap = mesh_obj('Overlapping diagonal front of the burnous',np.concatenate(wrap_rows),panels,hood)
    wrap.parent=root
    finish=wrap.modifiers.new('Folded wool edge','SOLIDIFY')
    finish.thickness=.004
    # Draped sleeves narrow from the shoulder to the wrist, turn at the elbow
    # and end on the lap. Use the stage's articulated hand sculpture at the cuff.
    for side, source in [(-1,'Rain hand R'),(1,'Rain hand L')]:
        wrist = np.array([side*(.084+.027*(variant%2)),.226,.301+(side==1)*.033])
        fore = np.array([side*.251,.151,.362])
        bent_cloth('Bent sleeve with turned cuff', root,
                   [(side*.127,-.061,.584),(side*.197,-.035,.566),(side*.245,-.004,.505),
                    (side*.282,.068,.370),fore,wrist],
                   [.060,.089,.092,.091,.081,.056],[.060,.084,.087,.081,.066,.043],outer,edging,phase)
        hand = sculpt(root,bpy.data.objects[source], 'Hand resting across the lap',skin)
        finger = unit(wrist-fore+[0,.090,.038])
        lateral = unit(np.cross([0,0,1],finger))
        frame = np.column_stack([finger*side,lateral*side,unit(np.cross(finger,lateral))])
        hand.rotation_euler = Matrix(frame.tolist()).to_euler()
        hand.location = wrist
        hand.scale = (.84,)*3
    # A real recessed face under the overhang gives a cheek, nose and brow in
    # profile. The neck wrap hides the chin and turns down across one shoulder.
    head = obj('Inclined hood and head',None,root)
    head.location = (-.021,-.041,.811)
    head.rotation_euler = (-.26-.075*(variant%2),.065*math.sin(phase+.7),.12*math.sin(phase+1.2))
    neutral = bpy.data.collections['Proxy head'].objects['Block head']
    face = sculpt(head,neutral,'Shadowed face inside the hood',shade)
    face.scale = (.85,.85,.92)
    face.location = (0,-.051,-.003)
    eyes = sculpt(head,bpy.data.collections['Proxy head'].objects['Block eyes'],'Eyes in shade',shade)
    eyes.location=face.location
    eyes.scale=face.scale
    face.rotation_euler.x=eyes.rotation_euler.x=-.11
    # Opening turns back to form a deep inner facing. The brow comes forward and
    # the peak falls back low. Slightly planar cheeks give the silhouette corners.
    rows = []
    sections = [(.102,.123,.071),(.107,.130,.127),(.113,.151,.151),
                (.121,.160,.136),(.143,.173,.052),(.137,.173,-.038),
                (.120,.141,-.112),(.076,.084,-.166),(.001,.001,-.196)]
    for j,(w,h,fwd) in enumerate(sections):
        side = np.sign(np.sin(a))*abs(np.sin(a))**.90
        vertical = np.cos(a)
        crease = 1+.033*np.cos(5*a+.65*j+phase)+.022*np.sin(3*a+.42*j)
        rows.append(np.c_[w*side*crease+.009*np.cos(a+.3*j),
                          fwd+.079*vertical*(1-j/9)+.012*np.cos(2*a+phase),
                          h*vertical*crease+.049 +.019*np.maximum(vertical,0)**9 - .014*j/8])
    garment('Projecting hood with folded interior facing',head,rows,hood,edging,(0,1,2))
    rows=[]
    for t in np.linspace(0,1,27):
        w = .112+.105*(1-t)**1.4
        d = .111+.046*(1-t)
        bias = .029*np.cos(a+1.8*t+phase)+.016*np.sin(2*a+2*t)
        tuck = .008*np.sin(16*t + 1.4*np.sin(a+.6))
        rows.append(np.c_[(w+tuck)*np.cos(a),-.042+(d+tuck)*np.sin(a),
                          .606+.158*t+bias+.020*t*np.sin(a)])
    garment('Bias-wrapped neckcloth falling over the shoulder',root,rows,hood,edging,(2,23))
    for child in root.children_recursive:
        if child.type=='MESH':child.pass_index=7
    return root
