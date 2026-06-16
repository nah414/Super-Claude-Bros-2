"""WORLD 1 — alternative layout: THE LANTERN CLIMB (Emberwell Canyon) -> /Game/Maps/LanternClimb

A VERTICAL warm-cyberpunk canyon: you climb a switchback up the west cliff, cross a gondola
bridge, then spiral a central spire to relight the FIRST LANTERN at the crown (the world goal).
Distinct from the linear festival street: the journey is UP, not forward.

Design rules learned the hard way:
 * The critical path is WALKABLE RAMPS (gentle <=12 deg) + flat landings — guaranteed traversable
   with no blind-jump tuning. The hero can still jump for optional nooks.
 * A SOLID wet floor spans the whole canyon bottom — falling is a setback (respawn at last lit
   lantern), never a death pit (Adam's "set boundaries / no cliffs" rule).
 * Meshy props: grounded by bounding box, NO Nanite, no-collision decoratives,
   visible_in_ray_tracing=False. Props gracefully SKIP if the kit isn't imported yet, so the
   structure builds + tests before the assets land; re-run after import to dress it.
 * Tier 0 is a WADEABLE wet slot (cosmetic water over a solid floor) — no swim controller needed.
Re-runnable (scratch dance rebuilds the map each run).
"""
import math
import unreal
from collections import Counter

EAL = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

MAP = "/Game/Maps/LanternClimb"
KIT = "/Game/Art/LanternClimbKit"

# ---- scratch dance: rebuild the map fresh ----
if EAL.does_asset_exist("/Game/Maps/_Scratch"):
    EAL.delete_asset("/Game/Maps/_Scratch")
assert les.new_level("/Game/Maps/_Scratch"), "SCRATCH_FAILED"
if EAL.does_asset_exist(MAP):
    assert EAL.delete_asset(MAP), "DELETE_OLD_FAILED"
assert les.new_level(MAP), "NEW_MAP_FAILED"

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
PLANE = unreal.load_asset("/Engine/BasicShapes/Plane")


def mat(name):
    return EAL.load_asset(f"/Game/Art/CityMat/{name}")


M_ASPHALT = mat("M_WetAsphalt")
M_SIDEWALK = mat("M_Sidewalk")
M_BUILD = mat("M_Windows_b") or M_SIDEWALK
M_BUILD2 = mat("M_Windows_a") or M_SIDEWALK
M_WATER = mat("M_HoloBillboard") or M_ASPHALT     # stand-in translucent-ish sheen
M_EMISSIVE = EAL.load_asset("/Game/Art/M_VertexLitEmissive")

LANTERN_CLASS = unreal.load_class(None, "/Script/SuperClaudeBros2.Lantern")
NETMGR_CLASS = unreal.load_class(None, "/Script/SuperClaudeBros2.LightNetworkManager")
P = Counter()


def setp(actor, names, value):
    for nm in names:
        try:
            actor.set_editor_property(nm, value)
            return True
        except Exception:
            continue
    return False


def block(x, y, z, sx, sy, sz, label, material=M_BUILD, solid=True, rt=False, hidden=False):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z))
    a.static_mesh_component.set_static_mesh(CUBE)
    a.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0))
    if material:
        a.static_mesh_component.set_material(0, material)
    if not rt:
        a.static_mesh_component.set_editor_property("visible_in_ray_tracing", False)
    if hidden:
        a.set_actor_hidden_in_game(True)
    if not solid:
        a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    a.set_actor_label(f"LC_{label}")
    P[label.split('_')[0]] += 1
    return a


def ramp(p0, p1, width, label, material=M_SIDEWALK):
    """A walkable tilted slab from p0 (low) to p1 (high). p0/p1 are WALKING-SURFACE points;
    the 36uu-thick slab is centred so its top ~ the waypoint line."""
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    R = math.hypot(dx, dy)
    L = math.hypot(R, dz)
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, R))     # +pitch tilts local +X (=toward p1) UP
    mid = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2 - 18.0)
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*mid))
    a.static_mesh_component.set_static_mesh(CUBE)
    a.set_actor_rotation(unreal.Rotator(0.0, pitch, yaw), False)  # (roll, pitch, yaw)
    a.set_actor_scale3d(unreal.Vector(L / 100.0, width / 100.0, 0.36))
    if material:
        a.static_mesh_component.set_material(0, material)
    a.static_mesh_component.set_editor_property("visible_in_ray_tracing", False)
    a.set_actor_label(f"LC_{label}")
    P["ramp"] += 1
    return a


def landing(cx, cy, ztop, w, d, label, material=M_SIDEWALK):
    """Flat platform whose TOP surface sits at ztop."""
    return block(cx, cy, ztop - 20.0, w, d, 40.0, label, material=material, rt=False)


def lantern(x, y, label, *, z, checkpoint=False, goal=False, dark=False,
            relight_radius=320.0, auto=9.0, scale=1.0, intensity=1100.0, radius=620.0):
    a = eas.spawn_actor_from_class(LANTERN_CLASS, unreal.Vector(x, y, z))
    setp(a, ["lit_intensity", "LitIntensity"], intensity)
    setp(a, ["lit_radius", "LitRadius"], radius)
    setp(a, ["relight_by_hero_radius", "RelightByHeroRadius"], relight_radius)
    setp(a, ["auto_relight_seconds", "AutoRelightSeconds"], auto)
    setp(a, ["is_checkpoint", "b_is_checkpoint", "bIsCheckpoint"], checkpoint)
    setp(a, ["is_world_goal", "b_is_world_goal", "bIsWorldGoal"], goal)
    setp(a, ["start_dark", "b_start_dark", "bStartDark"], dark)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    a.set_actor_label(f"LC_Lantern_{label}")
    P["lantern"] += 1
    return a


def fprop(name, x, y, scale, yaw=0.0, z=None, solid=False):
    """Meshy LanternClimbKit prop; grounds on its bbox base unless z given. Skips (logs)
    if the kit isn't imported yet so the structure builds without it."""
    sm = EAL.load_asset(f"{KIT}/{name}/SM_{name}")
    if not sm:
        unreal.log_warning(f"KIT_MISSING {name} (skipped)")
        return None
    bb = sm.get_bounding_box()
    zz = (0.0 - bb.min.z * scale) if z is None else z
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, zz))
    a.static_mesh_component.set_static_mesh(sm)
    a.set_actor_rotation(unreal.Rotator(0.0, 0.0, yaw), False)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    a.static_mesh_component.set_editor_property("visible_in_ray_tracing", False)
    if not solid:
        a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    a.set_actor_label(f"LC_Prop_{name}_{P['prop']}")
    P["prop"] += 1
    return a


def shell(cx, cy, ztop, w, d, h, label, door_yaw=0.0):
    """Enterable room: floor (top at ztop) + roof + 3 walls + a front wall with a door gap
    (facing door_yaw: 0=+X,90=+Y,180=-X,270=-Y), + interior lantern & crates."""
    T = 40.0
    block(cx, cy, ztop + h / 2, w, d, 30.0, f"{label}_roof")
    block(cx, cy, ztop - 20, w, d, 40.0, f"{label}_floor", material=M_SIDEWALK)
    sides = {0: ("fx", cx + w / 2, cy, T, d), 180: ("bx", cx - w / 2, cy, T, d),
             90: ("fy", cx, cy + d / 2, w, T), 270: ("by", cx, cy - d / 2, w, T)}
    dw, dh = 360.0, 520.0
    for ang, (tag, wx, wy, sx, sy) in sides.items():
        if ang == door_yaw:                      # front wall with a door gap
            if sx > sy:                          # wall spans X -> split along X
                seg = (sx - dw) / 2
                block(wx - (dw / 2 + seg / 2), wy, ztop + h / 2, seg, sy, h, f"{label}_dL")
                block(wx + (dw / 2 + seg / 2), wy, ztop + h / 2, seg, sy, h, f"{label}_dR")
                block(wx, wy, ztop + dh + (h - dh) / 2, dw, sy, h - dh, f"{label}_dT")
            else:                                # wall spans Y -> split along Y
                seg = (sy - dw) / 2
                block(wx, wy - (dw / 2 + seg / 2), ztop + h / 2, sx, seg, h, f"{label}_dL")
                block(wx, wy + (dw / 2 + seg / 2), ztop + h / 2, sx, seg, h, f"{label}_dR")
                block(wx, wy, ztop + dh + (h - dh) / 2, sx, dw, h - dh, f"{label}_dT")
        else:
            block(wx, wy, ztop + h / 2, sx, sy, h, f"{label}_{tag}")
    lantern(cx, cy, f"in_{label}", z=ztop + 120, relight_radius=360.0, scale=0.9)
    fprop("cargo_crate_set", cx - w * 0.25, cy + d * 0.2, 1.0)
    P["shell"] += 1


# ============================================================ CANYON SHELL
# Canyon X in [-2500,2500], Y in [-2900,2900], climb Z 350 -> 8650.
FLOOR_TOP = 350.0
# Solid wet bottom floor across the whole canyon (no death pit).
block(0, 0, FLOOR_TOP - 150, 5200, 6000, 300, "Floor", material=M_ASPHALT)
# Cosmetic shallow water sheet just above it (no collision -> wade through).
block(0, 0, FLOOR_TOP + 6, 4600, 5400, 12, "Water", material=M_WATER, solid=False, rt=False)
# The two facing building cliffs (tall backdrops) + Y end caps -> a bounded canyon.
block(-2300, 0, 4600, 360, 6000, 9200, "CliffW", material=M_BUILD)
block(2300, 0, 4600, 360, 6000, 9200, "CliffE", material=M_BUILD2)
block(0, -2950, 4600, 5200, 360, 9200, "CapS", material=M_BUILD)
block(0, 2950, 4600, 5200, 360, 9200, "CapN", material=M_BUILD2)

# ============================================================ THE WALKABLE CLIMB
WX = -1350.0          # west-cliff switchback X
Y_LO, Y_HI = -2200.0, 2200.0
PATH_W = 560.0
z = FLOOR_TOP
wp = [(0.0, -2600.0, z), (WX, Y_LO, z)]   # spawn slot -> base of the switchback
RAMPS = 10
ZTOP_SWITCH = 6000.0
dz = (ZTOP_SWITCH - z) / RAMPS
ydir = 1
y = Y_LO
checkpts = []
for i in range(RAMPS):
    yn = Y_HI if ydir > 0 else Y_LO
    zn = z + dz
    wp.append((WX, yn, zn))
    z = zn
    y = yn
    ydir = -ydir
# from the last switchback turn, run a short landing toward canyon centre at z=6000
wp.append((WX, 0.0, ZTOP_SWITCH))
# lay ramps + a landing at every waypoint
for i in range(len(wp) - 1):
    ramp(wp[i], wp[i + 1], PATH_W, f"Ramp_{i:02d}")
for i, (px, py, pz) in enumerate(wp):
    landing(px, py, pz, PATH_W + 140, PATH_W + 140, f"Land_{i:02d}")
    # a relightable checkpoint lantern at every other turn
    if 1 < i < len(wp) - 1 and i % 2 == 1:
        dark = (i % 4 == 1)
        lantern(px + (120 if px < 0 else -120), py, f"cp_{i:02d}", z=pz + 60,
                checkpoint=True, dark=dark, relight_radius=0.0 if dark else 320.0,
                auto=0.0 if dark else 9.0, intensity=1400.0, radius=640.0)

# ============================================================ THE GONDOLA CROSSING
# From the switchback top (WX,0,6000) to the spire base (0,0,6000): a flat bridge.
SPIRE_BASE_Z = 6000.0
ramp((WX, 0.0, ZTOP_SWITCH), (-650.0, 0.0, SPIRE_BASE_Z), PATH_W, "GondApproach")
block(-325.0, 0.0, SPIRE_BASE_Z - 20, 760, 460, 40, "GondDeck", material=M_SIDEWALK)
fprop("cable_car_gondola", -325.0, 0.0, 2.4, yaw=90.0, z=SPIRE_BASE_Z - 10, solid=False)

# ============================================================ THE SPIRE + CROWN GOAL
# Central spire core column + a 4-segment spiral stair up to the First Lantern at the crown.
CROWN_Z = 8650.0
block(0, 0, (SPIRE_BASE_Z + CROWN_Z) / 2, 460, 460, CROWN_Z - SPIRE_BASE_Z, "SpireCore", material=M_BUILD)
SR = 760.0
SEGS = 6                                          # 6 gentle 90deg ramps (~21deg) wind up the spire
spire_wp = [(-650.0, 0.0, SPIRE_BASE_Z)]
for i in range(SEGS + 1):
    ang = math.radians(180 + 90 * i)             # start on -X side, wind around
    spire_wp.append((SR * math.cos(ang), SR * math.sin(ang),
                     SPIRE_BASE_Z + (CROWN_Z - 130 - SPIRE_BASE_Z) * i / SEGS))
spire_wp.append((0.0, 0.0, CROWN_Z - 90))        # final catwalk to the crown platform under the goal
for i in range(len(spire_wp) - 1):
    ramp(spire_wp[i], spire_wp[i + 1], 440, f"Spiral_{i:02d}")
for i, (px, py, pz) in enumerate(spire_wp):
    landing(px, py, pz, 500, 500, f"SpiralLand_{i:02d}")

# the FIRST LANTERN spire dressing + the crown goal lantern (relight = win)
fprop("first_lantern_spire", 0.0, 0.0, 14.0, z=SPIRE_BASE_Z, solid=False)
fprop("waygate_arch", 0.0, 560.0, 4.0, yaw=0.0, z=CROWN_Z - 120, solid=False)
lantern(0.0, 0.0, "FIRST", z=CROWN_Z, goal=True, dark=True, relight_radius=0.0, auto=0.0,
        scale=3.0, intensity=7000.0, radius=3000.0)

# ============================================================ 8 ENTERABLE SHELLS (per the spec)
shell(-1850, -1400, 900, 900, 760, 560, "S1_basement", door_yaw=0)
shell(-1850, -200, 950, 900, 760, 560, "S2_noodle", door_yaw=0)
shell(-1700, 1500, 2600, 900, 760, 560, "S3_workshop", door_yaw=90)
shell(-1100, 1500, 2600, 900, 760, 560, "S4_pawn", door_yaw=0)
shell(1700, 700, 4000, 900, 760, 560, "S5_arcade", door_yaw=180)
shell(1500, -700, 4800, 900, 760, 560, "S6_fixer", door_yaw=180)
shell(950, -1500, 5300, 900, 760, 560, "S7_bunk", door_yaw=270)
shell(700, 600, 5600, 820, 720, 540, "S8_pumproom", door_yaw=90)

# ============================================================ MESHY DRESSING (skip if not imported)
# Tier 0 wet base: the hover-car wreck + sunken shopfronts + a shrine.
fprop("hover_car_textured", 700, -1800, 2.2, yaw=28, z=FLOOR_TOP + 10)
fprop("sunken_shopfront", -700, -1500, 2.6, yaw=12, z=FLOOR_TOP - 30)
fprop("sunken_shopfront", 900, 900, 2.6, yaw=-100, z=FLOOR_TOP - 30)
fprop("wet_street_shrine", -1900, -2300, 1.5, yaw=40, z=FLOOR_TOP + 8)
fprop("food_cart_ramen", -1850, -800, 1.7, yaw=0, z=950)
fprop("food_cart_ramen", 1500, 200, 1.7, yaw=180, z=4400)
# Cliff dressing: fire-escapes, balconies, neon sign clusters along both faces.
for k, (cx, sgn) in enumerate(((-2050, 1), (2050, -1))):
    for j in range(5):
        zz = 900 + j * 1500
        fprop("fire_escape_module", cx, -1800 + j * 900, 2.0, yaw=90 * sgn, z=zz)
        fprop("tenement_balcony", cx, 1200 - j * 800, 2.2, yaw=90 * sgn, z=zz + 300)
        fprop("neon_sign_cluster", cx, -400 + j * 700, 1.8, yaw=90 * sgn, z=zz + 600)
# Overhead cables strung across the canyon for depth.
for zz in (2200, 4200, 6200):
    fprop("overhead_cables", 0, -600 + (zz % 900), 2.4, yaw=0, z=zz)
# Warm street-lantern posts beside the lower landings.
for (lx, ly, lz) in ((WX + 200, -1400, FLOOR_TOP), (WX + 200, 1400, 1700), (1600, 0, 4000)):
    fprop("street_lantern", lx, ly, 1.8, z=lz)

# ============================================================ AMBIENT WARM LANTERNS (lit pools)
for (lx, ly, lz) in ((WX, -1600, FLOOR_TOP + 60), (WX, 1600, 2200), (WX, -600, 3400),
                     (WX, 800, 4600), (0, 0, SPIRE_BASE_Z + 80), (700, -1400, 5360)):
    lantern(lx, ly, f"amb_{int(lz)}", z=lz)

# ============================================================ ATMOSPHERE + LIGHTING
fog = eas.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0))
fc = fog.component
fc.set_editor_property("enable_volumetric_fog", True)
fc.set_editor_property("fog_density", 0.018)
fc.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(0.012, 0.008, 0.018, 1.0))
fog.set_actor_label("LC_Fog")

eas.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0)).set_actor_label("LC_SkyAtm")
sky = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 4000))
sky.light_component.set_editor_property("real_time_capture", True)
sky.light_component.set_intensity(0.06)
sky.set_actor_label("LC_SkyLight")

# A low warm "moon over the canyon" key so the geometry reads (the lanterns carry the warmth).
moon = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 9000))
moon.set_actor_rotation(unreal.Rotator(0.0, -52.0, -35.0), False)  # (roll, pitch, yaw): aim down
moon.light_component.set_intensity(0.55)
moon.light_component.set_light_color(unreal.LinearColor(1.0, 0.82, 0.6, 1.0))
moon.set_actor_label("LC_Moon")

ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
ppv.set_editor_property("unbound", True)
pps = ppv.get_editor_property("settings")


def pp(name, value):
    try:
        pps.set_editor_property(f"override_{name}", True)
        pps.set_editor_property(name, value)
    except Exception as e:
        unreal.log_warning(f"pp skip {name}: {e}")


pp("bloom_method", unreal.BloomMethod.BM_FFT)
pp("bloom_intensity", 1.2)
pp("auto_exposure_min_brightness", -1.5)
pp("auto_exposure_max_brightness", -1.5)
pp("film_grain_intensity", 0.12)
pp("vignette_intensity", 0.4)
pp("color_gain_shadows", unreal.Vector4(1.02, 0.95, 1.16, 1.0))
pp("color_gain_highlights", unreal.Vector4(1.1, 1.02, 0.92, 1.0))
ppv.set_editor_property("settings", pps)
ppv.set_actor_label("LC_Post")

# ============================================================ SPAWN + SYSTEMS
start = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, -2600, FLOOR_TOP + 120))
start.set_actor_rotation(unreal.Rotator(0.0, 0.0, 90.0), False)   # (roll,pitch,yaw): face +Y up the canyon
start.set_actor_label("LC_PlayerStart")

mgr = eas.spawn_actor_from_class(NETMGR_CLASS, unreal.Vector(0, 0, SPIRE_BASE_Z))
mgr.set_actor_label("LC_LightNetworkManager")

saved = les.save_current_level()
if EAL.does_asset_exist("/Game/Maps/_Scratch"):
    EAL.delete_asset("/Game/Maps/_Scratch")
print(f"LANTERN_CLIMB_BUILT: {dict(P)} saved={saved} -> {MAP}")
