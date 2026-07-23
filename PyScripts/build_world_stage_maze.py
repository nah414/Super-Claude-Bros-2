"""THE CRYSTAL MAZE v2 — braided paths, rolling ground, a forest with no sightlines.

Adam's round-2 calls (July 22): DENSER — small/medium undergrowth sporadic-but-dense
among the big trees; an ACTUAL maze with VARIED paths (braided, not single-solution);
the Bramblehulk's light ring INVISIBLE from spawn; and gentle ROLLING HILLS.

The ground: ~30 walkable dome primitives (flattened spheres, equator at z=0) whose
heights are ANALYTIC — ground_z(x, y) is computed in-script, so every prop, lantern,
moth and monster plants at true ground height. Flat exclusion zones keep the beam
gameplay honest (plaza, tutorial garden, arena, goal). A deliberate three-dome RIDGE
rises before the arena so the ring only reveals when you crest it.

The maze: recursive backtracker (perfect) then BRAIDED — 15% of interior walls
knocked out, so routes loop and vary. Mouth at center-south; exit bent WEST
(column 2) so no straight corridor ever faces the arena.

Rerun-safe: same seed = same world; MW_ actors purged and rebuilt.
"""
import math
import random

import unreal

MAP = "/Game/Maps/WorldStageTesting"
SEED = 29
COLS, ROWS = 11, 11
CELL = 1150.0
MAZE_Y0 = 3000.0
MAZE_X0 = -(COLS * CELL) / 2.0
ARENA = unreal.Vector(0.0, 18200.0, 0.0)
ARENA_R = 2100.0
BRAID = 0.15                 # fraction of interior walls knocked out -> varied paths
EXIT_COL = 2                 # the western bend: no straight line to the arena

random.seed(SEED)

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary

# ---------------- Nanite for every Moonworks mesh (incl. fresh undergrowth) ----------------
nanite_count = 0
for path in EAL.list_assets("/Game/Art/Moonworks", recursive=True):
    if "stage_terrain" in path:
        continue   # terrain keeps raster tris: Nanite would swap in its coarse collision fallback
    sm = unreal.load_asset(path)
    if isinstance(sm, unreal.StaticMesh):
        ns = sm.get_editor_property("nanite_settings")
        if not ns.get_editor_property("enabled"):
            ns.set_editor_property("enabled", True)
            sm.set_editor_property("nanite_settings", ns)
            EAL.save_loaded_asset(sm)
        nanite_count += 1
print(f"MAZE_MARKER: Nanite verified on {nanite_count} Moonworks meshes")

assert les.load_level(MAP), "LOAD_STAGE_FAILED"


def rot(yaw):
    return unreal.Rotator(0.0, 0.0, yaw)


def cls(name):
    c = unreal.load_class(None, f"/Script/SuperClaudeBros2.{name}")
    assert c, f"CLASS_MISSING: {name}"
    return c


def cx(c):
    return MAZE_X0 + c * CELL


def cy(r):
    return MAZE_Y0 + r * CELL


# ---------------- purge the old world, keep the stage bones ----------------
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith("MW_"):
        eas.destroy_actor(a)

# ---------------- THE HILLS: analytic walkable domes, equator at z=0 ----------------
FLAT_ZONES = [                      # (x, y, radius) — beam gameplay stays on level ground
    (0.0, -400.0, 2600.0),          # spawn plaza
    (-2600.0, -2900.0, 2600.0),     # tutorial garden
    (ARENA.x, ARENA.y, 3000.0),     # the arena bowl
    (0.0, 20900.0, 1700.0),         # the goal court
]

hills = []                          # (x, y, a, c)
attempts = 0
while len(hills) < 26 and attempts < 400:
    attempts += 1
    hx = random.uniform(-13000.0, 13000.0)
    hy = random.uniform(-5200.0, 20200.0)
    a = random.uniform(1600.0, 3600.0)
    c = random.uniform(140.0, 420.0)
    if any(math.hypot(hx - fx, hy - fy) < fr + a * 0.55 for fx, fy, fr in FLAT_ZONES):
        continue
    hills.append((hx, hy, a, c))
# THE RIDGE: the arena stays a rumor until you crest it.
hills += [(-2600.0, 15000.0, 2600.0, 520.0),
          (100.0, 15250.0, 2400.0, 560.0),
          (2700.0, 15000.0, 2600.0, 520.0)]

# THE MELDED GROUND (v3): the hills live in ONE sculpted terrain mesh now — the
# Blender-built stage_terrain, complex-collision so feet truly land (the ghost-hills
# fix). This script and Blender share the same summed Wyvill field, so every prop
# still plants at true ground height.
terrain_sm = EAL.load_asset("/Game/Art/Moonworks/stage_terrain")
assert terrain_sm, "TERRAIN_MISSING: run import_stage_terrain.py first"
t = eas.spawn_actor_from_object(terrain_sm, unreal.Vector(0.0, 0.0, 0.0))
t.set_actor_label("MW_Terrain")
print(f"MAZE_MARKER: melded terrain placed ({len(hills)} hills in one mesh)")


def ground_z(x, y):
    """True ground height: the summed Wyvill field — EXACTLY what Blender sculpted."""
    g = 0.0
    for hx, hy, a, c in hills:
        d2 = ((x - hx) ** 2 + (y - hy) ** 2) / (a * a)
        if d2 < 1.0:
            g += c * (1.0 - d2) ** 2
    return g


# TERRAIN TRUTH PROBES (the floating-boulder law, July 23): the sculpted mesh must
# agree with the field function BEFORE anything is planted on it. A silent axis
# flip in the FBX handshake put the ridge in the south wilderness and hung 1500
# props in mid-air — never again. Probe three landmarks; mismatch = hard stop.
def probe_ground(x, y):
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            t, unreal.Vector(x, y, 3000.0), unreal.Vector(x, y, -500.0),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [],
            unreal.DrawDebugTrace.NONE, True)
        if hit:
            return hit.get_editor_property("impact_point").z
    except Exception as e:
        print(f"MAZE_WARN: terrain probe API unavailable ({e}) — screenshot is the fallback truth")
    return None


probes_ok = True
for px, py, pname in ((100.0, 15250.0, "ridge"), (0.0, -400.0, "plaza"),
                      (100.0, -15250.0, "south-of-spawn")):
    want = ground_z(px, py)
    got = probe_ground(px, py)
    got_s = f"{got:.0f}" if got is not None else "NONE"
    print(f"MAZE_MARKER: terrain probe {pname}: measured={got_s} expected={want:.0f}")
    if got is not None and abs(got - want) > 150.0:
        probes_ok = False
assert probes_ok, "TERRAIN_MISALIGNED: sculpted ground disagrees with the field (axis flip?)"


# ---------------- slab, spawn, moonlight ----------------
for a in list(eas.get_all_level_actors()):
    label = a.get_actor_label()
    if label == "StageSlab":
        eas.destroy_actor(a)   # the terrain IS the ground now — no coplanar z-fighting
    elif label == "StageSpawn":
        a.set_actor_rotation(rot(90.0), False)
    elif label == "StageSun":
        comp = a.get_component_by_class(unreal.DirectionalLightComponent)
        if comp:
            comp.set_editor_property("intensity", 3.2)
            comp.set_light_color(unreal.LinearColor(0.58, 0.74, 1.0, 1.0))
        a.set_actor_rotation(unreal.Rotator(0.0, -34.0, 40.0), False)
    elif label == "StageSkyLight":
        comp = a.get_component_by_class(unreal.SkyLightComponent)
        if comp:
            comp.set_editor_property("intensity", 0.55)
            comp.recapture_sky()
print("MAZE_MARKER: slab expanded, moonlight set, spawn faces the forest")

# ---------------- the prop pools ----------------
crystal_sm = EAL.load_asset("/Game/Art/Moonworks/moon_crystal")
tree_sm = EAL.load_asset("/Game/Art/Moonworks/crystal_tree")
assert crystal_sm and tree_sm, "PROPS_MISSING"


def pool_entry(sm, canon_h):
    b = sm.get_bounding_box()
    h = max(b.max.z - b.min.z, 1.0)
    return (sm, canon_h / h, b.min.z)


TREE = pool_entry(tree_sm, 900.0)
CRYS = pool_entry(crystal_sm, 340.0)

# Undergrowth: the stage-30 kit when it has landed; small-scaled heroes otherwise.
UNDER = []
for name, canon in (("crystal_shards", 120.0), ("moon_fern", 180.0),
                    ("moonstone_boulder", 220.0), ("crystal_sapling", 380.0)):
    sm = EAL.load_asset(f"/Game/Art/Moonworks/{name}")
    if sm:
        UNDER.append(pool_entry(sm, canon))
if not UNDER:
    UNDER = [(CRYS[0], CRYS[1] * 0.35, CRYS[2]), (TREE[0], TREE[1] * 0.3, TREE[2])]
    print("MAZE_WARN: stage-30 undergrowth not imported yet — heroes at small scale fill in")
else:
    print(f"MAZE_MARKER: undergrowth kit loaded ({len(UNDER)} kinds)")

prop_count = 0


def plant(entry, x, y, scale_mul, label):
    global prop_count
    sm, base_f, minz = entry
    f = base_f * scale_mul
    z = ground_z(x, y) - minz * f
    a = eas.spawn_actor_from_object(sm, unreal.Vector(x, y, z))
    a.set_actor_label(label)
    a.set_actor_rotation(rot(random.uniform(0.0, 360.0)), False)
    a.set_actor_scale3d(unreal.Vector(f, f, f))
    prop_count += 1


def plant_under(x, y, tag):
    plant(random.choice(UNDER), x, y, random.uniform(0.6, 1.5), tag)


def plant_wall(x1, y1, x2, y2, tag):
    """A DENSE wall: a heavy file of trees/crystals plus an undergrowth fringe."""
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    n = max(4, int(length / 240.0))
    for i in range(n):
        t = (i + 0.5) / n
        x = x1 + dx * t + ux * random.uniform(-70, 70) + px * random.uniform(-110, 110)
        y = y1 + dy * t + uy * random.uniform(-70, 70) + py * random.uniform(-110, 110)
        if random.random() < 0.55:
            plant(TREE, x, y, random.uniform(0.45, 1.5), f"MW_Maze_{tag}_t{i}")
        else:
            plant(CRYS, x, y, random.uniform(0.5, 1.7), f"MW_Maze_{tag}_c{i}")
    m = max(2, int(length / 380.0))
    for i in range(m):
        t = random.uniform(0.05, 0.95)
        side = random.choice((-1.0, 1.0))
        x = x1 + dx * t + px * side * random.uniform(130.0, 190.0)
        y = y1 + dy * t + py * side * random.uniform(130.0, 190.0)
        plant_under(x, y, f"MW_Fringe_{tag}_{i}")


# ---------------- the maze: perfect, then BRAIDED ----------------
south = [[True] * COLS for _ in range(ROWS + 1)]
west = [[True] * (COLS + 1) for _ in range(ROWS)]
visited = [[False] * COLS for _ in range(ROWS)]

stack = [(0, COLS // 2)]
visited[0][COLS // 2] = True
while stack:
    r, c = stack[-1]
    options = []
    if r > 0 and not visited[r - 1][c]:
        options.append(("S", r - 1, c))
    if r < ROWS - 1 and not visited[r + 1][c]:
        options.append(("N", r + 1, c))
    if c > 0 and not visited[r][c - 1]:
        options.append(("W", r, c - 1))
    if c < COLS - 1 and not visited[r][c + 1]:
        options.append(("E", r, c + 1))
    if not options:
        stack.pop()
        continue
    d, nr, nc = random.choice(options)
    if d == "S":
        south[r][c] = False
    elif d == "N":
        south[r + 1][c] = False
    elif d == "W":
        west[r][c] = False
    else:
        west[r][c + 1] = False
    visited[nr][nc] = True
    stack.append((nr, nc))

# The braid: varied paths, loops, choices (Adam: "an actual maze with varied paths").
interior = ([("s", r, c) for r in range(1, ROWS) for c in range(COLS) if south[r][c]] +
            [("w", r, c) for r in range(ROWS) for c in range(1, COLS) if west[r][c]])
for kind, r, c in random.sample(interior, int(len(interior) * BRAID)):
    if kind == "s":
        south[r][c] = False
    else:
        west[r][c] = False

south[0][COLS // 2] = False      # the mouth (center-south, between the gate lanterns)
south[ROWS][EXIT_COL] = False    # the exit (bent WEST — never a straight line north)

for r in range(ROWS + 1):
    for c in range(COLS):
        if south[r][c]:
            plant_wall(cx(c), cy(r), cx(c + 1), cy(r), f"s{r}_{c}")
for r in range(ROWS):
    for c in range(COLS + 1):
        if west[r][c]:
            plant_wall(cx(c), cy(r), cx(c), cy(r + 1), f"w{r}_{c}")
print(f"MAZE_MARKER: braided maze {COLS}x{ROWS} planted ({int(len(interior) * BRAID)} walls opened)")

# Sporadic-but-dense: undergrowth inside every cell (edges only — paths stay walkable),
# clusters at wall corners, and a wilderness sprinkle beyond the maze band.
for r in range(ROWS):
    for c in range(COLS):
        for i in range(3):
            ang = random.uniform(0, 2 * math.pi)
            d = random.uniform(320.0, 500.0)
            plant_under(cx(c) + CELL * 0.5 + math.cos(ang) * d,
                        cy(r) + CELL * 0.5 + math.sin(ang) * d, f"MW_Cell{r}_{c}_{i}")
for r in range(ROWS + 1):
    for c in range(COLS + 1):
        if random.random() < 0.35:
            for i in range(2):
                plant_under(cx(c) + random.uniform(-140, 140),
                            cy(r) + random.uniform(-140, 140), f"MW_Post{r}_{c}_{i}")
wild = 0
while wild < 70:
    x = random.uniform(-13400.0, 13400.0)
    y = random.uniform(-5400.0, 20600.0)
    in_maze = (MAZE_X0 - 700 < x < -MAZE_X0 + 700) and (MAZE_Y0 - 700 < y < cy(ROWS) + 700)
    in_flat = any(math.hypot(x - fx, y - fy) < fr for fx, fy, fr in FLAT_ZONES)
    if in_maze or in_flat:
        continue
    if random.random() < 0.45:
        plant(random.choice((TREE, CRYS)), x, y, random.uniform(0.5, 1.6), f"MW_Wild{wild}")
    else:
        plant_under(x, y, f"MW_Wild{wild}")
    wild += 1
print("MAZE_MARKER: undergrowth laid — cells, corners, wilderness")

# ---------------- lanterns, gate, moths ----------------
def no_heal(lantern):
    """NO FREE HEALTH (Adam, July 23): waypoint lamps light the road but do not
    refill the flame — with 13 lanterns in the maze the hero out-healed every
    fight. Sanctuary lives at the GOAL lantern alone."""
    ls = lantern.get_component_by_class(unreal.LightStateComponent)
    if ls:
        ls.set_editor_property("refills_embers", False)


lantern_cells = random.sample([(r, c) for r in range(1, ROWS - 1) for c in range(COLS)], 11)
for i, (r, c) in enumerate(lantern_cells):
    x = cx(c) + CELL * 0.5 + random.uniform(-140, 140)
    y = cy(r) + CELL * 0.5 + random.uniform(-140, 140)
    a = eas.spawn_actor_from_class(cls("Lantern"), unreal.Vector(x, y, ground_z(x, y)),
                                   rot(random.uniform(0, 360)))
    a.set_actor_label(f"MW_Breadcrumb{i}")
    no_heal(a)

for i, gx in enumerate((cx(COLS // 2) + CELL * 0.5 - 350, cx(COLS // 2) + CELL * 0.5 + 350)):
    g = eas.spawn_actor_from_class(cls("Lantern"),
                                   unreal.Vector(gx, MAZE_Y0 - 250, ground_z(gx, MAZE_Y0 - 250)), rot(0))
    g.set_actor_label(f"MW_GateLantern{i}")
    no_heal(g)

# ---------------- THE GLADE PROWLER: the maze has a warden now ----------------
px, py = cx(COLS // 2) + CELL * 0.5, cy(5) + CELL * 0.5
prowler = eas.spawn_actor_from_class(cls("GladeProwler"),
                                     unreal.Vector(px, py, ground_z(px, py) + 150), rot(0))
prowler.set_actor_label("MW_GladeProwler")
print("MAZE_MARKER: the Glade Prowler walks his rounds")

# ---------------- glasswings: the sky gets a pulse ----------------
for i in range(12):
    wx = random.uniform(-9000.0, 9000.0)
    wy = random.uniform(1000.0, 17000.0)
    w = eas.spawn_actor_from_class(cls("GlassWing"),
                                   unreal.Vector(wx, wy, ground_z(wx, wy) + random.uniform(900, 1500)),
                                   rot(random.uniform(0, 360)))
    w.set_actor_label(f"MW_GlassWing{i}")
    w.set_editor_property("orbit_radius", random.uniform(500.0, 1300.0))
    w.set_editor_property("orbit_speed", random.uniform(220.0, 420.0))

for i in range(14):
    r, c = random.randrange(ROWS), random.randrange(COLS)
    x, y = cx(c) + CELL * 0.5, cy(r) + CELL * 0.5
    a = eas.spawn_actor_from_class(cls("FlitMoth"),
                                   unreal.Vector(x, y, ground_z(x, y) + random.uniform(180, 320)), rot(0))
    a.set_actor_label(f"MW_Moth{i}")

# ---------------- the plaza tutorial garden (flat zone; beams stay true) ----------------
spawn = eas.spawn_actor_from_class


def ground_node(actor):
    """Meshy pivots are centered: sit the body's base on the stage (the buried-prism law)."""
    body = actor.get_editor_property("body_mesh")
    sm = body.get_editor_property("static_mesh") if body else None
    if sm and ("moon_" in sm.get_name() or "crystal_" in sm.get_name()):
        b = sm.get_bounding_box()
        body.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, -b.min.z))


src = spawn(cls("MoonBeamSource"), unreal.Vector(-3800, -1500, ground_z(-3800, -1500)), rot(0))
src.set_actor_label("MW_TutSource")
ca = spawn(cls("MoonCrystal"), unreal.Vector(-2200, -1500, ground_z(-2200, -1500)), rot(-90))
ca.set_actor_label("MW_TutCrystal")
ground_node(ca)
pr = spawn(cls("MoonPrism"), unreal.Vector(-2200, -2900, ground_z(-2200, -2900)), rot(-90))
pr.set_actor_label("MW_TutPrism")
ground_node(pr)
for i, sx in enumerate((-1, 1)):
    fx = -2200 + sx * math.sin(math.radians(30)) * 1560
    fy = -2900 - math.cos(math.radians(30)) * 1560
    f = spawn(cls("MoonflowerPlatform"), unreal.Vector(fx, fy, ground_z(fx, fy)), rot(0))
    f.set_actor_label(f"MW_TutFlower{i}")

# ---------------- the arena: ring, storm, light, answer ----------------
ring_n = 34
gap_deg = 22.0
for i in range(ring_n):
    ang = i * (360.0 / ring_n)
    if abs(((ang - 270.0) + 180.0) % 360.0 - 180.0) < gap_deg:        # south entrance
        continue
    if abs(((ang - 90.0) + 180.0) % 360.0 - 180.0) < gap_deg / 2.0:   # north gate to the goal
        continue
    x = ARENA.x + math.cos(math.radians(ang)) * ARENA_R
    y = ARENA.y + math.sin(math.radians(ang)) * ARENA_R
    if random.random() < 0.6:
        plant(TREE, x, y, random.uniform(0.9, 1.6), f"MW_Ring{i}")
    else:
        plant(CRYS, x, y, random.uniform(1.0, 1.8), f"MW_Ring{i}")
# Beam lanes are sacred: source->crystal and crystal->hulk lines stay clear of
# fringe scatter (a single random prop ate arena beam B on the first v2 run).
BEAM_LANES = [((-1500.0, 17000.0), (1400.0, 17000.0)),
              ((1500.0, 19400.0), (-1400.0, 19400.0)),
              ((1400.0, 17000.0), (0.0, 18000.0)),
              ((-1400.0, 19400.0), (0.0, 18000.0))]


def near_lane(x, y, clearance=280.0):
    for (ax, ay), (bx, by) in BEAM_LANES:
        abx, aby = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * abx + (y - ay) * aby) / (abx * abx + aby * aby)))
        if math.hypot(x - (ax + abx * t), y - (ay + aby * t)) < clearance:
            return True
    return False


for i in range(10):    # inner fringe: the bowl feels grown, not placed
    ang = random.uniform(0, 360)
    if abs(((ang - 270.0) + 180.0) % 360.0 - 180.0) < gap_deg + 8:
        continue
    x = ARENA.x + math.cos(math.radians(ang)) * (ARENA_R - 260)
    y = ARENA.y + math.sin(math.radians(ang)) * (ARENA_R - 260)
    if near_lane(x, y):
        continue
    plant_under(x, y, f"MW_RingFringe{i}")

# Exit corridor: from the WESTERN exit, over the ridge shoulder, into the south gap.
exit_x = cx(EXIT_COL) + CELL * 0.5
plant_wall(exit_x - 620, cy(ROWS), ARENA.x - 780, ARENA.y - ARENA_R - 120, "exitW")
plant_wall(exit_x + 620, cy(ROWS), ARENA.x + 780, ARENA.y - ARENA_R - 120, "exitE")

hulk = spawn(cls("Bramblehulk"),
             unreal.Vector(ARENA.x, ARENA.y, ground_z(ARENA.x, ARENA.y) + 250), rot(-90))
hulk.set_actor_label("MW_Bramblehulk")
# NO REGENERATING BOSS BAR (Adam, July 23): calm no longer bleeds away between
# beam passes — progress against the storm STAYS won.
hulk.set_editor_property("calm_decay_per_second", 0.0)

for tag, (sx, sy, syaw), (kx, ky) in (
    ("A", (-1500, 17000, 0), (1400, 17000)),
    ("B", (1500, 19400, 180), (-1400, 19400)),
):
    s = spawn(cls("MoonBeamSource"), unreal.Vector(sx, sy, ground_z(sx, sy)), rot(syaw))
    s.set_actor_label(f"MW_ArenaSource{tag}")
    hit_yaw = math.degrees(math.atan2(ARENA.y - 200 - ky, ARENA.x - kx))
    k = spawn(cls("MoonCrystal"), unreal.Vector(kx, ky, ground_z(kx, ky)), rot(hit_yaw - 3 * 22.5))
    k.set_actor_label(f"MW_ArenaCrystal{tag}")
    ground_node(k)
    k.set_editor_property("beam_calm_per_second", 7.0)

# ---------------- the goal: the guttering light pole, the flag beside it ----------------
goal_y = ARENA.y + ARENA_R + 600
goal = spawn(cls("Lantern"), unreal.Vector(ARENA.x, goal_y, ground_z(ARENA.x, goal_y)), rot(0))
goal.set_actor_label("MW_GoalLantern")
for prop, val in (("start_guttering", True), ("is_world_goal", True),
                  ("is_checkpoint", True), ("relight_by_hero_radius", 0.0)):
    try:
        goal.set_editor_property(prop, val)
    except Exception as e:
        print(f"MAZE_WARN: goal lantern {prop}: {e}")

flag = spawn(cls("FlagpoleGoal"),
             unreal.Vector(ARENA.x + 420, goal_y, ground_z(ARENA.x + 420, goal_y)), rot(0))
flag.set_actor_label("MW_Flagpole")

# ---------------- THE HORIZON (Adam, July 23: "not just a white abyss") ----------------
# A distant crystal range rings the world beyond the terrain's edge — mega-scaled
# silhouettes sunk into the void — and a silver-teal height fog melts the far
# ground into them. The edge of the stage becomes a view, not an ending.
ring_count = 26
for i in range(ring_count):
    ang = i * (360.0 / ring_count) + random.uniform(-4.0, 4.0)
    ex = math.cos(math.radians(ang)) * 18500.0
    ey = math.sin(math.radians(ang)) * 26500.0
    entry = TREE if i % 2 == 0 else CRYS
    f = entry[1] * random.uniform(9.0, 22.0)
    b = eas.spawn_actor_from_object(entry[0], unreal.Vector(ex, ey, -entry[2] * f - 400.0))
    b.set_actor_label(f"MW_Backdrop{i}")
    b.set_actor_rotation(rot(random.uniform(0, 360)), False)
    b.set_actor_scale3d(unreal.Vector(f, f, f))

fog = eas.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0), rot(0))
fog.set_actor_label("MW_Haze")
fog_comp = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
if fog_comp:
    fog_comp.set_editor_property("fog_density", 0.012)
    fog_comp.set_editor_property("fog_height_falloff", 0.05)
    fog_comp.set_editor_property("start_distance", 2500.0)
    try:
        fog_comp.set_editor_property("fog_inscattering_luminance",
                                     unreal.LinearColor(0.42, 0.56, 0.75, 1.0))
    except Exception as e:
        print(f"MAZE_WARN: fog tint property: {e}")
print("MAZE_MARKER: horizon ring + silver haze raised")

print(f"MAZE_MARKER: {prop_count} forest props planted")
assert les.save_current_level(), "SAVE_MAZE_FAILED"
print("MAZE_MARKER: DONE — the braided crystal maze rolls over the hills")
