"""The thread: who posts what, when, and what gives each commenter away. Lyric lines are replies from @aditazzz
(typed word by word on their sung times); the crowd and the system cards are written here by hand."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
LN = json.load(open(os.path.join(HERE, "build", "timed.json")))
def wt(i, j): return LN[i]["wt"][j]
def ls(i): return LN[i]["s"]

class E:
    __slots__ = ("id", "t", "kind", "user", "text", "av", "reply", "likes", "badges", "top_t", "edited_t", "chips",
                 "chip_sel_t", "deleted_t", "stamp_t", "line", "sys", "train", "point_t", "underline_t", "flip")
    def __init__(s, t, kind, user="", text="", av="crowd:0", reply=False, likes=None, badges=(), top_t=None,
                 edited_t=None, chips=(), chip_sel_t=None, deleted_t=None, stamp_t=None, line=None, sys=None,
                 point_t=None, underline_t=None, flip=True):
        s.id = 0; s.t = t; s.kind = kind; s.user = user; s.text = text; s.av = av; s.reply = reply
        s.likes = likes or [(t, 0)]; s.badges = list(badges); s.top_t = top_t; s.edited_t = edited_t; s.chips = chips
        s.chip_sel_t = chip_sel_t; s.deleted_t = deleted_t; s.stamp_t = stamp_t; s.line = line; s.sys = sys
        s.train = None; s.point_t = point_t; s.underline_t = underline_t; s.flip = flip

ENT = []
def C(t, user, text, av, **kw):
    e = E(t, "crowd", user, text, av, **kw); ENT.append(e); return e
def S(t, kind_sys, **kw):
    e = E(t, "system", sys=kind_sys, flip=False, **kw); ENT.append(e); return e

# lyric replies (INTRO is the post's caption, the BRIDGE is typed into the composer and never posted, TAG is the last post)
LYRIC_SKIP = {"INTRO", "BRIDGE", "TAG"}
for i, L in enumerate(LN):
    if L["sec"] in LYRIC_SKIP: continue
    n = 1
    lk = [(L["s"], 0), (L["s"] + 6, 40 + (i * 37) % 300), (L["s"] + 30, 400 + (i * 113) % 900)]
    ENT.append(E(L["s"] - 0.32, "lyric", "aditazzz", L["text"], "artist", reply=True, likes=lk, line=i, flip=False))

# ---------------------------------------------------------------- INTRO: the first comments
C(8.6, "realart_only", "is this AI??", "crowd:0", likes=[(8.6, 0), (10, 3), (12, 14)])
C(9.5, "user8392017", "first", "bot:1", likes=[(9.5, 0), (11, 2)])
C(10.3, "lurker_9000", "wait it's actually good", "crowd:1", likes=[(10.3, 0), (12, 6)])
C(11.2, "analog.heart", "unfollowing.", "crowd:2", likes=[(11.2, 0), (12.2, 9)])

# ---------------------------------------------------------------- V1: the receipts
TOP = C(12.55, "realart_only", "the death of art", "crowd:0",
        likes=[(12.55, 0), (16.35, 12), (17.55, 200), (60, 200)],
        chips=("the death of art", "art is dead", "so sad"), chip_sel_t=wt(3, 4),
        badges=[(wt(4, 3), "Recommended for you")])
NINA = C(24.9, "nofilter.nina", "no makeup, no filter, ever", "crowd:3", likes=[(24.9, 0), (25.9, 240), (32, 2900)],
         badges=[(ls(5), "Glow filter")])
# the top comment is pinned under the header while the verse picks it apart; on "Filtered" Nina takes the top spot
PINS = [(TOP, ls(1), ls(5)), (NINA, ls(5), 37.95)]
C(34.62, "mid_but_honest", "so true", "crowd:4", likes=[(34.62, 0), (36, 88)])
C(34.80, "truartist", "art is dead", "crowd:5", likes=[(34.80, 0), (36, 120)])
C(34.98, "handmade_only", "real art only", "crowd:6", likes=[(34.98, 0), (37, 230)])
AI_BADGE_T = wt(8, 6)          # "do": every crowd comment so far turns out to be AI-assisted

# ---------------------------------------------------------------- PRE1: the flood
FLOOD = [("boycott.slop", "fake"), ("user1192834", "cheap"), ("pure.ink", "AI slop"), ("hand.drawn.only", "fake"),
         ("canvas.kid", "soulless"), ("user5520113", "cheap trick"), ("oilpaint.olga", "fake"), ("no.ai.ever", "slop"),
         ("film.is.alive", "lazy"), ("user7718202", "fake!!"), ("real.strings", "real artists exist"), ("grain.lover", "fake")]
for k, (u, tx) in enumerate(FLOOD):
    av = f"bot:{k + 4}" if u.startswith("user") else f"crowd:{(k * 5 + 7) % 24}"
    C(37.95 + k * 0.145, u, tx, av, likes=[(37.95 + k * 0.145, 0), (44, 20 + k * 31)])
S(39.55, "guidelines")                      # checks tick on "Look at all the rules we keep"
GUIDE_CHECKS = [wt(10, 1), wt(10, 3), wt(10, 4), wt(10, 6)]

# ---------------------------------------------------------------- CH1
CH1_EDIT_T = wt(15, 3)                      # "Every little lie": every crowd comment gets "edited"
S(ls(18) - 0.2, "report")                   # "We drew the lines, we set the taste"
REPORT_CHECKS = [wt(18, 1), wt(18, 3), wt(18, 5)]
POINT1 = [("this.is.why", "THIS. look at it"), ("art.police", "zoom in on the eyes"), ("user3301877", "fake"),
          ("frame.by.frame", "you can tell")]
for k, (u, tx) in enumerate(POINT1):
    C(wt(19, 0) + 0.1 + k * 0.62, u, tx, f"crowd:{(k * 7 + 3) % 24}" if not u.startswith("user") else "bot:9",
      likes=[(wt(19, 0) + k * 0.62, 0), (70, 300 + k * 90)], point_t=wt(19, 0) + 0.25 + k * 0.62)

# ---------------------------------------------------------------- V2: more receipts
C(82.75, "pure.vinyl.girl", "real singers don't need autotune", "crowd:7",
  likes=[(82.75, 0), (86, 1400)], badges=[(wt(23, 2), "Pitch-corrected 100%")])
C(87.8, "songwriter.sam", "write your own songs", "crowd:8", likes=[(87.8, 0), (90, 900)],
  badges=[(wt(24, 2), "Written by 7 people")])
C(90.6, "wellness.jen", "authenticity is everything", "crowd:9", likes=[(90.6, 0), (93, 5200)],
  badges=[(wt(25, 5), "Paid partnership")])
LAUGH = C(93.9, "laughtrack", "HAHAHAHAHA", "bot:12", likes=[(93.9, 0)])
SUGGEST_T = (wt(27, 3), wt(27, 7))          # the comment box fills itself, then posts it
C(wt(27, 7) + 0.25, "you", "this is soulless", "face:5", likes=[(wt(27, 7) + 0.25, 0), (102, 61)],
  badges=[(wt(27, 7) + 0.25, "Suggested reply")])
C(100.15, "road.trip.ray", "typing this while driving lol", "crowd:10", likes=[(100.15, 0), (103, 77)],
  badges=[(wt(28, 3), "Autopilot on")])
SORT_T = wt(29, 4)                          # "machine": Sort by Top -> Recommended
NOAI = C(106.25, "no.ai.ever", "AI can do anything except ART", "crowd:11", likes=[(106.25, 0), (109, 2400)],
         underline_t=wt(30, 2))

# ---------------------------------------------------------------- PRE2
S(ls(31) - 0.15, "guidelines2")
MIRROR_PRE2 = (wt(33, 4), ls(34) + 0.2)     # "It held a mirror to our face"
SEARCH = (ls(34) - 0.1, 117.6)              # "Now we're searching for someone to blame"

# ---------------------------------------------------------------- CH2
S(ls(40) - 0.2, "report")
POINT2 = [("art.police", "look at the hands"), ("user6620019", "fake"), ("taste.maker", "my kid could do this"),
          ("frame.by.frame", "uncanny")]
for k, (u, tx) in enumerate(POINT2):
    C(wt(41, 0) + 0.1 + k * 0.62, u, tx, f"crowd:{(k * 5 + 11) % 24}" if not u.startswith("user") else "bot:14",
      likes=[(wt(41, 0) + k * 0.62, 0), (142, 500 + k * 70)], point_t=wt(41, 0) + 0.25 + k * 0.62)

# ---------------------------------------------------------------- BREAK: fake, fake, fake
FAKE = [(wt(45, 0), "lawn.goals", "my lawn is 100% real", "crowd:12"),
        (wt(45, 2), "lash.queen", "100% natural lashes", "crowd:13"),
        (wt(46, 0), "bestie.4ever", "so happy for you!!", "crowd:14"),
        (wt(47, 0), "smile.daily", "woke up like this :)", "crowd:15"),
        (wt(47, 2), "growth.guru", "1.2M real followers", "bot:16"),
        (wt(48, 0), "fan.account.7", "I love what you do!", "crowd:16")]
for (tf, u, tx, av) in FAKE:
    C(tf - 0.55, u, tx, av, likes=[(tf - 0.55, 0), (tf + 1, 1200)], stamp_t=tf)
C(ls(49) - 0.1, "sad.but.aesthetic", "it's been a hard year", "crowd:17", likes=[(ls(49), 0), (172, 15000)],
  badges=[(wt(49, 2), "Sponsored")])
S(ls(50) - 0.2, "insights")
AI_LABEL_T = wt(51, 3)                      # the post gets labeled "AI-generated?"
COUNTERFEIT_T = wt(52, 3)

# ---------------------------------------------------------------- BUILD: training, the crack
TRAIN = (wt(63, 0) + 0.2, wt(63, 8) + 0.4)  # every comment so far flies into the mirror
CRACK_T = wt(64, 2)                         # "mad"

# ---------------------------------------------------------------- FINAL
S(ls(70) - 0.2, "report")
POINT3 = [("art.police", "it even has the crack"), ("user9910021", "fake"), ("taste.maker", "who made this??"),
          ("frame.by.frame", "it looks like us")]
for k, (u, tx) in enumerate(POINT3):
    C(wt(71, 0) + 0.1 + k * 0.62, u, tx, f"crowd:{(k * 3 + 17) % 24}" if not u.startswith("user") else "bot:18",
      likes=[(wt(71, 0) + k * 0.62, 0), (234, 900 + k * 70)], point_t=wt(71, 0) + 0.25 + k * 0.62)

# ---------------------------------------------------------------- OUTRO: deleted, one by one
DELETE = (247.3, 255.6)
TAG_POST_T = 260.62

ENT.sort(key=lambda e: e.t)
for i, e in enumerate(ENT): e.id = i
