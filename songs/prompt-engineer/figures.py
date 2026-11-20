"""The cast and props, as stitch sprites."""
import numpy as np
from art import A, canvas, paste, recolor, flip, C, star8, text

# ----------------------------------------------------------------------------- small dancers (15 x 25)
_MAN_TOP = """
......WWW......
.....WWWWW.....
.....WWWWW.....
.....SSSSS.....
.....SeSeS.....
.....SSSSS.....
.....SKKKS.....
......SSS......
...WWKKWKKWW...
..WWWKGWGKWWW..
.WW.WKKWKKW.WW.
SW..WKGWGKW..WS
....WKKWKKW....
....RRRRRRR....
....RGRGRGR....
"""
_MAN_LEGS = ["""
....WWWWWWW....
....KWW.WWK....
....KWW.WWK....
....KWW.WWK....
....KWW.WWK....
....KWW.WWK....
....KWW.WWK....
....KWW.WWK....
....KWW.WWK....
...RKKK.KKKR...
""", """
....WWWWWWW....
....KWW.WWK....
....KWW.WWK....
....KWW.WWK....
....KWW.WWWK...
....KWW..WWK...
....KWW..KKKR..
....KWW........
....KWW........
...RKKK........
"""]
_WOMAN_TOP = """
......RRR......
.....RRRRR.....
....RRKKKRR....
....RSSSSSR....
....RSeSeSR....
.....SSSSS.....
.....SSPSS.....
......SSS......
...WWRRGRRWW...
..WWWRGGGRWWW..
.WW.WRRGRRW.WW.
SW..WRRRRRW..WS
....GGGGGGG....
....KKKRKKK....
...KKKRRRKKK...
...KKRRGRRKK...
..KKKRGGGRKKK..
..KKKRRGRRKKK..
..KKKKRRRKKKK..
.KKKKKKRKKKKKK.
.RRRRRRRRRRRRR.
.GKGKGKGKGKGKG.
.RRRRRRRRRRRRR.
"""
_WOMAN_FEET = ["""
....WW...WW....
...KKK...KKK...
""", """
....WW...KKK...
...KKK.........
"""]


def _stack(*parts):
    arrs = [A(p) if isinstance(p, str) else p for p in parts]
    w = max(a.shape[1] for a in arrs)
    out = canvas(w, sum(a.shape[0] for a in arrs))
    y = 0
    for a in arrs:
        out[y:y + a.shape[0], :a.shape[1]] = a
        y += a.shape[0]
    return out


def dancer(kind, pose):
    """kind 'm'/'w'; pose 0 both feet down, 1 right foot up, 2 both down, 3 left foot up. 15 x 25."""
    pose = pose % 4
    if kind == 'm':
        legs = A(_MAN_LEGS[0 if pose % 2 == 0 else 1])
        if pose == 3:
            legs = flip(legs)
        out = _stack(_MAN_TOP, legs)
    else:
        feet = A(_WOMAN_FEET[0 if pose % 2 == 0 else 1])
        if pose == 3:
            feet = flip(feet)
        out = _stack(_WOMAN_TOP, feet)
    if pose % 2:
        _lift_arms(out)
    return out


def _lift_arms(out):
    """Raise the forearms one row (the W hold swinging up on the hop). Rows 9-11, the outer three columns each side."""
    for cols in (slice(0, 3), slice(12, 15)):
        blk = out[9:12, cols].copy()
        out[9:12, cols] = 0
        out[8:11, cols] = np.where(blk > 0, blk, out[8:11, cols])


def dancer_lead(pose):
    """Lead man: free hand up, twirling the white handkerchief (shami)."""
    d = dancer('m', pose)
    out = canvas(15 + 5, 25 + 3)
    paste(out, d, 0, 3)
    # replace the right arm (viewer's right) with a raised arm
    out[3 + 8:3 + 12, 11:15] = 0
    out[3 + 8, 11] = C['white']
    arm = A("""
        ...WW
        ..WW.
        .WW..
        WW...
    """)
    paste(out, arm, 11, 3 + 6)
    out[3 + 5, 15] = C['skin']
    hk = [A("""
        .WWW.
        WWWWW
        .WWW.
        ..W..
    """), A("""
        WW...
        WWWW.
        .WWWW
        ..W..
    """)][(pose // 1) % 2]
    paste(out, hk, 13, 0 + 1)
    return out


# ----------------------------------------------------------------------------- hero figures (17 wide)
_HIM_HEAD = """
......KKKKK......
.....KKKKKKK.....
....KKKKKKKKK....
....KKKSSSKKK....
....KSSSSSSSK....
....SKKKSKKKS....
....SKbKKKbKS....
....SKKKSKKKS....
....SSSSSSSSS....
.....SSKKKSS.....
.....SSSSSSS.....
.......SSS.......
"""
_HIM_HOODIE = """
....yyyyyyyyy....
...yyyyyWyyyyy...
..yyyyyyWyyyyyy..
..yyyyyyyyyyyyy..
..yy.yyyyyyy.yy..
..yy.yyyyyyy.yy..
..yy.yyyyyyy.yy..
..yy.yydddyy.yy..
..yy.yydddyy.yy..
..SS.yyyyyyy.SS..
"""
_HIM_SUIT = """
....KKKWWWKKK....
...KKKKWRWKKKK...
..KKKKKWRWKKKKK..
..KKKKKWRWKKKKK..
..KK.KKWRWKK.KK..
..KK.KKKRKKK.KK..
..KK.KKKKKKK.KK..
..KK.KKKKKKK.KK..
..KK.KKKKKKK.KK..
..SS.KKKKKKK.SS..
"""
_HIM_LEGS = """
.....NNNNNNN.....
.....NNN.NNN.....
.....NNN.NNN.....
.....NNN.NNN.....
.....NNN.NNN.....
.....NNN.NNN.....
.....NNN.NNN.....
.....NNN.NNN.....
....WWWW.WWWW....
"""
_SUIT_LEGS = """
.....KKKKKKK.....
.....KKK.KKK.....
.....KKK.KKK.....
.....KKK.KKK.....
.....KKK.KKK.....
.....KKK.KKK.....
.....KKK.KKK.....
.....KKK.KKK.....
....KKKK.KKKK....
"""


def him(outfit="hoodie"):
    if outfit == "hoodie":
        return _stack(_HIM_HEAD, _HIM_HOODIE, _HIM_LEGS)
    return _stack(_HIM_HEAD, _HIM_SUIT, _SUIT_LEGS)


def him_plead(mouth=0, happy=0):
    """Hoodie; hands pressed together at his chest (please, please). mouth 1 = open (talking)."""
    s = him("hoodie")
    s[17:22, 2:4] = 0; s[17:22, 13:15] = 0          # lower arms come in to the chest
    s[16, 4] = C['grey']; s[16, 12] = C['grey']
    s[15:17, 7:10] = C['skin']
    if mouth:
        s[9, 7:10] = C['dred']; s[10, 7:10] = C['dred']
    if happy:
        s[9, 6] = C['black']; s[9, 10] = C['black']
    return s


def him_talk(mouth=0):
    """Suit, at the wedding. mouth 0 smile, 1 open."""
    s = him("suit")
    if mouth:
        s[9, 7:10] = C['dred']
        s[10, 7:10] = C['dred']
    return s


def him_shrug():
    """Suit; hands out, palms up (I talk to the computer)."""
    s = _stack(_HIM_HEAD, """
....KKKWWWKKK....
...KKKKWRWKKKK...
..KKKKKWRWKKKKK..
.KKK.KKWRWKK.KKK.
SKK..KKWRWKK..KKS
SS...KKKRKKK...SS
.....KKKKKKK.....
.....KKKKKKK.....
.....KKKKKKK.....
.....KKKKKKK.....
""", _SUIT_LEGS)
    return s


_MAMA = """
.....WWWWWWW.....
....WWRWWWRWW....
...WWWWWWWWWWW...
...WWyySSSyyWW...
...WWSSSSSSSWW...
...WSSeSSSeSSW...
...WSSSSSSSSSW...
...WSPSSSSSPSW...
....WSSRRRSSW....
....WWSSSSSWW....
.....WWWWWWW.....
......GGGGG......
...RRRRRRRRRRR...
..RRRRGRRRGRRRR..
.RRRRRRRRRRRRRRR.
.RRR.KKKKKKK.RRR.
.RRR.KGKKKGK.RRR.
.RRR.KKKRKKK.RRR.
.SS..KKRRRKK..SS.
....KKKKRKKKK....
....KGKKKKKGK....
...KKKKKKKKKKK...
...KKRKKRKKRKK...
...KKKKKKKKKKK...
..RRRRRRRRRRRRR..
..RGRGRGRGRGRGR..
..RRRRRRRRRRRRR..
.....KK...KK.....
....KKK...KKK....
"""


def mama(pose="stand"):
    s = A(_MAMA)
    if pose == "stand":
        return s
    out = canvas(21, 29)
    paste(out, s, 0, 0)
    if pose == "point":          # right arm (viewer's right) raised, finger up: listing instructions
        out[14:19, 13:17] = 0
        out[14, 13:15] = C['red']
        paste(out, A("""
            ....S
            ....S
            ...SS
            ..RR.
            .RRR.
            RRR..
        """), 13, 8)
    elif pose == "glass":        # raising a glass
        out[14:19, 13:17] = 0
        out[14, 13:15] = C['red']
        paste(out, GLASS_ARM("R"), 13, 5)
    elif pose == "ask":          # hand out toward him, palm up
        out[14:19, 13:17] = 0
        out[14, 13:15] = C['red']
        paste(out, A("""
            RRRR..
            .RRRSS
        """), 13, 15)
    return out


_UNCLE = """
......WWWWW......
.....WWWWWWW.....
.....WWWWWWW.....
....ySSSSSSSy....
....SKKSSSKKS....
....SSeSSSeSS....
....SSSSsSSSS....
....SKKKKKKKS....
....KKKSSSKKK....
.....SSSSSSS.....
.......SSS.......
...KKKWWWWWKKK...
..KKKKWWWWWKKKK..
.WWKKGWWWWWGKKWW.
.WWKKKWWWWWKKKWW.
.WWKKGWWWWWGKKWW.
.WWKKKWWWWWKKKWW.
.WW.RRRRRRRRR.WW.
.SS.RRGRGRGRR.SS.
....RRRRRRRRR....
....ddddddddd....
....dddd.dddd....
....dddd.dddd....
....dddd.dddd....
....dddd.dddd....
....dddd.dddd....
....dddd.dddd....
...RKKKK.KKKKR...
"""


def uncle(pose="stand"):
    s = A(_UNCLE)
    if pose == "stand":
        return s
    out = canvas(21, 31)
    paste(out, s, 2, 3)
    if pose in ("yell", "yell2"):       # both arms up, mouth open
        out[3 + 13:3 + 19, 2 + 1:2 + 3] = 0
        out[3 + 13:3 + 19, 2 + 14:2 + 16] = 0
        dy = 0 if pose == "yell" else 1
        armL = A("""
            SS...
            WW...
            WW...
            .WW..
            ..WW.
            ...WW
        """)
        paste(out, armL, 0, 3 + 7 + dy)
        paste(out, flip(armL), 16, 3 + 7 + dy)
        out[3 + 9, 2 + 7:2 + 10] = C['dred']      # open mouth under the moustache
        out[3 + 10, 2 + 7:2 + 10] = C['dred'] if pose == "yell" else C['skin']
    elif pose == "glass":
        out[3 + 13:3 + 19, 2 + 14:2 + 16] = 0
        paste(out, GLASS_ARM("W"), 2 + 13, 3 + 4)
    return out


# ----------------------------------------------------------------------------- the star (the model)
def star(mood="plain", r=6):
    """Eight-point kilim star with a face: the model. moods: plain, happy, wig (expert lawyer), breath, sad."""
    if mood == "breath":
        r = r + 1
    s = star8(r, 'terra')
    n = 2 * r + 1
    pad = 6
    out = canvas(n + 2 * pad, n + 2 * pad)
    paste(out, s, pad, pad)
    cx = cy = pad + r
    for ex in (cx - 2, cx + 2):
        out[cy - 1, ex] = C['eyet']
    if mood in ("happy", "wig"):
        out[cy + 2, cx - 1:cx + 2] = C['black']
        out[cy + 1, cx - 2] = C['black']; out[cy + 1, cx + 2] = C['black']
    elif mood == "plain":
        out[cy + 2, cx - 1:cx + 2] = C['black']
    elif mood == "sad":
        out[cy + 2, cx - 1:cx + 2] = C['black']
        out[cy + 3, cx - 2] = C['black']; out[cy + 3, cx + 2] = C['black']
    elif mood == "breath":
        out[cy + 1:cy + 4, cx - 1:cx + 2] = C['black']
        out[cy + 2, cx] = C['dred']
    if mood == "happy":
        for dx, dy in ((-r - 3, -r), (r + 3, -r), (-r - 4, 3), (r + 4, 3)):
            out[cy + dy - 1:cy + dy + 2, cx + dx] = C['gold']
            out[cy + dy, cx + dx - 1:cx + dx + 2] = C['gold']
    if mood == "wig":
        wig = A("""
            ....WWWWWWWWW....
            ..WWWWWWWWWWWWW..
            .WWWWWWWWWWWWWWW.
            .WWWW.......WWWW.
            .yyyy.......yyyy.
            .WWWW.......WWWW.
            .yyyy.......yyyy.
            .WWWW.......WWWW.
            .yyyy.......yyyy.
            .WWWW.......WWWW.
            .yyyy.......yyyy.
            .WWW.........WWW.
        """)
        paste(out, wig, cx - 8, cy - r - 3)
        out[cy - r:cy - r + 1, cx - 1:cx + 2] = C['white']
    return out


def gavel():
    return A("""
        .nnnnn...
        .nnnnn...
        ..nn.....
        ...nn....
        ....nn...
        .....nn..
        ......nn.
        .........
        nnnnnnn..
        nnnnnnn..
    """)


# ----------------------------------------------------------------------------- sets: bedroom
def bed(awake=0):
    """Bed, side on; he sits up in it. awake 0 = asleep (head on pillow), 1 = sitting up stretching, 2 = arms down."""
    out = canvas(46, 30)
    # headboard + frame
    out[6:26, 0:3] = C['brown']
    out[20:23, 3:44] = C['brown']
    out[23:29, 1:3] = C['brown']; out[23:29, 41:43] = C['brown']
    out[12:26, 43:45] = C['brown']
    # mattress + pillow
    out[17:20, 3:43] = C['white']
    out[13:17, 4:13] = C['white']; out[12, 5:12] = C['white']
    # blanket: red with kilim stripes
    out[13:20, 14:43] = C['red']
    out[14, 14:43] = C['black']; out[18, 14:43] = C['black']
    for x in range(15, 43, 4):
        out[16, x:x + 2] = C['gold']
    if awake == 0:
        # asleep: head on the pillow, hair on top, eyes closed
        head = A("""
            .KKKKK.
            KKSSSKK
            KSSSSSS
            SKKSKKS
            SSSSSSS
            .SSSSS.
        """)
        paste(out, head, 5, 7)
        out[13:15, 12:16] = C['grey']   # shoulder under blanket
    else:
        head = A("""
            ...KKKKK...
            ..KKKKKKK..
            .KKKKKKKKK.
            .KKKSSSKKK.
            .KSSSSSSSK.
            .SKKKSKKKS.
            .SKbKKKbKS.
            .SKKKSKKKS.
            .SSSSSSSSS.
            ..SSKKKSS..
            ..SSSSSSS..
            ....SSS....
        """)
        if awake == 1:
            head[9, 4:7] = C['dred']; head[10, 4:7] = C['dred']   # yawn
        hx = 10
        paste(out, head, hx, -1 + 1)
        body = A("""
            .yyyyyyyyy.
            yyyyyWyyyyy
            yyyyyWyyyyy
        """)
        paste(out, body, hx, 12 - 1 + 1)
        out[13:15, 14:22] = C['grey']
        if awake == 1:      # arms stretched up
            armL = A("""
                SS.
                yy.
                yy.
                .yy
                .yy
                .yy
            """)
            paste(out, armL, hx - 3, 5)
            paste(out, flip(armL), hx + 11, 5)
        else:
            out[13:17, hx - 1:hx + 1] = C['grey']
            out[13:17, hx + 11:hx + 13] = C['grey']
            out[17, hx - 1:hx + 1] = C['skin']; out[17, hx + 11:hx + 13] = C['skin']
    return out


def house_window(open_=0):
    """A wooden window with green shutters. open_ 0 closed, 1 half, 2 open with the morning outside. 44 x 34."""
    out = canvas(44, 34)
    # frame
    out[2:32, 10:34] = C['brown']
    if open_ == 0:
        out[4:30, 12:32] = C['green']
        out[4:30, 21:23] = C['brown']
        for y in range(6, 29, 3):
            out[y, 13:21] = C['lgreen']; out[y, 23:31] = C['lgreen']
    else:
        out[4:30, 12:32] = C['sky']
        # sun + rays
        sun = A("""
            ..YYYY..
            .YYYYYY.
            YYYYYYYY
            YYYYYYYY
            YYYYYYYY
            YYYYYYYY
            .YYYYYY.
            ..YYYY..
        """)
        paste(out, sun[1:7, 1:7], 23, 6)
        for (x, y) in ((25, 5), (26, 5), (25, 13), (26, 13), (30, 8), (30, 10)):
            out[y, x] = C['gold']
        out[9:11, 13:19] = C['white']; out[8, 14:17] = C['white']     # a cloud
        # hills
        for x in range(12, 32):
            hgt = int(4 + 2.5 * np.sin((x - 12) / 4.0) + 1.5 * np.sin((x - 12) / 1.7))
            out[30 - hgt:30, x] = C['green']
        # mullions
        out[4:30, 21:22] = C['brown']
        sw = 5 if open_ == 1 else 9
        for side in (0, 1):
            x0 = 10 - sw if side == 0 else 34
            out[3:31, x0:x0 + sw] = C['green']
            for y in range(6, 29, 3):
                out[y, x0 + 1:x0 + sw - 1] = C['lgreen']
    # sill with a flower pot
    out[32:34, 7:37] = C['brown']
    return out


def laptop_back(w=15, h=9):
    out = canvas(w, h)
    out[:, :] = C['silver']
    out[0, 0] = 0; out[0, -1] = 0
    out[-1, :] = C['grey']
    return out


def desk_scene(pose="type"):
    """He sits behind his desk, laptop lid toward us. poses: type, surgeon, crack. 41 x 40."""
    out = canvas(41, 40)
    cx = 20
    # the chair he sits on: back rail and posts behind his shoulders, legs under the desk
    out[12:14, cx - 11:cx + 12] = C['lbrown']
    out[12:27, cx - 11:cx - 9] = C['lbrown']; out[12:27, cx + 10:cx + 12] = C['lbrown']
    out[28:39, cx - 8:cx - 6] = C['lbrown']; out[28:39, cx + 7:cx + 9] = C['lbrown']
    out[28:30, cx - 8:cx + 9] = C['lbrown']
    head = A(_HIM_HEAD)
    paste(out, head, cx - 8, 2)
    body = A("""
        ....yyyyyyyyy....
        ...yyyyyWyyyyy...
        ..yyyyyyWyyyyyy..
        ..yyyyyyyyyyyyy..
        ..yyyyyyyyyyyyy..
        ..yyyyyyyyyyyyy..
        ..yyyyyyyyyyyyy..
        ..yyyyyyyyyyyyy..
        ..yyyyyyyyyyyyy..
        ..yyyyyyyyyyyyy..
    """)
    paste(out, body, cx - 8, 14)
    # chair back behind him
    # desk
    out[26:28, 1:40] = C['brown']
    out[28:39, 3:5] = C['brown']; out[28:39, 36:38] = C['brown']
    # his legs under the desk
    out[28:37, cx - 3:cx] = C['navy']; out[28:37, cx + 1:cx + 4] = C['navy']
    out[37:39, cx - 4:cx] = C['white']; out[37:39, cx + 1:cx + 5] = C['white']
    # laptop on the desk
    lap = laptop_back(15, 8)
    paste(out, lap, cx - 7, 18, mask=False)
    # mug with steam
    out[23:26, 33:36] = C['red']; out[24, 36] = C['red']
    out[20, 34] = C['white']; out[21, 35] = C['white']; out[19, 35] = C['white']
    # lamp
    out[25, 4:9] = C['dgrey']
    out[14:25, 6] = C['dgrey']
    out[11:14, 4:10] = C['gold']; out[10, 5:9] = C['gold']
    if pose == "type":
        out[18:24, cx - 10:cx - 8] = C['grey']; out[18:24, cx + 9:cx + 11] = C['grey']
        out[24:26, cx - 10:cx - 7] = C['skin']; out[24:26, cx + 8:cx + 11] = C['skin']
    elif pose == "surgeon":     # scrubbed-in: forearms up, hands at head height
        for side in (-1, 1):
            xs = cx + side * 9 + (0 if side > 0 else -1)
            out[16:19, min(xs, xs + side * 2):max(xs, xs + side * 2) + 2] = C['grey']
            xe = cx + side * 11 + (0 if side > 0 else -1)
            out[9:18, xe:xe + 2] = C['grey']
            out[5:9, xe:xe + 2] = C['skin']
            out[5:8, xe + (2 if side > 0 else -1)] = C['skin']
    elif pose in ("crack", "crack2"):   # fingers laced, pushed out in front of his chest
        for side in (-1, 1):
            for i in range(5):
                x = cx + side * (9 - i) + (0 if side > 0 else -1)
                out[15 - i // 2: 17 - i // 2, x] = C['grey']
        out[12:15, cx - 4:cx + 5] = C['skin']
        out[13, cx - 3:cx + 4:2] = C['skind']
        if pose == "crack2":
            for (dx, dy) in ((-7, -3), (7, -3), (-8, 0), (8, 0), (-6, -5), (6, -5)):
                out[13 + dy, cx + dx] = C['gold']
            out[9, cx - 9] = C['gold']; out[9, cx + 9] = C['gold']
    return out


# ----------------------------------------------------------------------------- sets: kitchen
def stove(frame=0):
    out = canvas(20, 30)
    out[12:29, 1:19] = C['white']
    out[11, 0:20] = C['black']
    out[15:25, 4:16] = C['dgrey']
    out[13, 4:7] = C['black']; out[13, 9:12] = C['black']; out[13, 14:17] = C['black']
    out[26, 3:17] = C['grey']
    out[29, 1:4] = C['black']; out[29, 16:19] = C['black']
    # pot
    out[6:11, 5:15] = C['red']
    out[5, 4:16] = C['dred']
    out[7, 3:5] = C['black']; out[7, 15:17] = C['black']
    out[8, 6:14] = C['gold']
    st = [[(8, 3), (9, 2), (8, 1), (11, 3), (12, 2), (11, 1)], [(9, 3), (8, 2), (9, 1), (12, 3), (11, 2), (12, 0)]][frame % 2]
    for x, y in st:
        out[y, x] = C['white']
    return out


def shelf():
    out = canvas(34, 16)
    out[10:12, 0:34] = C['brown']
    # jars
    for i, col in enumerate(['red', 'gold', 'green', 'white']):
        x = 2 + i * 6
        out[4:10, x:x + 4] = C[col]
        out[3, x:x + 4] = C['dgrey']
    # hanging peppers
    for i in range(4):
        x = 26 + i * 2
        out[12, x] = C['green']
        out[13:16, x] = C['red']
    return out


def kitchen_table(screen=True):
    """Table with the uncle's laptop on it, screen toward us. 38 x 22."""
    out = canvas(38, 22)
    out[10:12, 0:38] = C['lbrown']
    out[12:22, 2:4] = C['brown']; out[12:22, 34:36] = C['brown']
    # table runner
    out[10, 4:34] = C['red']
    # laptop, open toward us: screen + keyboard deck
    out[0:9, 10:28] = C['dgrey']
    out[1:8, 11:27] = C['cream']
    out[9, 8:30] = C['silver']
    out[10, 8:30] = C['grey']
    return out


# ----------------------------------------------------------------------------- sets: wedding
def wedding_table(w=96):
    out = canvas(w, 22)
    # cloth
    out[6:18, 0:w] = C['white']
    out[6, 0:w] = C['red']
    for x in range(0, w, 4):
        out[17, x:x + 2] = C['red']
        out[16, x + 1] = C['red']
    out[10:12, 0:w] = C['red']
    for x in range(1, w, 6):
        out[10:12, x:x + 2] = C['gold']
    out[18:22, 3:5] = C['brown']; out[18:22, w - 5:w - 3] = C['brown']
    # things on the table
    for x in range(6, w - 6, 15):
        # bottle
        out[0:6, x:x + 2] = C['green']; out[-0 + 0, x] = C['green']
        # glasses
        out[3:5, x + 5:x + 7] = C['sky']; out[5, x + 5:x + 7] = C['silver']
        # plate with food
        out[5, x + 9:x + 13] = C['silver']; out[4, x + 10:x + 12] = C['gold']
    return out


def bunting(w, phase=0):
    """String of small red and black pennants (not flags)."""
    out = canvas(w, 5)
    for x in range(w):
        out[int(round(1.2 * np.sin(x / w * np.pi))), x] = C['dgrey']
    for i, x in enumerate(range(2, w - 4, 6)):
        col = C['red'] if (i + phase) % 2 == 0 else C['gold']
        y = int(round(1.2 * np.sin((x + 1) / w * np.pi))) + 1
        out[y, x:x + 3] = col
        out[y + 1, x:x + 3] = col
        out[y + 2, x + 1] = col
    return out


def lantern(lit=1):
    out = A("""
        ..d..
        .YYY.
        YYYYY
        YYYYY
        .YYY.
        ..G..
    """)
    if not lit:
        out = recolor(out, {'yellow': 'gold'})
    return out


# musicians: built on the small man, hero-sized bodies would crowd the stage
def musician(kind, pose=0):
    """kind: clarinet, drum (lodra/tupan), accordion. 21 x 26."""
    out = canvas(23, 26)
    m = dancer('m', 0)
    paste(out, m, 4, 1 - (pose % 2))
    ox, oy = 4, 1 - (pose % 2)
    # clear the out-stretched arms
    out[oy + 8:oy + 12, ox + 0:ox + 4] = 0
    out[oy + 8:oy + 12, ox + 11:ox + 15] = 0
    out[oy + 8, ox + 3] = C['white']; out[oy + 8, ox + 11] = C['white']
    if kind == "clarinet":
        body = out[oy + 8:oy + 13, ox + 4:ox + 11]
        body[body == C['black']] = C['white']; body[body == C['gold']] = C['white']
        # clarinet: black, silver keys, flared bell, held out at an angle so it reads against the cloth
        # short and straight, pointing down from the mouth in front of the chest, bell at the belt
        for i in range(8):
            cx_ = ox + 7 + (i + 1) // 3
            out[oy + 7 + i, cx_:cx_ + 2] = C['black']
        out[oy + 15, ox + 9:ox + 12] = C['black']
        out[oy + 16, ox + 8:ox + 13] = C['black']
        for i in (2, 4, 6):
            out[oy + 7 + i, ox + 7 + (i + 1) // 3 + 1] = C['silver']
        # both hands on it: upper hand from the left sleeve, lower hand from the right sleeve
        out[oy + 9, ox + 3:ox + 5] = C['white']; out[oy + 10, ox + 4:ox + 7] = C['white']
        out[oy + 10, ox + 7] = C['skin']
        out[oy + 9, ox + 11:ox + 13] = C['white']; out[oy + 10, ox + 12:ox + 14] = C['white']
        out[oy + 11, ox + 12:ox + 14] = C['white']; out[oy + 12, ox + 11:ox + 13] = C['white']
        out[oy + 12, ox + 11] = C['skin']
        if pose % 2:
            nx = ox + 15
            out[oy + 1:oy + 4, nx] = C['black']; out[oy + 3, nx - 1] = C['black']; out[oy + 1, nx + 1] = C['black']
    elif kind == "drum":
        # lodra: big two-headed drum slung at the left hip, rope lacing, thick beater + thin switch
        dr = A("""
            ..lllll..
            .lWWWWWl.
            lWWWWWWWl
            lWWWWWWWl
            lWWWrWWWl
            lWWWWWWWl
            lWWWWWWWl
            .lWWWWWl.
            ..lllll..
        """)
        paste(out, dr, ox + 3, oy + 9)
        out[oy + 8, ox + 4:ox + 11] = C['dgrey']   # strap over the shoulder
        # arms: right hand (viewer's left) with the thick beater, left with the switch
        out[oy + 9, ox + 2] = C['white']; out[oy + 10, ox + 1] = C['white']
        out[oy + 9, ox + 12] = C['white']; out[oy + 10, ox + 13] = C['white']
        if pose % 2 == 0:
            out[oy + 11, ox + 1] = C['skin']; out[oy + 12, ox + 2] = C['brown']; out[oy + 13, ox + 2] = C['brown']
            out[oy + 11, ox + 13] = C['skin']; out[oy + 10, ox + 14] = C['brown']; out[oy + 9, ox + 15] = C['brown']
        else:
            out[oy + 11, ox + 1] = C['skin']; out[oy + 10, ox + 0] = C['brown']; out[oy + 9, ox + 0] = C['brown']
            out[oy + 11, ox + 13] = C['skin']; out[oy + 12, ox + 12] = C['brown']
    elif kind == "accordion":
        w = 9 if pose % 2 == 0 else 11
        x0 = ox + 7 - w // 2
        out[oy + 9:oy + 16, x0:x0 + w] = C['white']
        for x in range(x0 + 2, x0 + w - 2, 2):
            out[oy + 9:oy + 16, x] = C['dred']
        out[oy + 9:oy + 16, x0:x0 + 2] = C['red']
        out[oy + 9:oy + 16, x0 + w - 2:x0 + w] = C['red']
        out[oy + 10:oy + 15:2, x0 + w - 1] = C['white']       # keys on the player's right... viewer's right side
        out[oy + 10:oy + 15:2, x0] = C['black']                # bass buttons
        out[oy + 9, ox + 2:x0] = C['white']; out[oy + 9, x0 + w:ox + 13] = C['white']
        out[oy + 11, x0 - 1] = C['skin']; out[oy + 11, x0 + w] = C['skin']
    return out


def glass_raised(kind, pose=0):
    """Small dancer raising a glass with the viewer's-right hand."""
    d = dancer(kind, 0)
    out = canvas(17, 28)
    paste(out, d, 0, 3)
    out[3 + 8:3 + 12, 11:15] = 0
    out[3 + 8, 11] = C['white']
    dy = -(pose % 2)
    paste(out, A("""
        .b..b.
        .bRRb.
        ..bb..
        ..V...
        ..S...
        .W....
        W.....
    """), 11, 3 + 2 + dy)
    return out


# ----------------------------------------------------------------------------- mama's four instructions
def icon_bus():
    return A("""
        .RRRRRRRRRRRRRRRRR.
        RRRRRRRRRRRRRRRRRRR
        RbbRbbRbbRbbRbbRbbR
        RbbRbbRbbRbbRbbRbbR
        RRRRRRRRRRRRRRRRRRR
        RWRRRRRRRRRRRRRRRYR
        RRRKKKRRRRRRRKKKRRR
        ..KKyKK.....KKyKK..
        ...KKK.......KKK...
    """)


def icon_clock():
    return A("""
        ...KKKKK...
        .KKWWKWWKK.
        .KWWWKWWWK.
        KWWKWKWWWWK
        KWWWKKWWWWK
        KKWWWRWWWKK
        KWWWWWWWWWK
        KWWWWWWWWWK
        .KWWWWWWWK.
        .KKWWKWWKK.
        ...KKKKK...
    """)


def icon_jacket():
    return A("""
        ....NN.NN....
        ..NNNNGNNNN..
        .NNNNNGNNNNN.
        NNNNNNGNNNNNN
        NNN.NNGNN.NNN
        NNN.NNGNN.NNN
        NNN.NNGNN.NNN
        NNN.NNGNN.NNN
        .SS.NNGNN.SS.
        ....NNNNN....
    """)


def icon_phone():
    return A("""
        .KKKKKKK.
        .KbbbbbK.
        .KbgggbK.
        .KbgWgbK.
        .KbgggbK.
        .KbbbbbK.
        .KbbbbbK.
        .KKKyKKK.
        .KKKKKKK.
    """)


def kid():
    """Him as a boy, school bag on. 11 x 20."""
    return A("""
        ...KKKKK...
        ..KKKKKKK..
        ..KSSSSSK..
        ..SeSSSeS..
        ..SSSSSSS..
        ...SSRSS...
        ....SSS....
        .BNNNNNNNB.
        BBNNNGNNNBB
        BBNNNGNNNBB
        NN.NNGNN.NN
        NN.NNGNN.NN
        SS.NNNNN.SS
        ...ddddd...
        ...dd.dd...
        ...dd.dd...
        ...dd.dd...
        ...dd.dd...
        ..KKK.KKK..
    """)


def bottle_glass():
    return A("""
        .g....
        .g....
        ggg...
        ggg.bb
        ggg.bb
        ggg.V.
    """)


def nightstand(ring=0):
    """Small bedside table with a round alarm clock; ring 1/2 = the bells shaking."""
    out = canvas(15, 22)
    out[11:13, 2:13] = C['brown']
    out[13:22, 3:5] = C['brown']; out[13:22, 10:12] = C['brown']
    out[15:17, 5:10] = C['lbrown']
    ck = A("""
        .K...K.
        KKRRRKK
        .RWWWR.
        .RWKWR.
        .RWWWR.
        ..RRR..
        .K...K.
    """)
    paste(out, ck, 4 + (1 if ring == 1 else (-1 if ring == 2 else 0)), 4)
    if ring:
        for (x, y) in ((1, 3), (0, 6), (13, 3), (14, 6), (7, 1)):
            out[y, x] = C['gold']
    return out


def fridge():
    out = canvas(18, 40)
    out[0:39, 1:17] = C['white']
    out[0, 1] = 0; out[0, 16] = 0
    out[13, 1:17] = C['grey']
    out[4:10, 14] = C['dgrey']; out[17:27, 14] = C['dgrey']
    out[39, 2:5] = C['black']; out[39, 13:16] = C['black']
    # magnets and a note
    out[4:6, 4:6] = C['red']; out[8:10, 8:10] = C['gold']
    out[18:25, 4:10] = C['cream']
    out[20, 5:9] = C['grey']; out[22, 5:8] = C['grey']
    out[17, 6:8] = C['red']
    return out


def GLASS_ARM(sleeve="R"):
    """A raised arm holding a wine glass by the stem (bowl, wine, stem, the hand on the stem, the sleeve). 6 x 9."""
    return A("""
        V....V
        VbbbbV
        VRRRRV
        .VRRV.
        ...V..
        ...S..
        ..#S..
        .###..
        ###...
    """.replace("#", sleeve))
