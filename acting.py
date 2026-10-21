"""Acting layer for Tiny Japanese Story.

Stage directions in the [story] section (lines starting with '>' or '&') become keyframes
(walking, entering, expressions, waving...) and every frame asks Stage.state() where each
character is and what they are doing. Characters are drawn by rig() - the same Mika & Alex art as
lesson.py, but parameterised (walk cycle, raised arm, expressions).
"""
import functools, math, re
from PIL import Image, ImageDraw, ImageOps

L = None            # the lesson module, set by bind()
SPEED = 380.0       # px / second when walking
EXPRS = {"neutral": "neutral", "confused": "confused", "puzzled": "confused", "nervous": "confused",
         "lost": "confused", "surprised": "surprised", "shocked": "surprised", "amazed": "surprised",
         "happy": "happy", "excited": "happy", "smiling": "happy", "glad": "happy", "laughing": "happy",
         "sad": "sad", "worried": "sad", "disappointed": "sad", "shy": "shy", "embarrassed": "shy"}


def bind(mod):
    global L
    L = mod


# ------------------------------------------------------------------ directive parsing
def _names():
    return {k.lower(): k for k in L.CHARS}


def parse_dir(text):
    """'Mika enters left' -> (['Mika'], 'enter', 'left').  Raises ValueError with a friendly message."""
    t = text.strip().rstrip(".")
    m = re.match(r"^(wait|pause)\s*([\d.]*)\s*s?$", t, re.I)
    if m:
        return [], "wait", m[2] or "1"
    names = _names()
    m = re.match(r"^(%s|both|everyone|they)\s+([A-Za-z]+)\s*(.*)$" % "|".join(names), t, re.I)
    if not m:
        raise ValueError(f"can't read the stage direction '{text}'. Use e.g. 'Mika enters left', 'Alex walks to center', "
                         f"'Mika looks confused', 'both exit right', 'wait 1'")
    who = m[1].lower()
    whos = list(L.CHARS) if who in ("both", "everyone", "they") else [names[who]]
    verb, arg = m[2].lower(), m[3].strip()
    aliases = {"enters": "enter", "enter": "enter", "walks": "walk", "walk": "walk", "goes": "walk", "runs": "walk",
               "moves": "walk", "steps": "walk", "exits": "exit", "exit": "exit", "leaves": "exit", "leave": "exit",
               "looks": "look", "look": "look", "feels": "look", "seems": "look", "is": "look", "gets": "look",
               "faces": "face", "face": "face", "turns": "face", "turn": "face", "waves": "wave", "wave": "wave",
               "jumps": "hop", "jump": "hop", "hops": "hop", "hop": "hop"}
    if verb not in aliases:
        raise ValueError(f"unknown action '{verb}' in '{text}'. Actions: enters, walks to, exits, looks <feeling>, faces, waves, jumps, wait")
    verb = aliases[verb]
    if verb == "look":
        a = re.sub(r"^(at\s+)", "", arg, flags=re.I).strip()
        if arg.lower().startswith("at "):
            verb, arg = "face", a
        else:
            if a.lower() not in EXPRS:
                raise ValueError(f"unknown feeling '{arg}' in '{text}'. Feelings: {', '.join(sorted(set(EXPRS)))}")
            arg = a.lower()
    return whos, verb, arg


def check_dir(text):
    parse_dir(text)


# ------------------------------------------------------------------ the stage
def _smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


class Stage:
    def __init__(self):
        W = L.W
        self.W = W
        self.home = {nm: c["x"] + L.SPRITE_W // 2 for nm, c in L.CHARS.items()}
        self.dflt_face = {nm: (1 if self.home[nm] < W / 2 else -1) for nm in L.CHARS}
        self.moves = {nm: [] for nm in L.CHARS}      # (t0, t1, x0, x1)
        self.vis = {nm: [] for nm in L.CHARS}        # (t, bool)
        self.expr = {nm: [] for nm in L.CHARS}       # (t, name)
        self.face = {nm: [] for nm in L.CHARS}       # (t, +1/-1)
        self.wave = {nm: [] for nm in L.CHARS}       # (t0, t1)
        self.hop = {nm: [] for nm in L.CHARS}
        self.pops = []                               # (t0, t1, name, text)
        self.start_vis = {nm: True for nm in L.CHARS}
        self.start_x = dict(self.home)

    # -- setup
    def prescan(self, lines):
        seen = set()
        for ln in lines:
            for item in (ln.get("dirs") or []) + (ln.get("after") or []):
                if item[0] != "dir":
                    continue
                whos, verb, _ = parse_dir(item[1])
                for nm in whos:
                    if nm not in seen:
                        seen.add(nm)
                        if verb == "enter":
                            self.start_vis[nm] = False
                            self.start_x[nm] = self._off(nm, "left" if self.home[nm] < self.W / 2 else "right")

    def _off(self, nm, side):
        return -L.SPRITE_W if side == "left" else self.W + L.SPRITE_W

    # -- queries
    def x_at(self, nm, t):
        x = self.start_x[nm]
        for t0, t1, x0, x1 in self.moves[nm]:
            if t < t0:
                break
            x = x1 if t >= t1 else x0 + (x1 - x0) * _smooth((t - t0) / max(1e-6, t1 - t0))
        return x

    def vis_at(self, nm, t):
        v = self.start_vis[nm]
        for tt, b in self.vis[nm]:
            if tt <= t:
                v = b
        return v

    def _last(self, lst, t, default):
        v = default
        for item in lst:
            if item[0] <= t:
                v = item[1]
        return v

    def state(self, nm, t):
        walking = any(t0 <= t < t1 and abs(x1 - x0) > 1 for t0, t1, x0, x1 in self.moves[nm])
        wave = any(a <= t < b for a, b in self.wave[nm])
        hop = next(((t - a) / (b - a) for a, b in self.hop[nm] if a <= t < b), None)
        pop = next((txt for a, b, n, txt in self.pops if n == nm and a <= t < b), None)
        face = self._last(self.face[nm], t, self.dflt_face[nm])
        return dict(vis=self.vis_at(nm, t), x=self.x_at(nm, t), walking=walking, wave=wave, hop=hop, pop=pop,
                    expr=self._last(self.expr[nm], t, "neutral"), face=face, mirror=(face != self.dflt_face[nm]))

    # -- compile directives into keyframes
    def _target(self, nm, arg, t):
        a = re.sub(r"^(to\s+)?(the\s+)?", "", arg.strip().lower()).strip()
        W = self.W
        names = _names()
        m = re.match(r"^(next to|beside|near)\s+(\w+)$", a)
        if m and m[2] in names:
            ox = self.x_at(names[m[2]], t)
            cur = self.x_at(nm, t)
            return ox + (-380 if cur < ox else 380)
        if a in names:
            return self.x_at(names[a], t) + (-380 if self.x_at(nm, t) < self.x_at(names[a], t) else 380)
        table = {"left": 0.2, "center": 0.5, "centre": 0.5, "middle": 0.5, "right": 0.8, "front": 0.5,
                 "far left": 0.1, "far right": 0.9, "desk": 0.35, "door": 0.12}
        if a in table:
            return table[a] * W
        if a in ("home", "", "seat", "spot"):
            return self.home[nm]
        m = re.match(r"^(\d+)\s*%?$", a)
        if m:
            return int(m[1]) / 100 * W
        raise ValueError(f"don't know the place '{arg}'. Use left, center, right, home, 'next to Alex' or a percent like 40")

    def _move(self, nm, t, x1, dur=None):
        x0 = self.x_at(nm, t)
        d = abs(x1 - x0)
        dur = dur or max(0.6, d / SPEED)
        self.moves[nm].append((t, t + dur, x0, x1))
        if d > 1:
            self.face[nm].append((t, 1 if x1 > x0 else -1))
        return dur

    def _one(self, text, t):
        whos, verb, arg = parse_dir(text)
        if verb == "wait":
            return float(arg)
        dur = 0.0
        for nm in whos:
            if verb == "enter":
                a = arg.lower()
                side = "left" if re.search(r"\bleft\b", a) else "right" if re.search(r"\bright\b", a) else \
                    ("left" if self.home[nm] < self.W / 2 else "right")
                m = re.search(r"\bto\s+(.+)$", a)
                dest = self._target(nm, m[1], t) if m else self.home[nm]
                x_now = self.x_at(nm, t)
                if (not self.vis_at(nm, t)) or x_now < -L.SPRITE_W * 0.5 or x_now > self.W + L.SPRITE_W * 0.5:
                    self.moves[nm].append((t, t, x_now, self._off(nm, side)))   # start from off-screen
                    self.vis[nm].append((t, True))
                d = self._move(nm, t, dest)
                end = t + d
                dur = max(dur, d)
                for other in L.CHARS:
                    if other != nm and self.vis_at(other, end) and abs(self.x_at(other, end) - dest) > 5:
                        self.face[nm].append((end, 1 if self.x_at(other, end) > dest else -1))
                        self.face[other].append((end, 1 if dest > self.x_at(other, end) else -1))
                        self.pops.append((end, end + 1.0, other, "!"))
            elif verb == "walk":
                d = self._move(nm, t, self._target(nm, arg, t)); dur = max(dur, d)
            elif verb == "exit":
                a = arg.lower()
                side = "left" if "left" in a else "right" if "right" in a else \
                    ("left" if self.x_at(nm, t) < self.W / 2 else "right")
                d = self._move(nm, t, self._off(nm, side))
                self.vis[nm].append((t + d, False)); self.expr[nm].append((t + d, "neutral")); dur = max(dur, d)
            elif verb == "look":
                self.expr[nm].append((t, EXPRS[arg])); dur = max(dur, 1.3)
            elif verb == "face":
                a = arg.lower().strip()
                names = _names()
                if a in names:
                    f = 1 if self.x_at(names[a], t) > self.x_at(nm, t) else -1
                elif a in ("left", "right"):
                    f = -1 if a == "left" else 1
                else:
                    raise ValueError(f"'{text}': face left, right or a name")
                self.face[nm].append((t, f)); dur = max(dur, 0.4)
            elif verb == "wave":
                self.wave[nm].append((t, t + 1.6)); dur = max(dur, 1.6)
            elif verb == "hop":
                self.hop[nm].append((t, t + 0.9)); dur = max(dur, 0.9)
        return dur

    def direct(self, items, t0):
        """items: [(text, parallel)] -> end time."""
        end, last = t0, t0
        for text, par in items:
            start = last if par else end
            d = self._one(text, start)
            last = start
            end = max(end, start + d)
        return end

    def line(self, speaker, a, b):
        """The speaker turns to the other visible character (and vice versa) when a line starts."""
        for other in L.CHARS:
            if other != speaker and self.vis_at(other, a) and self.vis_at(speaker, a):
                xs, xo = self.x_at(speaker, a), self.x_at(other, a)
                if abs(xs - xo) > 5:
                    self.face[speaker].append((a, 1 if xo > xs else -1))
                    self.face[other].append((a, 1 if xs > xo else -1))


def story_line(tr, stage, mark, ln, prev):
    """Directions (as animated 'act' segments), then the spoken line. Returns the current scene."""
    def run(items, cur):
        group = []
        def flush(cur_scene):
            nonlocal group
            if group:
                t0 = tr.t
                t1 = stage.direct(group, t0)
                mark("act", t0, scene=cur_scene, prev_scene=prev_box[0])
                prev_box[0] = cur_scene
                tr.gap(max(0.05, t1 - t0))
                group = []
        for it in items:
            if it[0] == "scene":
                flush(cur)
                cur = it[1]
                if not group:   # a pure scene change with no acting of its own is applied by the next segment
                    pass
                group = []
                pending_scene[0] = cur
            else:
                group.append((it[1], it[2]))
        flush(cur)
        return cur
    prev_box, pending_scene = [prev], [None]
    cur = prev
    dirs = ln.get("dirs") or []
    if dirs:
        cur = run(dirs, prev)
    a, b = tr.say(ln["jp"], ln["speaker"])
    ln.update(start=a, end=b)
    stage.line(ln["speaker"], a, b)
    mark("story", a - 0.02, line=ln, scene=ln["scene"], prev_scene=prev_box[0])
    cur = ln["scene"]
    tr.gap(0.6)
    after = ln.get("after") or []
    if after:
        prev_box[0] = cur
        cur = run(after, cur)
    return cur


# ------------------------------------------------------------------ drawing
@functools.lru_cache(None)
def rig(name, mouth, blink, expr, walk, arm, out):
    """Full-body Mika / Alex with a walk phase (0-3), a waving arm (0-2) and an expression."""
    from PIL import ImageFont  # noqa
    c, S = L.CHARS[name], 2 * L.CHAR_SCALE
    w, h = int(560 * S), int(960 * S)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    P = lambda *v: [int(x * S) for x in v]
    ell = lambda box, fill: d.ellipse(P(*box), fill=fill)
    ink, hair, skin, top, acc = (70, 45, 48), c["hair"], c["skin"], c["top"], c["accent"]
    brow_c, mouth_c = (86, 56, 52), (120, 40, 52)
    ll, rl = (28 if walk == 1 else 0), (28 if walk == 3 else 0)
    swing = {0: 0, 1: 8, 2: 0, 3: -8}[walk]
    if c["long_hair"]:
        d.rounded_rectangle(P(110, 170, 450, 590), radius=int(110 * S), fill=hair)
    shoe = (96, 66, 60)
    if c["long_hair"]:
        for x0, lf in ((214, ll), (306, rl)):
            d.rounded_rectangle(P(x0, 780 - lf, x0 + 42, 905 - lf), radius=int(16 * S), fill=skin)
            d.rounded_rectangle(P(x0 - 2, 862 - lf, x0 + 44, 912 - lf), radius=int(14 * S), fill=(250, 248, 246))
            ell((x0 - 14, 896 - lf, x0 + 62, 940 - lf), shoe)
        d.polygon(P(178, 640, 382, 640, 414, 805, 146, 805), fill=(122, 132, 196))
        for x in range(170, 400, 46):
            d.line(P(x, 700, x - (280 - x) * 0.08, 800), fill=(104, 114, 178), width=int(5 * S))
    else:
        for x0, lf in ((198, ll), (292, rl)):
            d.rounded_rectangle(P(x0, 640, x0 + 72, 890 - lf), radius=int(26 * S), fill=(96, 112, 150))
            ell((x0 - 10, 876 - lf, x0 + 84, 926 - lf), shoe)
        d.rounded_rectangle(P(190, 628, 370, 700), radius=int(26 * S), fill=(96, 112, 150))
    d.rounded_rectangle(P(185, 450, 375, 690), radius=int(60 * S), fill=top)
    d.polygon(P(245, 452, 280, 505, 315, 452), fill=skin)
    ell((140 + swing, 500, 210 + swing, 650), top)
    ell((148 + swing, 625, 205 + swing, 675), skin)
    if not arm:
        ell((350 - swing, 500, 420 - swing, 650), top)
        ell((355 - swing, 625, 412 - swing, 675), skin)
    ell((125, 145, 435, 455), skin)
    d.pieslice(P(118, 136, 442, 460), 180, 360, fill=hair)
    if c["long_hair"]:
        for x in range(150, 420, 48):
            ell((x - 34, 225, x + 34, 300 + (12 if (x // 48) % 2 else 0)), hair)
        ell((112, 280, 168, 520), hair); ell((392, 280, 448, 520), hair)
        ell((340, 165, 392, 215), acc); ell((355, 180, 377, 200), (255, 240, 200))
    else:
        for x in range(135, 420, 58):
            d.polygon(P(x, 225, x + 58, 225, x + 29, 305), fill=hair)
        d.polygon(P(262, 120, 300, 120, 282, 165), fill=hair)
    # eyes
    for ex in (222, 338):
        if blink or expr == "happy":
            d.arc(P(ex - 26, 332, ex + 26, 376), 200, 340, fill=ink, width=int(6 * S))
        elif expr == "surprised":
            ell((ex - 30, 308, ex + 30, 392), (55, 35, 42))
            ell((ex - 18, 322, ex + 4, 346), (255, 255, 255)); ell((ex + 8, 362, ex + 20, 374), (255, 255, 255))
        else:
            ell((ex - 24, 318, ex + 24, 382), (55, 35, 42))
            sh = 8 if expr == "confused" else 0
            ell((ex - 15 + sh, 330, ex + 3 + sh, 350), (255, 255, 255)); ell((ex + 6 + sh, 358, ex + 16 + sh, 368), (255, 255, 255))
    # brows
    bw = int(7 * S)
    if expr == "confused":
        d.line(P(192, 300, 252, 294), fill=brow_c, width=bw); d.line(P(312, 270, 368, 282), fill=brow_c, width=bw)
    elif expr == "surprised":
        d.arc(P(190, 270, 254, 300), 200, 340, fill=brow_c, width=bw); d.arc(P(306, 270, 370, 300), 200, 340, fill=brow_c, width=bw)
    elif expr == "sad":
        d.line(P(192, 302, 252, 284), fill=brow_c, width=bw); d.line(P(308, 284, 368, 302), fill=brow_c, width=bw)
    # cheeks
    chk = (246, 140, 140) if expr == "shy" else (250, 172, 170)
    k = 8 if expr == "shy" else 0
    ell((168 - k, 388 - k, 215 + k, 412 + k), chk); ell((345 - k, 388 - k, 392 + k, 412 + k), chk)
    # mouth
    if mouth == 1:
        ell((268, 408, 292, 430), mouth_c)
    elif mouth >= 2:
        ell((258, 405, 302, 442), mouth_c); ell((266, 424, 294, 440), (236, 120, 132))
    elif expr == "happy":
        d.arc(P(248, 394, 312, 440), 20, 160, fill=ink, width=int(6 * S))
    elif expr == "surprised":
        ell((270, 410, 290, 436), mouth_c)
    elif expr == "confused":
        d.line(P(264, 424, 276, 416, 288, 426, 300, 416), fill=ink, width=int(5 * S))
    elif expr == "sad":
        d.arc(P(262, 418, 298, 446), 200, 340, fill=ink, width=int(5 * S))
    elif expr == "shy":
        d.arc(P(270, 404, 292, 424), 20, 160, fill=ink, width=int(4 * S))
    else:
        d.arc(P(262, 400, 298, 430), 20, 160, fill=ink, width=int(5 * S))
    if expr == "confused":     # sweat drop
        d.polygon(P(430, 165, 416, 205, 444, 205), fill=(176, 216, 240)); ell((414, 192, 446, 226), (176, 216, 240))
    if arm:                    # raised, waving arm (drawn over the head edge)
        hx = 448 + (16 if arm == 1 else -6)
        d.line(P(385, 545, hx, 440), fill=top, width=int(66 * S))
        ell((352, 505, 420, 585), top)
        ell((hx - 32, 380, hx + 32, 452), skin)
    return im.resize((int(L.SPRITE_W * out), int(L.SPRITE_H * out * 960 / 760)), Image.LANCZOS)


def draw_characters(R, fr, seg, i, tt, who, mouth):
    """Draw both characters for frame i using the stage timeline."""
    B, stage = R.B, R.B["stage"]
    d = ImageDraw.Draw(fr)
    order = sorted(L.CHARS, key=lambda n: 1 if who == n else 0)
    for nm in order:
        st = stage.state(nm, tt)
        if seg["kind"] == "outro":
            st = dict(vis=True, x=stage.home[nm], walking=False, wave=False, hop=None, pop=None, expr="happy",
                      face=stage.dflt_face[nm], mirror=False)
        if not st["vis"] or st["x"] < -L.SPRITE_W * 1.2 or st["x"] > L.W + L.SPRITE_W * 1.2:
            continue
        speaking = who == nm
        blink = ((i + (0 if nm == "Mika" else 41)) % 72) < 3
        walk = (0, 1, 0, 3)[int(tt * 7) % 4] if st["walking"] else 0
        arm = (1 + int(tt * 5) % 2) if st["wave"] else 0
        s = rig(nm, int(mouth) if speaking else 0, blink, st["expr"], walk, arm, L.STAGE_OUT)
        if st["mirror"]:
            s = ImageOps.mirror(s)
        bob = 0.0
        if st["walking"]:
            bob = 12 * abs(math.sin(tt * 7 * math.pi / 2 * 2 / 2))
        elif speaking and mouth:
            bob = 6 * abs(math.sin(tt * 7))
        else:
            bob = 2 * math.sin(tt * 2 + (0 if nm == "Mika" else 1.7))
        if st["hop"] is not None:
            bob += 150 * math.sin(math.pi * st["hop"])
        x = int(st["x"] - s.width // 2)
        y = int(L.FLOOR_Y - 50 - s.height - bob)
        fr.paste(s, (x, y), s)
        p = R.pills[(nm, int(speaking))]
        fr.paste(p, (int(st["x"]) - p.width // 2, int(L.FLOOR_Y - 50 - s.height + 36)), p)
        mark = st["pop"] or {"confused": "?", "surprised": "!"}.get(st["expr"])
        if mark:
            wob = 6 * math.sin(tt * 9)
            d.text((int(st["x"] + s.width * (0.26 if not st["mirror"] else -0.26)), int(y - 20 + wob)), mark,
                   font=L.font(110), fill=L.CHARS[nm]["accent"], stroke_width=10, stroke_fill=(255, 255, 255), anchor="mm")
